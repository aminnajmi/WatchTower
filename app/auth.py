from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
import hashlib
import hmac
import secrets
from urllib.parse import urlsplit

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError

from .config import settings
from .models import SessionLocal, User

bearer = HTTPBearer(auto_error=False)
SESSION_COOKIE_NAME = "os_tracker_session"
_session_factory_provider = lambda: SessionLocal


def configure_session_factory_provider(provider) -> None:
    """Allow the app's configured DB session factory to be injected in tests."""
    global _session_factory_provider
    _session_factory_provider = provider


@dataclass(frozen=True)
class Principal:
    id: int | None
    username: str
    role: str
    is_active: bool = True


def principal_for_username(username: str) -> Principal | None:
    """Resolve every request against current DB state so disable takes effect immediately."""
    db = _session_factory_provider()()
    allow_legacy_fallback = False
    try:
        user = db.scalar(select(User).where(User.username == username))
        if user is not None:
            if not user.is_active:
                return None
            return Principal(user.id, user.username, user.role, user.is_active)
        # The legacy environment admin remains usable only before any user
        # records exist (or before the users table was migrated). Once users
        # exist, a deleted identity must not fall back to administrator access.
        allow_legacy_fallback = (db.scalar(select(func.count(User.id))) or 0) == 0
    except OperationalError as exc:
        # Compatibility for old test fixtures/integrations that have not run
        # init_db yet. A real database error fails closed.
        if "no such table: users" in str(exc).lower() or "doesn't exist" in str(exc).lower():
            allow_legacy_fallback = True
        else:
            return None
    finally:
        db.close()

    # Keep the legacy configured administrator working during first startup
    # and for API clients whose database has not yet been migrated.
    if allow_legacy_fallback and username == settings.admin_username:
        return Principal(None, username, "admin", True)
    return None


def _request_origin(request: Request) -> str:
    # Uvicorn rewrites request.url.scheme only for configured trusted proxies.
    # Ignore X-Forwarded-Host here so a client cannot spoof the CSRF origin.
    scheme = request.url.scheme
    host = request.headers.get("host", request.url.netloc)
    return f"{scheme}://{host}".rstrip("/")


def _hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000).hex()


def verify_password(password: str) -> bool:
    if not settings.admin_password_hash or not settings.admin_password_salt:
        return False
    try:
        salt = bytes.fromhex(settings.admin_password_salt)
        expected = _hash_password(password, salt)
        return hmac.compare_digest(expected, settings.admin_password_hash)
    except ValueError:
        return False


def create_access_token(username: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": username, "exp": expires, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    username = payload.get("sub")
    return username if isinstance(username, str) and username else None


def authenticate_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Principal:
    # Bearer JWT is the normal production authentication method.
    if credentials:
        username = verify_access_token(credentials.credentials)
    else:
        # Browser requests use an HTTP-only cookie created from the existing JWT.
        token = request.cookies.get(SESSION_COOKIE_NAME)
        username = verify_access_token(token) if token else None
        if username:
            if request.method not in {"GET", "HEAD", "OPTIONS"}:
                origin = request.headers.get("origin")
                if not origin or urlsplit(origin).netloc.lower() != urlsplit(_request_origin(request)).netloc.lower() or urlsplit(origin).scheme != urlsplit(_request_origin(request)).scheme:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid request origin")
    if username:
        principal = principal_for_username(username)
        if principal:
            return principal

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_admin(principal: Principal = Depends(authenticate_token)) -> Principal:
    if principal.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator role required")
    return principal


def generate_password_hash(password: str) -> tuple[str, str]:
    salt = secrets.token_bytes(16)
    return _hash_password(password, salt), salt.hex()


def hash_user_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = _hash_password(password, salt)
    return f"pbkdf2_sha256$310000${salt.hex()}${digest}"


def verify_user_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256" or int(iterations) != 310_000:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False
