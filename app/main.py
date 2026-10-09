from datetime import datetime, timezone
import asyncio
import hashlib
import hmac
import logging
import json
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request, Header, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from typing import Literal
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, OperationalError

from .auth import (
    SESSION_COOKIE_NAME,
    authenticate_token,
    configure_session_factory_provider,
    create_access_token,
    hash_user_password,
    principal_for_username,
    Principal,
    require_admin,
    verify_access_token,
    verify_user_password,
    verify_password,
)
from .config import settings
from .models import init_db, SessionLocal, OSRelease, ReleaseHistory, ReleaseEvent, User, Notification, TidioConnection
from .schemas import UserCreate, UserUpdate, PasswordReset, PasswordChange, NotificationCreate
from .notifications.telegram import send_test as send_telegram_test
from .notifications.service import (
    ALLOWED_SEVERITIES, ALLOWED_SOURCES, ALLOWED_STATUSES,
    create_notification, metadata_for,
)
from .providers import PROVIDERS
from . import service
from . import scheduler as scheduler_module
from .service import check_all
from .scheduler import JOB_ID, SCHEDULE_LABEL, start_scheduler, stop_scheduler
from .tidio import monitor as tidio_monitor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
configure_session_factory_provider(lambda: SessionLocal)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.validate_production_settings()
    init_db()
    start_scheduler()
    tidio_restore_task = asyncio.create_task(tidio_monitor.restore())
    try:
        yield
    finally:
        tidio_restore_task.cancel()
        try:
            await tidio_restore_task
        except asyncio.CancelledError:
            pass
        await tidio_monitor.shutdown()
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
templates.env.globals["asset_version"] = hashlib.sha256(
    (PROJECT_ROOT / "static/js/app.js").read_bytes()
).hexdigest()[:12]
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "static")), name="static")


@app.exception_handler(RequestValidationError)
async def sanitized_validation_error(_request: Request, _exc: RequestValidationError):
    # Pydantic's default error payload includes the submitted input, which can
    # include a password. Return only field locations and generic messages.
    return JSONResponse({"detail": "Request validation failed"}, status_code=422)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as exc:
        # Do not log query strings: legacy GET login attempts may contain
        # credentials in them, and framework access logs include that string.
        logger.error(
            "http_request method=%s path=%s status=500 exception=%s",
            request.method,
            request.url.path,
            type(exc).__name__,
        )
        raise
    logger.info(
        "http_request method=%s path=%s status=%s",
        request.method,
        request.url.path,
        response.status_code,
    )
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return response


class WebSessionRequest(BaseModel):
    access_token: str


@app.get("/health")
def health():
    required_ui_assets = (
        PROJECT_ROOT / "static/css/app.css",
        PROJECT_ROOT / "static/js/app.js",
        PROJECT_ROOT / "static/watchtower.svg",
        PROJECT_ROOT / "templates/login.html",
    )
    if any(not asset.is_file() or asset.stat().st_size == 0 for asset in required_ui_assets):
        raise HTTPException(status_code=503, detail="WatchTower UI assets are unavailable")
    return {"status": "ok"}


@app.post("/api/v1/auth/token", tags=["authentication"])
async def login(username: str = Form(...), password: str = Form(...)):
    principal = _authenticate_login(username, password)
    if not principal:
        logger.warning("Authentication rejected stage=credentials status=401")
        raise HTTPException(status_code=401, detail="Invalid username or password")
    logger.info("Authentication accepted stage=credentials status=200")
    return {
        "access_token": create_access_token(username),
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "user": {"username": principal.username, "role": principal.role},
    }


@app.get("/", include_in_schema=False)
def home(request: Request):
    principal = _web_principal(request)
    if not principal:
        return RedirectResponse("/login", status_code=303)
    return RedirectResponse("/dashboard" if principal.role == "admin" else "/notification-center", status_code=303)


def _web_user(request: Request) -> str | None:
    principal = _web_principal(request)
    return principal.username if principal else None


def _web_principal(request: Request) -> Principal | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    username = verify_access_token(token) if token else None
    return principal_for_username(username) if username else None


def _authenticate_login(username: str, password: str) -> Principal | None:
    """DB user credentials first; retain the configured admin as bootstrap fallback."""
    db = SessionLocal()
    allow_legacy_fallback = False
    try:
        user = db.scalar(select(User).where(User.username == username))
        if user is not None:
            if not user.is_active or not verify_user_password(password, user.password_hash):
                return None
            user.last_login_at = datetime.utcnow()
            db.commit()
            return Principal(user.id, user.username, user.role, user.is_active)
        allow_legacy_fallback = (db.scalar(select(func.count(User.id))) or 0) == 0
    except OperationalError as exc:
        if "no such table: users" in str(exc).lower() or "doesn't exist" in str(exc).lower():
            allow_legacy_fallback = True
        else:
            return None
    finally:
        db.close()

    if allow_legacy_fallback and username == settings.admin_username and verify_password(password):
        return Principal(None, username, "admin", True)
    return None


def _render_page(request: Request, template: str, active: str, **context):
    principal = _web_principal(request)
    if not principal:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name=template,
        context={
            "active": active,
            "current_user": principal.username,
            "current_role": principal.role,
            "is_admin": principal.role == "admin",
            **context,
        },
    )


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request):
    principal = _web_principal(request)
    if principal:
        return RedirectResponse("/dashboard" if principal.role == "admin" else "/notification-center", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={})


@app.post("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_form(request: Request, username: str = Form(...), password: str = Form(...)):
    """POST fallback for browsers when client-side JavaScript is unavailable."""
    principal = _authenticate_login(username, password)
    if not principal:
        logger.warning("Authentication rejected stage=html_form status=401")
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"login_error": "Invalid username or password."},
            status_code=401,
        )
    logger.info("Authentication accepted stage=html_form status=303")
    response = RedirectResponse("/dashboard" if principal.role == "admin" else "/notification-center", status_code=303)
    _set_session_cookie(response, create_access_token(username), request)
    return response


def _set_session_cookie(response, access_token: str, request: Request) -> None:
    secure_cookie = request.url.scheme == "https"
    response.set_cookie(
        SESSION_COOKIE_NAME,
        access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=secure_cookie,
        samesite="strict",
        path="/",
    )


@app.post("/web/session", include_in_schema=False)
def create_web_session(payload: WebSessionRequest, request: Request):
    username = verify_access_token(payload.access_token)
    if not username or not principal_for_username(username):
        logger.warning("Authentication rejected stage=browser_session status=401")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    response = JSONResponse({"ok": True})
    _set_session_cookie(response, payload.access_token, request)
    secure_cookie = request.url.scheme == "https"
    logger.info("Browser session created status=200 secure_cookie=%s", secure_cookie)
    return response


@app.post("/logout", include_in_schema=False)
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/", httponly=True, samesite="strict")
    return response


def _render_admin_page(request: Request, template: str, active: str, **context):
    principal = _web_principal(request)
    if not principal:
        return RedirectResponse("/login", status_code=303)
    if principal.role != "admin":
        return RedirectResponse("/notification-center", status_code=303)
    return _render_page(request, template, active, **context)


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard_page(request: Request):
    major_events = events(event_type="new_major_release", os=None)[:5]
    check_result = service.last_check_result or {}
    return _render_admin_page(
        request,
        "dashboard.html",
        "dashboard",
        major_events=major_events,
        provider_errors=check_result.get("errors", []),
    )


@app.get("/os", response_class=HTMLResponse, include_in_schema=False)
def operating_systems_page(request: Request):
    return _render_admin_page(request, "dashboard.html", "os", os_index=True)


@app.get("/os/{slug}", response_class=HTMLResponse, include_in_schema=False)
def os_detail_page(slug: str, request: Request):
    return _render_admin_page(request, "os_detail.html", "os", slug=slug)


@app.get("/releases", response_class=HTMLResponse, include_in_schema=False)
def releases_page(request: Request):
    return _render_admin_page(request, "releases.html", "releases")


@app.get("/events", response_class=HTMLResponse, include_in_schema=False)
def events_page(request: Request):
    return _render_admin_page(request, "events.html", "events")


@app.get("/settings", response_class=HTMLResponse, include_in_schema=False)
def settings_page(request: Request):
    principal = _web_principal(request)
    if not principal:
        return RedirectResponse("/login", status_code=303)
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator role required")
    return _render_page(request, "settings.html", "settings")


@app.get("/users", response_class=HTMLResponse, include_in_schema=False)
def users_page(request: Request):
    principal = _web_principal(request)
    if not principal:
        return RedirectResponse("/login", status_code=303)
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator role required")
    return _render_page(request, "users.html", "users")


@app.get("/tidio", response_class=HTMLResponse, include_in_schema=False)
def tidio_page(request: Request):
    return _render_admin_page(request, "tidio.html", "tidio")


@app.get("/account", response_class=HTMLResponse, include_in_schema=False)
def account_page(request: Request):
    return _render_page(request, "account.html", "account")


@app.get("/notification-center", response_class=HTMLResponse, include_in_schema=False)
def notification_center_page(request: Request):
    return _render_page(request, "notifications.html", "notifications")


@app.get("/notifications", response_class=HTMLResponse, include_in_schema=False)
def notifications_legacy_page(request: Request):
    return RedirectResponse("/notification-center", status_code=303)


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


@app.get("/api/v1/os", dependencies=[Depends(require_admin)])
def list_os():
    db = SessionLocal()
    try:
        rows = db.scalars(select(OSRelease).order_by(OSRelease.slug)).all()
        return [serialize_os(r) for r in rows]
    finally:
        db.close()


@app.get("/api/v1/os/{slug}", dependencies=[Depends(require_admin)])
def get_os(slug: str):
    db = SessionLocal()
    try:
        row = db.scalar(select(OSRelease).where(OSRelease.slug == slug))
        if not row:
            raise HTTPException(status_code=404, detail="OS not found")
        return serialize_os(row)
    finally:
        db.close()


@app.get("/api/v1/releases", dependencies=[Depends(require_admin)])
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


@app.get("/api/v1/releases/{slug}", dependencies=[Depends(require_admin)])
def releases_for_os(slug: str):
    return releases(os=slug, release_type=None, date=None, limit=None, offset=0)


@app.get("/api/v1/events", dependencies=[Depends(require_admin)])
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


@app.post("/api/v1/check", dependencies=[Depends(require_admin)])
async def check():
    return await check_all()


@app.post("/api/v1/notifications/test/telegram", dependencies=[Depends(require_admin)])
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


def _serialize_notification(notification: Notification) -> dict:
    return {
        "id": notification.id,
        "source": notification.source,
        "title": notification.title,
        "message": notification.message,
        "status": notification.status,
        "severity": notification.severity,
        "requires_approval": notification.requires_approval,
        "approval_status": notification.approval_status,
        "approved_by": notification.approved_by,
        "approved_at": _utc_timestamp(notification.approved_at),
        "denial_reason": notification.denial_reason,
        "task_id": notification.task_id,
        "task_name": notification.task_name,
        "report_id": notification.report_id,
        "metadata": metadata_for(notification),
        "completed_at": _utc_timestamp(notification.completed_at),
        "external_url": notification.external_url,
        "created_at": _utc_timestamp(notification.created_at),
        "updated_at": _utc_timestamp(notification.updated_at),
    }


def _validate_notification_payload(payload: NotificationCreate) -> None:
    if payload.source not in ALLOWED_SOURCES:
        raise HTTPException(status_code=422, detail="Invalid notification source")
    if payload.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid notification status")
    if payload.severity not in ALLOWED_SEVERITIES:
        raise HTTPException(status_code=422, detail="Invalid notification severity")
    if payload.approval_status is not None and payload.approval_status not in {"not_required", "pending"}:
        raise HTTPException(status_code=422, detail="OpenClaw may only create pending approval requests")
    if payload.requires_approval and payload.approval_status == "not_required":
        raise HTTPException(status_code=422, detail="Approval requests must use pending approval status")
    if len(json.dumps(payload.metadata, ensure_ascii=False)) > 10000:
        raise HTTPException(status_code=413, detail="Notification metadata is too large")


def _openclaw_authorized(authorization: str | None) -> bool:
    configured = settings.openclaw_notification_api_key.strip()
    if not configured or not authorization:
        return False
    scheme, _, token = authorization.partition(" ")
    return scheme.lower() == "bearer" and bool(token) and hmac.compare_digest(token.strip(), configured)


@app.post("/api/v1/notifications", status_code=201)
def create_openclaw_notification(payload: NotificationCreate, authorization: str | None = Header(default=None)):
    if not _openclaw_authorized(authorization):
        raise HTTPException(status_code=401, detail="Valid OpenClaw notification credentials required", headers={"WWW-Authenticate": "Bearer"})
    _validate_notification_payload(payload)
    if payload.source != "openclaw":
        raise HTTPException(status_code=403, detail="OpenClaw endpoint accepts only openclaw notifications")
    try:
        notification = create_notification(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _serialize_notification(notification)


@app.get("/api/v1/notifications")
def list_notifications(
    principal: Principal = Depends(authenticate_token),
    source: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    since: datetime | None = Query(default=None),
):
    db = SessionLocal()
    try:
        stmt = select(Notification)
        count_stmt = select(func.count(Notification.id))
        filters = []
        if source:
            source = source.strip().lower()
            if source not in ALLOWED_SOURCES:
                raise HTTPException(status_code=422, detail="Invalid notification source")
            filters.append(Notification.source == source)
        if severity:
            severity = severity.strip().lower()
            if severity not in ALLOWED_SEVERITIES:
                raise HTTPException(status_code=422, detail="Invalid notification severity")
            filters.append(Notification.severity == severity)
        if status:
            status = status.strip().lower()
            if status not in ALLOWED_STATUSES:
                raise HTTPException(status_code=422, detail="Invalid notification status")
            filters.append(Notification.status == status)
        if approval_status:
            approval_status = approval_status.strip().lower()
            if approval_status not in {"not_required", "pending", "approved", "denied"}:
                raise HTTPException(status_code=422, detail="Invalid approval status")
            filters.append(Notification.approval_status == approval_status)
        if since:
            filters.append(Notification.created_at > since.replace(tzinfo=None) if since.tzinfo else Notification.created_at > since)
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        total = db.scalar(count_stmt) or 0
        rows = db.scalars(stmt.order_by(Notification.created_at.desc(), Notification.id.desc()).offset(offset).limit(limit)).all()
        return {"items": [_serialize_notification(row) for row in rows], "total": total, "limit": limit, "offset": offset}
    finally:
        db.close()


@app.get("/api/v1/notifications/{notification_id}")
def get_notification(
    notification_id: int,
    request: Request,
    authorization: str | None = Header(default=None),
):
    human_authorized = False
    try:
        human_authorized = bool(_web_principal(request))
    except Exception:
        human_authorized = False
    if not human_authorized and not _openclaw_authorized(authorization):
        raise HTTPException(status_code=401, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    db = SessionLocal()
    try:
        notification = db.get(Notification, notification_id)
        if notification is None:
            raise HTTPException(status_code=404, detail="Notification not found")
        return _serialize_notification(notification)
    finally:
        db.close()


@app.post("/api/v1/notifications/test", status_code=201, dependencies=[Depends(require_admin)])
def test_notification(current: Principal = Depends(require_admin)):
    notification = create_notification(
        source="watchtower",
        title="Test Notification",
        message="This is a test notification from the WatchTower Management Panel.",
        status="new",
        severity="info",
        requires_approval=False,
        metadata={"test": True, "source": "management_panel"},
    )
    logger.info("notification_test actor=%s notification_id=%s", current.username, notification.id)
    return _serialize_notification(notification)


@app.post("/api/v1/notifications/{notification_id}/approve")
def approve_notification(notification_id: int, current: Principal = Depends(authenticate_token)):
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        result = db.execute(
            update(Notification)
            .where(Notification.id == notification_id, Notification.requires_approval.is_(True), Notification.approval_status == "pending")
            .values(
                approval_status="approved",
                status="resolved",
                approved_by=current.username,
                approved_at=now,
                denial_reason=None,
                updated_at=now,
            )
        )
        if result.rowcount != 1:
            notification = db.get(Notification, notification_id)
            if notification is None:
                raise HTTPException(status_code=404, detail="Notification not found")
            if not notification.requires_approval:
                raise HTTPException(status_code=409, detail="This notification does not require approval")
            raise HTTPException(status_code=409, detail=f"Notification is already {notification.approval_status}")
        db.commit()
        notification = db.get(Notification, notification_id)
        logger.info("notification_decision actor=%s notification_id=%s decision=approved task_id=%s", current.username, notification.id, notification.task_id)
        return _serialize_notification(notification)
    finally:
        db.close()

class NotificationDenyRequest(BaseModel):
    reason: str | None = None


@app.post("/api/v1/notifications/{notification_id}/deny")
def deny_notification(
    notification_id: int,
    payload: NotificationDenyRequest | None = None,
    current: Principal = Depends(authenticate_token),
):
    reason = (payload.reason.strip() if payload and payload.reason else None)
    if reason and len(reason) > 1000:
        raise HTTPException(status_code=422, detail="Denial reason is too long")
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        result = db.execute(
            update(Notification)
            .where(Notification.id == notification_id, Notification.requires_approval.is_(True), Notification.approval_status == "pending")
            .values(
                approval_status="denied",
                status="resolved",
                approved_by=current.username,
                approved_at=now,
                denial_reason=reason,
                updated_at=now,
            )
        )
        if result.rowcount != 1:
            notification = db.get(Notification, notification_id)
            if notification is None:
                raise HTTPException(status_code=404, detail="Notification not found")
            if not notification.requires_approval:
                raise HTTPException(status_code=409, detail="This notification does not require approval")
            raise HTTPException(status_code=409, detail=f"Notification is already {notification.approval_status}")
        db.commit()
        notification = db.get(Notification, notification_id)
        logger.info("notification_decision actor=%s notification_id=%s decision=denied task_id=%s", current.username, notification.id, notification.task_id)
        return _serialize_notification(notification)
    finally:
        db.close()

class TidioConnectRequest(BaseModel):
    username: str
    password: str


class TidioVerificationAction(BaseModel):
    action: Literal["click", "scroll", "type", "press"]
    x: int | None = None
    y: int | None = None
    delta_y: int | None = None
    value: str | None = None


def _tidio_status_payload() -> dict:
    db = SessionLocal()
    try:
        row = db.get(TidioConnection, 1)
        snapshot = tidio_monitor.snapshot
        return {
            "configured": bool(row and row.username and row.password_encrypted),
            "username": row.username if row else None,
            "status": snapshot.status if snapshot.status != "not_configured" else (row.status if row else "not_configured"),
            "connected": snapshot.connected,
            "unassigned_chats": snapshot.unassigned_count,
            "last_checked_at": _utc_timestamp(row.last_checked_at) if row else snapshot.last_checked_at,
            "last_error": snapshot.error or (row.last_error if row else None),
            "poll_interval_seconds": 3,
            "verification_required": snapshot.status == "manual_verification_required",
        }
    finally:
        db.close()


@app.get("/api/v1/tidio", dependencies=[Depends(require_admin)])
def tidio_status():
    return _tidio_status_payload()


@app.post("/api/v1/tidio/connect", dependencies=[Depends(require_admin)])
async def tidio_connect(payload: TidioConnectRequest):
    username = payload.username.strip()
    if not username or not payload.password:
        raise HTTPException(status_code=422, detail="Tidio username and password are required")
    result = await tidio_monitor.connect(username, payload.password)
    if not result.connected:
        return JSONResponse(
            {"success": False, "error": result.error or "Tidio connection failed", "status": result.status},
            status_code=503,
        )
    return {"success": True, **_tidio_status_payload()}


@app.post("/api/v1/tidio/disconnect", dependencies=[Depends(require_admin)])
async def tidio_disconnect():
    await tidio_monitor.disconnect()
    return {"success": True, **_tidio_status_payload()}


@app.get("/api/v1/tidio/verification/screenshot", dependencies=[Depends(require_admin)])
async def tidio_verification_screenshot():
    try:
        screenshot = await tidio_monitor.verification_screenshot()
    except Exception:
        screenshot = None
    if screenshot is None:
        raise HTTPException(status_code=409, detail="Tidio verification is not active. Reconnect to start a new session.")
    return Response(screenshot, media_type="image/png", headers={"Cache-Control": "no-store", "Pragma": "no-cache"})


@app.post("/api/v1/tidio/verification/action", dependencies=[Depends(require_admin)])
async def tidio_verification_action(payload: TidioVerificationAction):
    try:
        accepted = await tidio_monitor.verification_action(
            payload.action, x=payload.x, y=payload.y, delta_y=payload.delta_y, value=payload.value
        )
    except Exception:
        accepted = False
    if not accepted:
        raise HTTPException(status_code=409, detail="Tidio verification session ended or the action was invalid.")
    return {"success": True}


@app.post("/api/v1/tidio/verification/resume", dependencies=[Depends(require_admin)])
async def tidio_verification_resume():
    await tidio_monitor.resume_verification()
    return {"success": tidio_monitor.snapshot.connected, **_tidio_status_payload()}


@app.get("/api/v1/providers", dependencies=[Depends(require_admin)])
def providers():
    return {"providers": list(PROVIDERS.keys())}


@app.get("/api/v1/status", dependencies=[Depends(require_admin)])
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


def _serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": _utc_timestamp(user.created_at),
        "updated_at": _utc_timestamp(user.updated_at),
        "last_login_at": _utc_timestamp(user.last_login_at),
    }


def _get_managed_user(db, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _ensure_another_active_admin(db, user: User) -> None:
    if user.role == "admin" and user.is_active:
        active_admins = db.scalar(select(func.count(User.id)).where(User.role == "admin", User.is_active.is_(True))) or 0
        if active_admins <= 1:
            raise HTTPException(status_code=409, detail="WatchTower must retain at least one active administrator")


@app.get("/api/v1/account", dependencies=[Depends(authenticate_token)])
def get_account(current: Principal = Depends(authenticate_token)):
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.username == current.username))
        if user is None:
            return {"username": current.username, "role": current.role, "is_active": True,
                    "created_at": None, "updated_at": None, "last_login_at": None}
        return _serialize_user(user)
    finally:
        db.close()


@app.post("/api/v1/account/change-password", dependencies=[Depends(authenticate_token)])
def change_own_password(payload: PasswordChange, current: Principal = Depends(authenticate_token)):
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.username == current.username))
        if user is None:
            raise HTTPException(status_code=409, detail="This account password is managed by server configuration")
        if not verify_user_password(payload.current_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        user.password_hash = hash_user_password(payload.new_password)
        user.updated_at = datetime.utcnow()
        db.commit()
        logger.info("user_audit actor=%s action=password_changed_self target=%s", current.username, user.username)
        return {"success": True}
    finally:
        db.close()


@app.get("/api/v1/users", dependencies=[Depends(require_admin)])
def list_users():
    db = SessionLocal()
    try:
        users = db.scalars(select(User).order_by(User.created_at, User.id)).all()
        return [_serialize_user(user) for user in users]
    finally:
        db.close()


@app.post("/api/v1/users", status_code=201, dependencies=[Depends(require_admin)])
def create_user(payload: UserCreate, current: Principal = Depends(require_admin)):
    db = SessionLocal()
    try:
        if db.scalar(select(User.id).where(User.username == payload.username)) is not None:
            raise HTTPException(status_code=409, detail="Username is already in use")
        user = User(
            username=payload.username,
            password_hash=hash_user_password(payload.password),
            role=payload.role,
            is_active=payload.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Username is already in use")
        db.refresh(user)
        logger.info("user_audit actor=%s action=user_created target_id=%s target=%s role=%s", current.username, user.id, user.username, user.role)
        return _serialize_user(user)
    finally:
        db.close()


@app.get("/api/v1/users/{user_id}", dependencies=[Depends(require_admin)])
def get_user(user_id: int):
    db = SessionLocal()
    try:
        return _serialize_user(_get_managed_user(db, user_id))
    finally:
        db.close()


@app.patch("/api/v1/users/{user_id}", dependencies=[Depends(require_admin)])
def update_user(user_id: int, payload: UserUpdate, current: Principal = Depends(require_admin)):
    db = SessionLocal()
    try:
        user = _get_managed_user(db, user_id)
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            raise HTTPException(status_code=400, detail="No user changes were provided")
        if "username" in changes and changes["username"] != user.username:
            if current.id == user.id:
                raise HTTPException(status_code=409, detail="Sign in again before changing your own username")
            if db.scalar(select(User.id).where(User.username == changes["username"])) is not None:
                raise HTTPException(status_code=409, detail="Username is already in use")
        becoming_inactive_admin = user.role == "admin" and user.is_active and (
            changes.get("role", user.role) != "admin" or changes.get("is_active", user.is_active) is False
        )
        if becoming_inactive_admin:
            _ensure_another_active_admin(db, user)
        if current.id == user.id and (changes.get("role", user.role) != "admin" or changes.get("is_active", user.is_active) is False):
            raise HTTPException(status_code=409, detail="You cannot disable or demote your own account")
        old_role, old_active, old_username = user.role, user.is_active, user.username
        for key, value in changes.items():
            setattr(user, key, value)
        user.updated_at = datetime.utcnow()
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Username is already in use")
        db.refresh(user)
        logger.info("user_audit actor=%s action=user_updated target_id=%s target=%s role_changed=%s active_changed=%s", current.username, user.id, user.username, old_role != user.role, old_active != user.is_active)
        if old_role != user.role:
            logger.info("user_audit actor=%s action=role_changed target_id=%s old_role=%s new_role=%s", current.username, user.id, old_role, user.role)
        if old_username != user.username:
            logger.info("user_audit actor=%s action=username_changed target_id=%s old_username=%s new_username=%s", current.username, user.id, old_username, user.username)
        if old_active != user.is_active:
            logger.info("user_audit actor=%s action=user_%s target_id=%s target=%s", current.username, "enabled" if user.is_active else "disabled", user.id, user.username)
        return _serialize_user(user)
    finally:
        db.close()


@app.post("/api/v1/users/{user_id}/reset-password", dependencies=[Depends(require_admin)])
def reset_user_password(user_id: int, payload: PasswordReset, current: Principal = Depends(require_admin)):
    db = SessionLocal()
    try:
        user = _get_managed_user(db, user_id)
        user.password_hash = hash_user_password(payload.new_password)
        user.updated_at = datetime.utcnow()
        db.commit()
        logger.info("user_audit actor=%s action=password_reset target_id=%s target=%s", current.username, user.id, user.username)
        return {"success": True}
    finally:
        db.close()


@app.post("/api/v1/users/{user_id}/enable", dependencies=[Depends(require_admin)])
def enable_user(user_id: int, current: Principal = Depends(require_admin)):
    return _set_user_active(user_id, True, current)


@app.post("/api/v1/users/{user_id}/disable", dependencies=[Depends(require_admin)])
def disable_user(user_id: int, current: Principal = Depends(require_admin)):
    return _set_user_active(user_id, False, current)


def _set_user_active(user_id: int, active: bool, current: Principal):
    db = SessionLocal()
    try:
        user = _get_managed_user(db, user_id)
        if current.id == user.id and not active:
            raise HTTPException(status_code=409, detail="You cannot disable your own account")
        if user.is_active == active:
            return _serialize_user(user)
        if not active:
            _ensure_another_active_admin(db, user)
        user.is_active = active
        user.updated_at = datetime.utcnow()
        db.commit()
        logger.info("user_audit actor=%s action=user_%s target_id=%s target=%s", current.username, "enabled" if active else "disabled", user.id, user.username)
        return _serialize_user(user)
    finally:
        db.close()


@app.delete("/api/v1/users/{user_id}", dependencies=[Depends(require_admin)])
def delete_user(user_id: int, current: Principal = Depends(require_admin)):
    db = SessionLocal()
    try:
        user = _get_managed_user(db, user_id)
        if current.id == user.id:
            raise HTTPException(status_code=409, detail="You cannot delete your own account")
        _ensure_another_active_admin(db, user)
        target_name = user.username
        db.delete(user)
        db.commit()
        logger.info("user_audit actor=%s action=user_deleted target_id=%s target=%s", current.username, user_id, target_name)
        return {"success": True}
    finally:
        db.close()
