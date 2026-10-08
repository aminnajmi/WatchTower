from datetime import datetime
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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

class NotificationCreate(BaseModel):
    source: str = Field(default="openclaw", min_length=1, max_length=30)
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=20000)
    status: str = Field(default="new", min_length=1, max_length=20)
    severity: str = Field(default="info", min_length=1, max_length=20)
    requires_approval: bool = False
    approval_status: str | None = None
    task_id: str | None = Field(default=None, max_length=100)
    task_name: str | None = Field(default=None, max_length=200)
    report_id: str | None = Field(default=None, max_length=100)
    metadata: dict = Field(default_factory=dict)
    completed_at: datetime | None = None
    external_url: str | None = Field(default=None, max_length=2000)

    @field_validator("source", "status", "severity")
    @classmethod
    def normalized_choice(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("external_url")
    @classmethod
    def safe_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        from urllib.parse import urlparse
        parsed = urlparse(value.strip())
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            raise ValueError("external_url must be an HTTP or HTTPS URL")
        return value.strip()
