from datetime import datetime
import json
import re
from typing import Any, Literal
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


_SENSITIVE_TEXT = re.compile(
    r"(?i)(?:authorization\s*:\s*bearer\s+|\bbearer\s+)[A-Za-z0-9._~+/=-]{12,}|"
    r"\b(?:api[_-]?key|access[_-]?token|password|secret|private[_-]?key|database_url)\s*[:=]\s*\S+|"
    r"\b(?:postgres(?:ql)?|mysql|sqlite)://\S+|https://api\.telegram\.org/bot\S+|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
)
_SENSITIVE_KEYS = re.compile(r"(?i)(password|secret|token|api[_-]?key|credential|private[_-]?key|database_url)")


def _reject_secret_text(value: str) -> str:
    if _SENSITIVE_TEXT.search(value):
        raise ValueError("Notification content appears to contain sensitive credentials")
    return value


class NotificationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["openclaw", "human_agent", "watchtower", "system"]
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=12000)
    status: Literal["new", "read", "reviewed", "resolved"] = "new"
    severity: Literal["info", "success", "warning", "error", "critical"] = "info"
    task_id: str | None = Field(default=None, max_length=128)
    task_name: str | None = Field(default=None, max_length=200)
    report_id: str | None = Field(default=None, max_length=128)
    metadata: dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime | None = None
    external_url: str | None = Field(default=None, max_length=2048)
    requires_review: bool = False

    @field_validator("title", "message", "task_name")
    @classmethod
    def content_is_safe_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be blank")
        return _reject_secret_text(value)

    @field_validator("task_id", "report_id")
    @classmethod
    def identifiers_are_plain_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value or _SENSITIVE_TEXT.search(value):
            raise ValueError("Identifier is invalid")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_is_bounded_and_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        def inspect(item: Any, depth: int = 0) -> None:
            if depth > 6:
                raise ValueError("Metadata nesting is too deep")
            if isinstance(item, dict):
                for key, child in item.items():
                    if not isinstance(key, str) or len(key) > 100 or _SENSITIVE_KEYS.search(key):
                        raise ValueError("Metadata contains a sensitive or invalid field name")
                    inspect(child, depth + 1)
            elif isinstance(item, list):
                if len(item) > 100:
                    raise ValueError("Metadata list is too large")
                for child in item:
                    inspect(child, depth + 1)
            elif isinstance(item, str):
                _reject_secret_text(item)
                if len(item) > 2000:
                    raise ValueError("Metadata string is too long")
            elif item is not None and not isinstance(item, (bool, int, float)):
                raise ValueError("Metadata must contain JSON values")

        inspect(value)
        if len(json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")) > 16000:
            raise ValueError("Metadata is too large")
        return value

    @field_validator("external_url")
    @classmethod
    def external_link_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("External URL must be a safe HTTP or HTTPS URL")
        return _reject_secret_text(value)


class NotificationResponse(BaseModel):
    id: int
    source: str
    title: str
    message: str
    status: str
    severity: str
    created_at: datetime
    updated_at: datetime
    task_id: str | None = None
    task_name: str | None = None
    report_id: str | None = None
    metadata: dict[str, Any]
    completed_at: datetime | None = None
    reviewed_at: datetime | None = None
    external_url: str | None = None
    requires_review: bool


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=12, max_length=256)
    confirm_password: str = Field(min_length=12, max_length=256)
    role: str = "user"
    is_active: bool = True

    @field_validator("username")
    @classmethod
    def valid_username(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", value):
            raise ValueError("Username must be 3-32 characters using letters, numbers, dot, underscore, or hyphen")
        return value

    @field_validator("role")
    @classmethod
    def valid_role(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"admin", "user"}:
            raise ValueError("Role must be Admin or User")
        return normalized

    @field_validator("is_active", mode="before")
    @classmethod
    def active_must_be_boolean(cls, value):
        if not isinstance(value, bool):
            raise ValueError("Active status must be true or false")
        return value

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Password confirmation does not match")
        return self


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str | None = Field(default=None, min_length=3, max_length=32)
    role: str | None = None
    is_active: bool | None = None

    @field_validator("username")
    @classmethod
    def valid_username(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Username cannot be empty")
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", value):
            raise ValueError("Username must be 3-32 characters using letters, numbers, dot, underscore, or hyphen")
        return value

    @field_validator("role")
    @classmethod
    def valid_role(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Role cannot be empty")
        normalized = value.strip().lower()
        if normalized not in {"admin", "user"}:
            raise ValueError("Role must be Admin or User")
        return normalized

    @field_validator("is_active", mode="before")
    @classmethod
    def active_must_be_boolean(cls, value):
        if not isinstance(value, bool):
            raise ValueError("Active status must be true or false")
        return value


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=12, max_length=256)
    confirm_password: str = Field(min_length=12, max_length=256)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Password confirmation does not match")
        return self


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)
    confirm_password: str = Field(min_length=12, max_length=256)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Password confirmation does not match")
        return self


class ReleaseInfo(BaseModel):
    slug: str
    name: str
    version: str
    major_version: str
    release_date: str | None = None
    source_url: str
    release_type: str
    is_rolling: bool = False
    checked_at: datetime | None = None
    changed: bool = False
    major_release: bool = False
    event_type: str | None = None


class CheckResult(BaseModel):
    checked: int
    failed: int
    changed: int
    major_releases: int
    results: list[ReleaseInfo]
    errors: list[dict]
