from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from urllib.parse import urlsplit

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

bearer = HTTPBearer(auto_error=False)
SESSION_COOKIE_NAME = "os_tracker_session"


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
    return username if username == settings.admin_username else None


def authenticate_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    # Bearer JWT is the normal production authentication method.
    if credentials:
        username = verify_access_token(credentials.credentials)
        if username:
            return username
    else:
        # Browser requests use an HTTP-only cookie created from the existing JWT.
        token = request.cookies.get(SESSION_COOKIE_NAME)
        username = verify_access_token(token) if token else None
        if username:
            if request.method not in {"GET", "HEAD", "OPTIONS"}:
                origin = request.headers.get("origin")
                if not origin or urlsplit(origin).netloc.lower() != urlsplit(_request_origin(request)).netloc.lower() or urlsplit(origin).scheme != urlsplit(_request_origin(request)).scheme:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid request origin")
            return username

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def generate_password_hash(password: str) -> tuple[str, str]:
    salt = secrets.token_bytes(16)
    return _hash_password(password, salt), salt.hex()
