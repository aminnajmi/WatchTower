from __future__ import annotations

import asyncio
import hashlib
import logging
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from .config import settings
from .models import SessionLocal, TidioConnection

logger = logging.getLogger(__name__)

TIDIO_LOGIN_URL = "https://www.tidio.com/panel/login"
POLL_SECONDS = 3


@dataclass
class TidioSnapshot:
    connected: bool
    status: str
    unassigned_count: int = 0
    last_checked_at: datetime | None = None
    error: str | None = None


class TidioMonitor:
    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._stop_event = asyncio.Event()
        self._snapshot = TidioSnapshot(False, "not_configured")
        self._last_unassigned_ids: set[str] = set()
        self._retrying = False

    @property
    def _session_path(self) -> Path:
        return Path(os.environ.get("TIDIO_SESSION_PATH", "/app/data/tidio-session.enc"))

    def _diagnose_page(self, page: Page) -> None:
        page.on("requestfailed", lambda request: self._log_request_failure(request))
        page.on("console", lambda message: logger.warning("Tidio browser console error type=%s", message.type) if message.type == "error" else None)
        page.on("pageerror", lambda error: logger.warning("Tidio browser page error type=%s", type(error).__name__))
        page.on("crash", lambda: logger.error("Tidio Chromium page crashed"))

    @staticmethod
    def _log_request_failure(request) -> None:
        parsed = urlparse(request.url)
        host = parsed.hostname or "unknown"
        kind = "recaptcha" if "recaptcha" in host or "recaptcha" in parsed.path else "request"
        logger.warning("Tidio browser %s request failed host=%s resource=%s error=%s", kind, host, request.resource_type, (request.failure or "unknown")[:160])

    @property
    def snapshot(self) -> TidioSnapshot:
        return self._snapshot

    def _fernet(self) -> Fernet:
        seed = settings.jwt_secret or settings.admin_password_hash or "watchtower-development-tidio-key"
        key = hashlib.sha256(seed.encode("utf-8")).digest()
        import base64
        return Fernet(base64.urlsafe_b64encode(key))

    def encrypt_password(self, password: str) -> str:
        return self._fernet().encrypt(password.encode("utf-8")).decode("ascii")

    def decrypt_password(self, encrypted: str) -> str:
        try:
            return self._fernet().decrypt(encrypted.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise RuntimeError("Stored Tidio credentials cannot be decrypted") from exc

    async def connect(self, username: str, password: str) -> TidioSnapshot:
        username = username.strip()
        if not username or not password:
            raise ValueError("Tidio username and password are required")

        async with self._lock:
            await self._close_browser()
            self._snapshot = TidioSnapshot(False, "connecting")
            await self._save_credentials(username, password, "connecting", None)
            await self._set_enabled(True)
            try:
                await self._ensure_browser()
                await self._login(username, password)
                self._snapshot = TidioSnapshot(True, "connected", last_checked_at=datetime.utcnow())
                await self._save_credentials(username, password, "connected", None)
                self._start_monitor_task()
                return self._snapshot
            except Exception as exc:
                logger.warning("Tidio login failed (%s)", type(exc).__name__)
                verification = "verification" in str(exc).lower()
                status = "authentication_required" if verification else "authentication_failed"
                await self._save_credentials(username, password, status, type(exc).__name__)
                await self._set_enabled(False)
                self._snapshot = TidioSnapshot(False, status, error=("Authentication Required: complete Tidio verification, then reconnect" if verification else self._public_error(exc)))
                await self._close_browser()
                return self._snapshot

    async def shutdown(self) -> None:
        self._stop_monitor_task()
        self._stop_event.set()
        await self._close_browser()

    async def disconnect(self) -> None:
        async with self._lock:
            self._stop_monitor_task()
            await self._close_browser()
            db = SessionLocal()
            try:
                row = db.get(TidioConnection, 1)
                if row:
                    row.status = "disconnected"
                    row.last_error = None
                    row.updated_at = datetime.utcnow()
                    db.commit()
            finally:
                db.close()
            self._snapshot = TidioSnapshot(False, "disconnected")
            self._last_unassigned_ids.clear()

    async def restore(self) -> None:
        db = SessionLocal()
        try:
            row = db.get(TidioConnection, 1)
            if not row or not row.enabled or not row.username or not row.password_encrypted:
                return
            username = row.username
            password = self.decrypt_password(row.password_encrypted)
        except Exception as exc:
            logger.warning("Tidio credential restore failed (%s)", type(exc).__name__)
            self._snapshot = TidioSnapshot(False, "credentials_unavailable", error="Stored credentials are unavailable")
            return
        finally:
            db.close()

        await self.connect(username, password)

    async def _ensure_browser(self) -> None:
        if self._context and self._page and not self._page.is_closed():
            return
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        if self._browser is None:
            self._browser = await self._playwright.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        storage_state = None
        try:
            if self._session_path.is_file():
                storage_state = json.loads(self._fernet().decrypt(self._session_path.read_bytes()))
        except Exception as exc:
            logger.warning("Tidio saved browser session unavailable type=%s", type(exc).__name__)
        self._context = await self._browser.new_context(viewport={"width": 1440, "height": 1000}, locale="en-US", storage_state=storage_state)
        self._page = await self._context.new_page()
        self._diagnose_page(self._page)

    async def _login(self, username: str, password: str) -> None:
        assert self._page is not None
        page = self._page
        await page.goto(TIDIO_LOGIN_URL, wait_until="domcontentloaded", timeout=30_000)
        if "/panel/login" not in urlparse(page.url).path:
            await self._open_inbox()
            await self._save_session()
            return
        await page.locator('input[type="email"]').first.fill(username)
        await page.locator('input[type="password"]').first.fill(password)
        await page.get_by_role("button", name=re.compile(r"log in", re.I)).first.click()
        await page.wait_for_timeout(2_000)
        try:
            await page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass
        if "/panel/login" in urlparse(page.url).path:
            body = (await page.locator("body").inner_text()).lower()
            if "recaptcha" in body or "two-factor" in body or "verification" in body or "authentication required" in body:
                raise RuntimeError("Tidio requires additional browser verification")
            raise RuntimeError("Tidio rejected the supplied credentials")
        await self._open_inbox()
        await self._save_session()

    async def _save_session(self) -> None:
        if not self._context:
            return
        try:
            self._session_path.parent.mkdir(parents=True, exist_ok=True)
            encrypted = self._fernet().encrypt(json.dumps(await self._context.storage_state()).encode("utf-8"))
            self._session_path.write_bytes(encrypted)
            self._session_path.chmod(0o600)
        except Exception as exc:
            logger.warning("Tidio browser session could not be persisted type=%s", type(exc).__name__)

    async def _open_inbox(self) -> None:
        assert self._page is not None
        page = self._page
        try:
            inbox = page.get_by_text("Inbox", exact=True).first
            if await inbox.is_visible(timeout=2_000):
                await inbox.click()
                await page.wait_for_timeout(500)
        except Exception:
            # The login destination may already be the Inbox. Monitoring will
            # validate the presence of the Unassigned view on the next check.
            pass

    def _start_monitor_task(self) -> None:
        self._stop_monitor_task()
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._monitor_loop(), name="tidio-monitor")

    def _stop_monitor_task(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    async def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self._check_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Tidio monitor check failed (%s)", type(exc).__name__)
                self._snapshot = TidioSnapshot(False, "session_expired", error=self._public_error(exc))
                if not self._retrying:
                    self._retrying = True
                    try:
                        await self._reconnect()
                    finally:
                        self._retrying = False
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=POLL_SECONDS)
            except asyncio.TimeoutError:
                pass

    async def _reconnect(self) -> None:
        db = SessionLocal()
        try:
            row = db.get(TidioConnection, 1)
            if not row or not row.password_encrypted:
                return
            username = row.username
            password = self.decrypt_password(row.password_encrypted)
        except Exception:
            return
        finally:
            db.close()

        self._snapshot = TidioSnapshot(False, "reconnecting")
        for delay in (0, 5, 15, 30):
            if delay:
                await asyncio.sleep(delay)
            try:
                await self._close_browser()
                await self._ensure_browser()
                await self._login(username, password)
                self._snapshot = TidioSnapshot(True, "connected", last_checked_at=datetime.utcnow())
                await self._save_credentials(username, password, "connected", None)
                return
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Tidio reconnect failed (%s)", type(exc).__name__)
                await self._save_credentials(username, password, "reconnecting", type(exc).__name__)
                if "verification" in str(exc).lower():
                    self._snapshot = TidioSnapshot(False, "authentication_required", error="Authentication Required: complete Tidio verification, then reconnect")
                    await self._save_credentials(username, password, "authentication_required", "additional verification required")
                    self._stop_event.set()
                    return
        self._snapshot = TidioSnapshot(False, "authentication_failed", error="Tidio session could not be restored")
        self._stop_event.set()

    async def _check_once(self) -> None:
        if not self._page or self._page.is_closed():
            raise RuntimeError("Tidio browser session is unavailable")
        if "/panel/login" in urlparse(self._page.url).path:
            raise RuntimeError("Tidio session expired")

        # Tidio's inbox UI is dynamic. We intentionally use visible text rather
        # than private/internal CSS class names so minor frontend changes are
        # less likely to break monitoring.
        body = await self._page.locator("body").inner_text(timeout=10_000)
        if "unassigned" not in body.lower():
            raise RuntimeError("Tidio inbox/unassigned view is unavailable")

        count = await self._read_unassigned_count()
        now = datetime.utcnow()
        self._snapshot = TidioSnapshot(True, "connected", count, now)
        await self._touch_status(now, None)

    async def _read_unassigned_count(self) -> int:
        assert self._page is not None
        page = self._page
        candidates = page.get_by_text(re.compile(r"^unassigned(?:\s+\d+)?$", re.I))
        count = await candidates.count()
        for index in range(count):
            text = (await candidates.nth(index).inner_text()).strip()
            match = re.search(r"\b(\d+)\b", text)
            if match:
                return int(match.group(1))

        # If the navigation label contains no count, inspect nearby buttons/links.
        for selector in ("button", "a"):
            nodes = page.locator(selector).filter(has_text=re.compile(r"unassigned", re.I))
            node_count = await nodes.count()
            for index in range(node_count):
                text = (await nodes.nth(index).inner_text()).strip()
                match = re.search(r"\b(\d+)\b", text)
                if match:
                    return int(match.group(1))
        return 0

    async def _save_credentials(self, username: str, password: str, status: str, error: str | None) -> None:
        db = SessionLocal()
        try:
            row = db.get(TidioConnection, 1)
            encrypted = self.encrypt_password(password)
            now = datetime.utcnow()
            if row is None:
                row = TidioConnection(
                    id=1,
                    username=username,
                    password_encrypted=encrypted,
                    status=status,
                    last_error=error,
                    created_at=now,
                    updated_at=now,
                )
                db.add(row)
            else:
                row.username = username
                row.password_encrypted = encrypted
                row.status = status
                row.last_error = error
                row.updated_at = now
            db.commit()
        finally:
            db.close()

    async def _set_enabled(self, enabled: bool) -> None:
        db = SessionLocal()
        try:
            row = db.get(TidioConnection, 1)
            if row:
                row.enabled = enabled
                row.updated_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()

    async def _touch_status(self, checked_at: datetime, error: str | None) -> None:
        db = SessionLocal()
        try:
            row = db.get(TidioConnection, 1)
            if row:
                row.status = "connected"
                row.last_checked_at = checked_at
                row.last_error = error
                row.updated_at = checked_at
                db.commit()
        finally:
            db.close()

    async def _close_browser(self) -> None:
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
        self._context = None
        self._page = None
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
        self._browser = None
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
        self._playwright = None
        self._retrying = False

    @staticmethod
    def _public_error(exc: Exception) -> str:
        message = str(exc).strip()
        return message[:200] if message else type(exc).__name__


monitor = TidioMonitor()
