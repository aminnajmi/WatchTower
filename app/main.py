from datetime import datetime, timezone
import logging
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from sqlalchemy import func, select

from .auth import (
    SESSION_COOKIE_NAME,
    authenticate_token,
    create_access_token,
    verify_access_token,
    verify_password,
)
from .config import settings
from .models import init_db, SessionLocal, OSRelease, ReleaseHistory, ReleaseEvent
from .notifications.telegram import send_test as send_telegram_test
from .providers import PROVIDERS
from . import service
from . import scheduler as scheduler_module
from .service import check_all
from .scheduler import JOB_ID, SCHEDULE_LABEL, start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.validate_production_settings()
    init_db()
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


app = FastAPI(title="WatchTower", version="2.0.0", lifespan=lifespan)
logger = logging.getLogger(__name__)
# Compatibility seam for tests/integrations that inject a scheduler instance.
# Normal operation always reads the lifecycle-owned scheduler from its module.
scheduler = None
allowed_hosts = [host.strip() for host in settings.allowed_hosts.split(",") if host.strip()]
if allowed_hosts and "*" not in allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "templates"))
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "static")), name="static")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return response


class WebSessionRequest(BaseModel):
    access_token: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/auth/token", tags=["authentication"])
async def login(username: str = Form(...), password: str = Form(...)):
    if username != settings.admin_username or not verify_password(password):
        logger.warning("Authentication rejected stage=credentials status=401")
        raise HTTPException(status_code=401, detail="Invalid username or password")
    logger.info("Authentication accepted stage=credentials status=200")
    return {
        "access_token": create_access_token(username),
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@app.get("/", include_in_schema=False)
def home(request: Request):
    return RedirectResponse("/dashboard" if _web_user(request) else "/login", status_code=303)


def _web_user(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    return verify_access_token(token) if token else None


def _render_page(request: Request, template: str, active: str, **context):
    username = _web_user(request)
    if not username:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name=template,
        context={"active": active, "current_user": username, **context},
    )


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request):
    if _web_user(request):
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={})


@app.post("/web/session", include_in_schema=False)
def create_web_session(payload: WebSessionRequest, request: Request):
    username = verify_access_token(payload.access_token)
    if not username:
        logger.warning("Authentication rejected stage=browser_session status=401")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    response = JSONResponse({"ok": True})
    secure_cookie = request.url.scheme == "https"
    response.set_cookie(
        SESSION_COOKIE_NAME,
        payload.access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=secure_cookie,
        samesite="strict",
        path="/",
    )
    logger.info("Browser session created status=200 secure_cookie=%s", secure_cookie)
    return response


@app.post("/logout", include_in_schema=False)
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/", httponly=True, samesite="strict")
    return response


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard_page(request: Request):
    major_events = events(event_type="new_major_release", os=None)[:5]
    check_result = service.last_check_result or {}
    return _render_page(
        request,
        "dashboard.html",
        "dashboard",
        major_events=major_events,
        provider_errors=check_result.get("errors", []),
    )


@app.get("/os", response_class=HTMLResponse, include_in_schema=False)
def operating_systems_page(request: Request):
    return _render_page(request, "dashboard.html", "os", os_index=True)


@app.get("/os/{slug}", response_class=HTMLResponse, include_in_schema=False)
def os_detail_page(slug: str, request: Request):
    return _render_page(request, "os_detail.html", "os", slug=slug)


@app.get("/releases", response_class=HTMLResponse, include_in_schema=False)
def releases_page(request: Request):
    return _render_page(request, "releases.html", "releases")


@app.get("/events", response_class=HTMLResponse, include_in_schema=False)
def events_page(request: Request):
    return _render_page(request, "events.html", "events")


@app.get("/settings", response_class=HTMLResponse, include_in_schema=False)
def settings_page(request: Request):
    return _render_page(request, "settings.html", "settings")


def serialize_os(row: OSRelease):
    checked_at = _utc_timestamp(row.checked_at)
    return {
        "slug": row.slug,
        "name": row.name,
        "version": row.version,
        "major_version": row.major_version,
        "release_date": row.release_date,
        "source_url": row.source_url,
        "release_type": row.release_type,
        "is_rolling": row.is_rolling,
        "checked_at": checked_at,
        "last_checked": checked_at,
        "first_seen_at": row.first_seen_at,
        "updated_at": row.updated_at,
    }


def _utc_timestamp(value: datetime | None):
    if value is None:
        return None
    if value.tzinfo is None:
        # Existing SQLite DateTime columns store UTC without timezone metadata.
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@app.get("/api/v1/os", dependencies=[Depends(authenticate_token)])
def list_os():
    db = SessionLocal()
    try:
        rows = db.scalars(select(OSRelease).order_by(OSRelease.slug)).all()
        return [serialize_os(r) for r in rows]
    finally:
        db.close()


@app.get("/api/v1/os/{slug}", dependencies=[Depends(authenticate_token)])
def get_os(slug: str):
    db = SessionLocal()
    try:
        row = db.scalar(select(OSRelease).where(OSRelease.slug == slug))
        if not row:
            raise HTTPException(status_code=404, detail="OS not found")
        return serialize_os(row)
    finally:
        db.close()


@app.get("/api/v1/releases", dependencies=[Depends(authenticate_token)])
def releases(
    os: str | None = Query(default=None),
    release_type: str | None = Query(default=None, alias="type"),
    date: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    db = SessionLocal()
    try:
        stmt = select(ReleaseHistory, OSRelease).join(OSRelease, ReleaseHistory.os_id == OSRelease.id)
        count_stmt = select(func.count(ReleaseHistory.id)).join(OSRelease, ReleaseHistory.os_id == OSRelease.id)
        if os:
            stmt = stmt.where(OSRelease.slug == os)
            count_stmt = count_stmt.where(OSRelease.slug == os)
        if release_type:
            stmt = stmt.where(ReleaseHistory.release_type == release_type)
            count_stmt = count_stmt.where(ReleaseHistory.release_type == release_type)
        if date:
            stmt = stmt.where(ReleaseHistory.release_date == date)
            count_stmt = count_stmt.where(ReleaseHistory.release_date == date)
        total = db.scalar(count_stmt) or 0
        stmt = stmt.order_by(ReleaseHistory.detected_at.desc(), ReleaseHistory.id.desc())
        if limit is not None:
            stmt = stmt.offset(offset).limit(limit)
        rows = db.execute(stmt).all()
        items = [{
            "id": history.id,
            "os": os_row.slug,
            "name": os_row.name,
            "version": history.version,
            "major_version": history.major_version,
            "release_type": history.release_type,
            "release_date": history.release_date,
            "source_url": history.source_url,
            "detected_at": history.detected_at,
        } for history, os_row in rows]
        if limit is not None:
            return {"items": items, "total": total, "limit": limit, "offset": offset}
        return items
    finally:
        db.close()


@app.get("/api/v1/releases/{slug}", dependencies=[Depends(authenticate_token)])
def releases_for_os(slug: str):
    return releases(os=slug, release_type=None, date=None, limit=None, offset=0)


@app.get("/api/v1/events", dependencies=[Depends(authenticate_token)])
def events(
    event_type: str | None = Query(default=None),
    os: str | None = Query(default=None),
):
    db = SessionLocal()
    try:
        stmt = select(ReleaseEvent, OSRelease).join(OSRelease, ReleaseEvent.os_id == OSRelease.id)
        if event_type:
            stmt = stmt.where(ReleaseEvent.event_type == event_type)
        if os:
            stmt = stmt.where(OSRelease.slug == os)
        stmt = stmt.order_by(ReleaseEvent.detected_at.desc(), ReleaseEvent.id.desc())
        rows = db.execute(stmt).all()
        return [{
            "id": event.id,
            "os": os_row.slug,
            "name": os_row.name,
            "previous_version": event.previous_version,
            "new_version": event.new_version,
            "previous_major_version": event.previous_major_version,
            "new_major_version": event.new_major_version,
            "event_type": event.event_type,
            "detected_at": event.detected_at,
            "notification_sent": event.notification_sent,
            "notification_sent_at": event.notification_sent_at,
        } for event, os_row in rows]
    finally:
        db.close()


@app.post("/api/v1/check", dependencies=[Depends(authenticate_token)])
async def check():
    return await check_all()


@app.post("/api/v1/notifications/test/telegram", dependencies=[Depends(authenticate_token)])
async def test_telegram_notification():
    if not settings.telegram_enabled:
        return JSONResponse(
            {"success": False, "error": "Telegram notifications are disabled"},
            status_code=400,
        )

    try:
        result = await send_telegram_test()
    except Exception as exc:
        # Test delivery failures can include credential-bearing request URLs.
        logger.warning("Telegram test delivery failed (%s)", type(exc).__name__)
        return JSONResponse(
            {"success": False, "error": f"Telegram test failed ({type(exc).__name__})"},
            status_code=503,
        )
    if not result.success:
        return JSONResponse(
            {"success": False, "error": result.error or "Telegram test message failed"},
            status_code=503,
        )
    return {"success": True, "message": "Telegram test message sent"}


@app.get("/api/v1/providers", dependencies=[Depends(authenticate_token)])
def providers():
    return {"providers": list(PROVIDERS.keys())}


@app.get("/api/v1/status", dependencies=[Depends(authenticate_token)])
def status():
    db = SessionLocal()
    try:
        tracked = db.scalar(select(func.count(OSRelease.id))) or 0
        last_stored_check = db.scalar(select(func.max(OSRelease.checked_at)))
        major_count = db.scalar(select(func.count(ReleaseEvent.id)).where(
            ReleaseEvent.event_type == "new_major_release"
        )) or 0
    finally:
        db.close()

    finished = service.last_check_finished_at
    stored_last_check = _utc_timestamp(last_stored_check)
    latest_check = max(
        (timestamp for timestamp in (finished, stored_last_check) if timestamp is not None),
        default=None,
    )
    try:
        active_scheduler = scheduler or scheduler_module.get_scheduler()
        job = active_scheduler.get_job(JOB_ID) if active_scheduler is not None else None
        apscheduler_running = bool(active_scheduler is not None and active_scheduler.running)
        if not apscheduler_running:
            job_state = "stopped"
        elif job is None:
            job_state = "missing"
        elif active_scheduler.state == scheduler_module.STATE_PAUSED or job.next_run_time is None:
            job_state = "paused"
        else:
            job_state = "scheduled"
        scheduler_running = apscheduler_running and job_state == "scheduled"
        next_check = job.next_run_time if job_state == "scheduled" else None
    except Exception:
        job = None
        apscheduler_running = False
        scheduler_running = False
        job_state = "unavailable"
        next_check = None

    check_result = service.last_check_result
    errors = check_result["errors"] if check_result else None
    return {
        "tracked_os": len(PROVIDERS),
        "initialized_os": tracked,
        "checked": check_result["checked"] if check_result else None,
        "failed": check_result["failed"] if check_result else None,
        "provider_errors": len(errors) if errors is not None else None,
        "errors": errors,
        "results": check_result["results"] if check_result else None,
        "major_releases": major_count,
        "scheduler": {
            "running": scheduler_running,
            "apscheduler_running": apscheduler_running,
            "job_id": JOB_ID,
            "job_exists": job is not None,
            "job_state": job_state,
            "schedule": SCHEDULE_LABEL,
            "trigger": "cron" if isinstance(getattr(job, "trigger", None), scheduler_module.CronTrigger) else None,
            "timezone": "UTC",
            "last_check": latest_check,
            "next_check": next_check,
            "next_run": next_check,
            "last_execution": scheduler_module.last_scheduled_run_finished_at,
            "last_execution_status": scheduler_module.last_scheduled_run_status,
            "last_job_started_at": scheduler_module.last_scheduled_run_started_at,
            "last_job_finished_at": scheduler_module.last_scheduled_run_finished_at,
            "last_job_error": scheduler_module.last_scheduled_run_error,
            "check_in_progress": bool(
                service.last_check_started_at
                and (finished is None or service.last_check_started_at > finished)
            ),
        },
        "notifications": {
            "discord_enabled": bool(settings.discord_webhook_url),
            "telegram_enabled": bool(
                settings.telegram_enabled and settings.telegram_bot_token and settings.telegram_chat_id
            ),
            "telegram_chat_configured": bool(settings.telegram_chat_id),
        },
    }
