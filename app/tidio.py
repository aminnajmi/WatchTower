from __future__ import annotations

import asyncio
import base64
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

TIDIO_INBOX_URL = "https://www.tidio.com/panel/inbox/operators/conversations/allOperators"
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
        self._diagnostic_secrets: set[str] = set()
        self._login_phase = "idle"

    @property
    def _session_path(self) -> Path:
        return Path(os.environ.get("TIDIO_SESSION_PATH", "/app/data/tidio-session.enc"))

    def _diagnose_page(self, page: Page) -> None:
        page.on("requestfailed", lambda request: self._log_request_failure(request))
        page.on("response", lambda response: self._log_browser_response(response))
        page.on("console", self._log_console_error)
        page.on("pageerror", self._log_page_error)
        page.on("crash", lambda: logger.error("Tidio Chromium page crashed"))

    def _sanitize_diagnostic_text(self, value: str, limit: int = 1200) -> str:
        text = str(value or "")
        for secret in sorted(self._diagnostic_secrets, key=len, reverse=True):
            if secret:
                text = text.replace(secret, "[REDACTED]")
        text = re.sub(r"(?i)\bBearer\s+[^\s,;]+", "Bearer [REDACTED]", text)
        text = re.sub(
            r"(?i)\b(authorization|set-cookie|cookie|password|passwd|token|secret|api[_-]?key|g-recaptcha-response)\b(\s*[:=]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)",
            r"\1\2[REDACTED]", text,
        )
        text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[EMAIL]", text)
        text = re.sub(r"\b[A-Za-z0-9_-]{80,}\b", "[OPAQUE_VALUE]", text)
        text = re.sub(r"\b[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b", "[JWT]", text)

        def safe_url(match: re.Match) -> str:
            raw = match.group(0)
            suffix = ""
            while raw and raw[-1] in "),.;]":
                suffix = raw[-1] + suffix
                raw = raw[:-1]
            parsed = urlparse(raw)
            path = "/".join(
                "[REDACTED]" if len(part) >= 32 or re.fullmatch(r"[0-9a-fA-F-]{32,36}", part) else part
                for part in parsed.path.split("/")
            )
            return f"{parsed.scheme}://{parsed.hostname or 'unknown'}{path}{suffix}"

        text = re.sub(r"https?://[^\s\"'<>]+", safe_url, text)
        return text[:limit]

    @staticmethod
    def _safe_location(value: str) -> str:
        parsed = urlparse(value or "")
        host = parsed.hostname or "unknown"
        parts = [
            "[REDACTED]" if len(part) >= 32 or re.fullmatch(r"[0-9a-fA-F-]{32,36}", part) else part
            for part in parsed.path.split("/")
        ]
        return f"{host}{'/'.join(parts)}"[:180]

    def _log_console_error(self, message) -> None:
        if message.type != "error":
            return
        text = message.text.lower()
        if "content security policy" in text or "content-security-policy" in text:
            category = "csp_violation"
        elif "recaptcha" in text and any(word in text for word in ("error", "failed", "blocked", "undefined")):
            category = "recaptcha_initialization"
        elif "typeerror" in text:
            category = "type_error"
        elif "referenceerror" in text:
            category = "reference_error"
        elif "syntaxerror" in text:
            category = "syntax_error"
        elif "securityerror" in text:
            category = "security_error"
        elif "failed to load resource" in text:
            category = "resource_load"
        elif "net::err_" in text:
            category = "network_error"
        elif "unhandled promise" in text or "uncaught (in promise)" in text:
            category = "promise_error"
        else:
            category = "script_error"
        location = message.location or {}
        source = self._safe_location(location.get("url", ""))
        line = location.get("lineNumber", 0)
        column = location.get("columnNumber", 0)
        safe_text = self._sanitize_diagnostic_text(message.text)
        logger.warning(
            "Tidio browser console error category=%s source=%s line=%s column=%s message=%s",
            category, source, line, column, safe_text,
        )

    def _log_page_error(self, error) -> None:
        message = getattr(error, "message", str(error))
        stack = getattr(error, "stack", "")
        logger.warning(
            "Tidio browser JavaScript exception type=%s message=%s stack=%s",
            type(error).__name__, self._sanitize_diagnostic_text(message),
            self._sanitize_diagnostic_text(stack, limit=2400),
        )

    @property
    def authentication_interaction_available(self) -> bool:
        return self._snapshot.status == "authentication_required" and bool(
            self._page and not self._page.is_closed()
        )

    def _log_request_failure(self, request) -> None:
        parsed = urlparse(request.url)
        host = parsed.hostname or "unknown"
        kind = "recaptcha" if "recaptcha" in host or "recaptcha" in parsed.path else "request"
        location = self._safe_location(request.url)
        failure = self._sanitize_diagnostic_text(request.failure or "unknown", limit=160)
        if kind == "recaptcha":
            logger.warning(
                "Tidio browser recaptcha request failed location=%s resource=%s error=%s",
                location, request.resource_type, failure,
            )
        else:
            logger.warning("Tidio browser request failed location=%s resource=%s error=%s", location, request.resource_type, failure)

    def _log_browser_response(self, response) -> None:
        parsed = urlparse(response.url)
        host = parsed.hostname or "unknown"
        recaptcha_resource = "recaptcha" in host or "recaptcha" in parsed.path.lower()
        headers = response.headers
        if response.status >= 400:
            logger.warning(
                "Tidio browser HTTP error location=%s resource=%s status=%s",
                self._safe_location(response.url), response.request.resource_type, response.status,
            )
        if response.request.resource_type == "document":
            policy = headers.get("content-security-policy", "")
            report_only = headers.get("content-security-policy-report-only", "")
            directives = sorted({piece.strip().split()[0] for piece in policy.split(";") if piece.strip()})
            report_directives = sorted({piece.strip().split()[0] for piece in report_only.split(";") if piece.strip()})
            if directives or report_directives:
                logger.info(
                    "Tidio document CSP location=%s enforced_directives=%s report_only_directives=%s",
                    self._safe_location(response.url), directives[:24], report_directives[:24],
                )
        if host != "code.tidio.co" and not recaptcha_resource:
            return
        content_type = headers.get("content-type", "unknown").split(";", 1)[0][:80]
        nosniff = headers.get("x-content-type-options", "absent")[:40]
        logger.warning(
            "Tidio browser resource response host=%s path=%s resource=%s status=%s content_type=%s nosniff=%s",
            host, parsed.path[:120] if recaptcha_resource else "redacted",
            response.request.resource_type, response.status, content_type, nosniff,
        )

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
            self._diagnostic_secrets = {value for value in (username, password) if value}
            self._login_phase = "browser_setup"
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
                logger.warning(
                    "Tidio login failed phase=%s type=%s message=%s",
                    self._login_phase, type(exc).__name__, self._sanitize_diagnostic_text(str(exc)),
                )
                verification = "verification" in str(exc).lower()
                status = "authentication_required" if verification else "authentication_failed"
                await self._save_credentials(username, password, status, type(exc).__name__)
                # Keep auth-required connections enabled so startup restore can
                # reopen the browser and present the challenge after a restart.
                await self._set_enabled(verification)
                self._snapshot = TidioSnapshot(False, status, error=("Authentication Required: complete Tidio verification, then reconnect" if verification else self._public_error(exc)))
                if not verification:
                    await self._close_browser()
                return self._snapshot

    async def authentication_screenshot(self) -> str:
        if not self.authentication_interaction_available or not self._page:
            raise RuntimeError("No interactive Tidio verification session is active")
        return base64.b64encode(await self._page.screenshot(type="jpeg", quality=65)).decode("ascii")

    async def authentication_action(
        self, action: str, *, x: float | None = None, y: float | None = None,
        text: str | None = None, key: str | None = None, delta_y: float | None = None,
    ) -> None:
        async with self._lock:
            if not self.authentication_interaction_available or not self._page:
                raise RuntimeError("No interactive Tidio verification session is active")
            page = self._page
            if action == "click":
                if x is None or y is None or not (0 <= x <= 1440 and 0 <= y <= 1000):
                    raise ValueError("Click coordinates are outside the Tidio browser view")
                await page.mouse.click(x, y)
            elif action == "type":
                if not text or len(text) > 64:
                    raise ValueError("Text must contain between 1 and 64 characters")
                self._diagnostic_secrets.add(text)
                await page.keyboard.type(text, delay=40)
            elif action == "key":
                if key not in {"Enter", "Tab", "Backspace", "Space", "Escape", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"}:
                    raise ValueError("Unsupported keyboard key")
                await page.keyboard.press(key)
            elif action == "wheel":
                if delta_y is None or not (-600 <= delta_y <= 600):
                    raise ValueError("Scroll amount is outside the permitted range")
                await page.mouse.wheel(0, delta_y)
            else:
                raise ValueError("Unsupported browser action")

    async def finish_authentication(self) -> TidioSnapshot:
        async with self._lock:
            if not self.authentication_interaction_available or not self._page:
                raise RuntimeError("No interactive Tidio verification session is active")
            inbox_loaded = await self._open_inbox()
            if "/panel/login" in urlparse(self._page.url).path:
                self._snapshot = TidioSnapshot(False, "authentication_required", error="Authentication Required: finish Tidio verification in the browser view")
                return self._snapshot
            if not inbox_loaded:
                if await self._verification_required():
                    error = "Authentication Required: finish Tidio verification in the browser view"
                else:
                    await self._log_inbox_not_rendered()
                    error = "Tidio inbox has not rendered yet; review the browser diagnostics and try again"
                self._snapshot = TidioSnapshot(False, "authentication_required", error=error)
                return self._snapshot
            db = SessionLocal()
            try:
                row = db.get(TidioConnection, 1)
                if not row or not row.username or not row.password_encrypted:
                    raise RuntimeError("Stored Tidio credentials are unavailable")
                username = row.username
                password = self.decrypt_password(row.password_encrypted)
            finally:
                db.close()
            now = datetime.utcnow()
            await self._save_credentials(username, password, "connected", None)
            await self._set_enabled(True)
            await self._save_session()
            self._snapshot = TidioSnapshot(True, "connected", last_checked_at=now)
            self._start_monitor_task()
            return self._snapshot

    async def shutdown(self) -> None:
        self._stop_monitor_task()
        self._stop_event.set()
        await self._close_browser()

    async def disconnect(self) -> None:
        async with self._lock:
            self._stop_monitor_task()
            await self._close_browser()
            try:
                self._session_path.unlink(missing_ok=True)
            except OSError as exc:
                logger.warning("Tidio saved browser session could not be removed type=%s", type(exc).__name__)
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
            self._browser = await self._playwright.chromium.launch(
                headless=False,
                ignore_default_args=["--disable-dev-shm-usage"],
            )
        storage_state = None
        try:
            if self._session_path.is_file():
                storage_state = json.loads(self._fernet().decrypt(self._session_path.read_bytes()))
        except Exception as exc:
            logger.warning("Tidio saved browser session unavailable type=%s", type(exc).__name__)
        self._context = await self._browser.new_context(
            viewport={"width": 1440, "height": 1000},
            locale="en-US",
            java_script_enabled=True,
            ignore_https_errors=False,
            storage_state=storage_state,
        )
        self._page = await self._context.new_page()
        self._diagnose_page(self._page)
        logger.info(
            "Tidio browser context configured browser_version=%s viewport=1440x1000 locale=en-US javascript=true "
            "ignore_https_errors=false storage_state_restored=%s",
            self._browser.version, storage_state is not None,
        )

    async def _log_login_phase(self, phase: str, http_status: int | None = None) -> None:
        assert self._page is not None
        try:
            state = await self._page.evaluate("""() => {
                const body = (document.body?.innerText || '').toLowerCase();
                return {
                    readyState: document.readyState,
                    recaptchaWarningVisible: body.includes('your browser is blocking the recaptcha script'),
                    loginFormVisible: !!document.querySelector('input[type="email"], input[type="password"], input[autocomplete="username"]'),
                };
            }""")
        except Exception as exc:
            state = {"diagnosticError": type(exc).__name__}
        logger.info(
            "Tidio login phase=%s path=%s http_status=%s page_state=%s",
            phase, self._safe_location(self._page.url), http_status or "unknown", state,
        )

    async def _log_recaptcha_diagnostics(self, phase: str, *, wait_for_ready: bool) -> None:
        """Inspect API availability and readiness only; never call execute() or read CAPTCHA tokens."""
        assert self._page is not None
        try:
            state = await self._page.evaluate("""async (waitForReady) => {
                const g = window.grecaptcha;
                let readyCallbackCompleted = false;
                if (waitForReady && g && typeof g.ready === 'function') {
                    readyCallbackCompleted = await Promise.race([
                        new Promise(resolve => {
                            try { g.ready(() => resolve(true)); }
                            catch (_) { resolve(false); }
                        }),
                        new Promise(resolve => setTimeout(() => resolve(false), 1500)),
                    ]);
                }
                const scripts = Array.from(document.scripts)
                    .filter(script => /recaptcha/i.test(script.src || ''))
                    .slice(0, 12)
                    .map(script => {
                        try {
                            const url = new URL(script.src);
                            return `${url.hostname}${url.pathname.slice(0, 100)}`;
                        } catch (_) { return 'invalid-script-url'; }
                    });
                const policies = Array.from(document.querySelectorAll('meta[http-equiv]'))
                    .filter(meta => meta.httpEquiv.toLowerCase() === 'content-security-policy')
                    .flatMap(meta => (meta.content || '').split(';').map(part => part.trim().split(/\\s+/)[0]))
                    .filter(Boolean);
                let localStorageAvailable = false, localStorageKeys = -1;
                let sessionStorageAvailable = false, sessionStorageKeys = -1;
                try { localStorageAvailable = true; localStorageKeys = localStorage.length; } catch (_) {}
                try { sessionStorageAvailable = true; sessionStorageKeys = sessionStorage.length; } catch (_) {}
                return {
                    readyState: document.readyState,
                    grecaptchaPresent: !!g,
                    readyFunction: !!g && typeof g.ready === 'function',
                    renderFunction: !!g && typeof g.render === 'function',
                    executeFunction: !!g && typeof g.execute === 'function',
                    enterprisePresent: !!g && !!g.enterprise,
                    readyCallbackCompleted,
                    recaptchaScriptTags: scripts,
                    cspMetaDirectives: [...new Set(policies)].slice(0, 24),
                    localStorageAvailable, localStorageKeys,
                    sessionStorageAvailable, sessionStorageKeys,
                    recaptchaWarningVisible: (document.body?.innerText || '').toLowerCase().includes('your browser is blocking the recaptcha script'),
                };
            }""", wait_for_ready)
        except Exception as exc:
            state = {"diagnosticError": type(exc).__name__}

        cookie_counts = {"tidio": 0, "google": 0, "gstatic": 0}
        if self._context:
            try:
                cookies = await self._context.cookies([
                    "https://www.tidio.com", "https://www.google.com", "https://www.gstatic.com",
                ])
                for cookie in cookies:
                    domain = str(cookie.get("domain", "")).lstrip(".").lower()
                    if domain == "tidio.com" or domain.endswith(".tidio.com"):
                        cookie_counts["tidio"] += 1
                    elif domain == "google.com" or domain.endswith(".google.com"):
                        cookie_counts["google"] += 1
                    elif domain == "gstatic.com" or domain.endswith(".gstatic.com"):
                        cookie_counts["gstatic"] += 1
            except Exception as exc:
                cookie_counts["error"] = type(exc).__name__
        logger.info(
            "Tidio reCAPTCHA diagnostics phase=%s path=%s state=%s cookie_counts=%s",
            phase, self._safe_location(self._page.url), state, cookie_counts,
        )

    async def _login(self, username: str, password: str) -> None:
        assert self._page is not None
        page = self._page
        self._login_phase = "open_inbox_for_login"
        response = await page.goto(TIDIO_INBOX_URL, wait_until="domcontentloaded", timeout=30_000)
        # The panel hydrates after the initial document response. Give its
        # client-side router time to redirect to login or render the inbox.
        await page.wait_for_timeout(2_000)
        await self._log_login_phase("login_page_loaded", response.status if response else None)
        await self._log_recaptcha_diagnostics("login_page_loaded", wait_for_ready=True)
        current_path = urlparse(page.url).path
        if "/panel/login" not in current_path:
            email = await self._find_visible_input((
                'input[type="email"]', 'input[autocomplete="username"]',
                'input[name*="email" i]', 'input[name*="user" i]',
                'input[type="text"]', 'input:not([type])',
                '[role="textbox"]', '[contenteditable="true"]', 'textarea',
                'input:not([type="hidden"])',
            ), timeout_ms=500)
            body = (await page.locator("body").inner_text(timeout=3_000)).lower()
            if email is None and "unassigned" in body:
                if not await self._open_inbox():
                    await self._raise_login_page_state("Tidio inbox did not render after restoring the session")
                await self._save_session()
                return
            if email is None:
                await self._raise_login_page_state(
                    f"Tidio panel did not render login or inbox (HTTP {response.status if response else 'unknown'})"
                )
        else:
            email = await self._find_visible_input((
                'input[type="email"]', 'input[autocomplete="username"]',
                'input[name*="email" i]', 'input[name*="user" i]',
                'input[type="text"]', 'input:not([type])',
                '[role="textbox"]', '[contenteditable="true"]', 'textarea',
                'input:not([type="hidden"])',
            ))
        if email is None:
            await self._raise_login_page_state("Tidio username field was not found")
        self._login_phase = "fill_credentials"
        await email.fill(username)

        password_field = await self._find_visible_input(('input[type="password"]',))
        if password_field is None:
            await self._click_login_action()
            password_field = await self._find_visible_input(('input[type="password"]',), timeout_ms=10_000)
        if password_field is None:
            await self._raise_login_page_state("Tidio password field was not found")
        await password_field.fill(password)
        await self._log_login_phase("before_login_submit")
        await self._log_recaptcha_diagnostics("before_login_submit", wait_for_ready=True)
        self._login_phase = "submit_credentials"
        await self._click_login_action()
        self._login_phase = "after_login_submit"
        await page.wait_for_timeout(2_000)
        await self._log_login_phase("after_login_submit")
        await self._log_recaptcha_diagnostics("after_login_submit", wait_for_ready=False)
        try:
            await page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass
        if "/panel/login" in urlparse(page.url).path:
            if await self._verification_required():
                self._login_phase = "verification_required"
                raise RuntimeError("Tidio requires additional browser verification")
            body = (await page.locator("body").inner_text()).lower()
            if any(term in body for term in ("incorrect password", "invalid credentials", "email or password is incorrect", "wrong password")):
                raise RuntimeError("Tidio rejected the supplied credentials")
            raise RuntimeError("Tidio sign-in did not complete; credentials were not confirmed")
        self._login_phase = "open_authenticated_inbox"
        if not await self._open_inbox():
            await self._raise_login_page_state("Tidio inbox did not render after sign-in")
        await self._save_session()

    async def _find_visible_input(self, selectors: tuple[str, ...], timeout_ms: int = 2_000):
        assert self._page is not None
        for frame in self._page.frames:
            for selector in selectors:
                locator = frame.locator(selector)
                try:
                    await locator.first.wait_for(state="visible", timeout=timeout_ms)
                    return locator.first
                except Exception:
                    continue
        return None

    async def _click_login_action(self) -> None:
        assert self._page is not None
        for name in (r"log in", r"sign in", r"continue", r"next"):
            button = self._page.get_by_role("button", name=re.compile(name, re.I)).first
            try:
                await button.click(timeout=2_000)
                return
            except Exception:
                continue
        await self._raise_login_page_state("Tidio login action was not found")

    async def _raise_login_page_state(self, fallback: str) -> None:
        assert self._page is not None
        body_text = ""
        frame_hosts = []
        input_types = []
        for frame in self._page.frames:
            frame_hosts.append(urlparse(frame.url).hostname or "about:blank")
            try:
                body_text += " " + (await frame.locator("body").inner_text(timeout=1_000)).lower()
            except Exception:
                pass
            try:
                input_types.extend(await frame.locator("input").evaluate_all(
                    "nodes => nodes.map(node => (node.getAttribute('type') || 'text').toLowerCase())"
                ))
            except Exception:
                pass
        if await self._verification_required(body_text):
            raise RuntimeError("Tidio requires additional browser verification")
        try:
            ready_state = await self._page.evaluate("() => document.readyState")
        except Exception:
            ready_state = "unavailable"
        logger.warning(
            "Tidio login form unavailable path=%s ready_state=%s frame_hosts=%s input_types=%s",
            urlparse(self._page.url).path[:100], ready_state,
            sorted(set(frame_hosts))[:8], sorted(set(input_types))[:8],
        )
        raise RuntimeError(fallback)

    async def _verification_required(self, existing_text: str = "") -> bool:
        assert self._page is not None
        markers = ("recaptcha", "captcha", "two-factor", "verification", "verify your identity", "verify you are human")
        if any(marker in existing_text for marker in markers):
            return True
        for frame in self._page.frames:
            frame_url = frame.url.lower()
            if "recaptcha" in frame_url or "challenge" in frame_url:
                return True
            try:
                text = (await frame.locator("body").inner_text(timeout=1_000)).lower()
            except Exception:
                continue
            if any(marker in text for marker in markers):
                return True
        return False

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

    async def _open_inbox(self) -> bool:
        assert self._page is not None
        page = self._page
        try:
            await page.goto(TIDIO_INBOX_URL, wait_until="domcontentloaded", timeout=30_000)
            return await self._wait_for_inbox_content()
        except Exception as exc:
            logger.warning("Tidio inbox navigation failed type=%s", type(exc).__name__)
            return False

    async def _wait_for_inbox_content(self, timeout_ms: int = 15_000) -> bool:
        """Allow Tidio's client-side inbox to hydrate without waiting for analytics idle."""
        assert self._page is not None
        deadline = asyncio.get_running_loop().time() + timeout_ms / 1000
        while True:
            if self._page.is_closed():
                return False
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                return False
            try:
                body = await self._page.locator("body").inner_text(timeout=max(1, min(500, int(remaining * 1000))))
                if "unassigned" in body.lower():
                    return True
            except Exception:
                pass
            if "/panel/login" in urlparse(self._page.url).path:
                return False
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                return False
            await self._page.wait_for_timeout(min(500, int(remaining * 1000)))

    async def _log_inbox_not_rendered(self) -> None:
        """Log page metadata only; never include page text, form values, or URLs with queries."""
        assert self._page is not None
        page = self._page
        try:
            ready_state = await page.evaluate("() => document.readyState")
            body_chars = await page.locator("body").evaluate("node => (node.innerText || '').length")
            has_login_input = await page.locator('input[type="password"], input[autocomplete="username"]').count() > 0
        except Exception:
            ready_state, body_chars, has_login_input = "unavailable", -1, False
        frame_hosts = sorted({urlparse(frame.url).hostname or "about:blank" for frame in page.frames})[:8]
        logger.warning(
            "Tidio inbox did not render path=%s ready_state=%s body_chars=%s login_input=%s frame_hosts=%s",
            self._safe_location(page.url), ready_state, body_chars, has_login_input, frame_hosts,
        )

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
        self._diagnostic_secrets.clear()
        self._login_phase = "idle"

    @staticmethod
    def _public_error(exc: Exception) -> str:
        message = str(exc).strip()
        return message[:200] if message else type(exc).__name__


monitor = TidioMonitor()
