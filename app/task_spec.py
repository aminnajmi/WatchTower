"""Validated, immutable task specifications used by OpenClaw approvals."""
import hashlib
import json
import re
from typing import Annotated, Literal, Union
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator


class _TaskBase(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    version: StrictInt
    task_type: str

    @field_validator("version")
    @classmethod
    def supported_version(cls, value: int) -> int:
        if value != 1:
            raise ValueError("Unsupported task schema version")
        return value


class PublicWebsiteInspectionTask(_TaskBase):
    task_type: Literal["public_website_inspection"]
    url: str

    @field_validator("url")
    @classmethod
    def normalize_public_url(cls, value: str) -> str:
        if not value or len(value) > 2048:
            raise ValueError("Invalid URL")
        try:
            parts = urlsplit(value)
            host = parts.hostname
            port = parts.port
        except ValueError as exc:
            raise ValueError("Invalid URL") from exc
        if (parts.scheme.lower() != "https" or not host or parts.username or parts.password
                or port not in (None, 443) or parts.query or parts.fragment):
            raise ValueError("Only credential-free HTTPS URLs on port 443 without query or fragment are allowed")
        try:
            host = host.rstrip(".").encode("idna").decode("ascii").lower()
        except UnicodeError as exc:
            raise ValueError("Invalid hostname") from exc
        if "." not in host or host in {"localhost", "localhost.localdomain"}:
            raise ValueError("A public fully-qualified hostname is required")
        if ":" in host or all(char in "0123456789." for char in host):
            raise ValueError("IP literal targets are not permitted")
        if len(host) > 253 or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in host.split(".")):
            raise ValueError("Invalid hostname")
        if any(ord(char) < 0x20 or ord(char) == 0x7F or char == "\\" for char in value):
            raise ValueError("URL contains disallowed characters")
        return urlunsplit(("https", host, parts.path or "/", "", ""))


class BusinessActionTask(_TaskBase):
    task_type: Literal["business_action"]
    system: str = Field(min_length=1, max_length=100)
    action: str = Field(min_length=1, max_length=100)
    target: str = Field(min_length=1, max_length=500)
    parameters: dict

    @field_validator("system", "action", "target")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip() or any(ord(c) < 0x20 or ord(c) == 0x7f for c in value):
            raise ValueError("Business action fields must be non-empty printable text")
        return value

    @model_validator(mode="after")
    def bounded_parameters(self):
        encoded = json.dumps(self.parameters, ensure_ascii=False, allow_nan=False)
        if len(encoded) > 20000:
            raise ValueError("Business action parameters are too large")
        return self


TaskSpec = Annotated[Union[PublicWebsiteInspectionTask, BusinessActionTask], Field(discriminator="task_type")]


class TaskSpecification:
    """Compatibility facade for existing callers; parsing returns the concrete spec model."""
    @staticmethod
    def model_validate(value):
        if not isinstance(value, dict):
            raise ValueError("Task specification must be an object")
        task_type = value.get("task_type")
        model = {"public_website_inspection": PublicWebsiteInspectionTask,
                 "business_action": BusinessActionTask}.get(task_type)
        if model is None:
            raise ValueError("Unsupported task type")
        return model.model_validate(value)

    @staticmethod
    def model_validate_json(value):
        try:
            return TaskSpecification.model_validate(json.loads(value))
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid task specification JSON") from exc


def canonical_task_json(specification: _TaskBase) -> str:
    """Match the execution core's canonical JSON representation."""
    return json.dumps(specification.model_dump(mode="json"), ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def task_digest(canonical_json: str) -> str:
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
