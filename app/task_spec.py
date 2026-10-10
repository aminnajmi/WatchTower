"""Task specification matching OpenClaw's fail-closed execution core."""
import hashlib
import json
import re
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, StrictInt, field_validator


class TaskSpecification(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: StrictInt
    task_type: str
    url: str

    @field_validator("version")
    @classmethod
    def supported_version(cls, value: int) -> int:
        if value != 1:
            raise ValueError("Unsupported task schema version")
        return value

    @field_validator("task_type")
    @classmethod
    def supported_task(cls, value: str) -> str:
        if value != "public_website_inspection":
            raise ValueError("Unsupported task type")
        return value

    @field_validator("url")
    @classmethod
    def normalize_public_url(cls, value: str) -> str:
        if not isinstance(value, str) or not value or len(value) > 2048:
            raise ValueError("Invalid URL")
        try:
            parts = urlsplit(value)
            host = parts.hostname
            port = parts.port
        except ValueError as exc:
            raise ValueError("Invalid URL") from exc
        if (
            parts.scheme.lower() != "https"
            or not host
            or parts.username
            or parts.password
            or port not in (None, 443)
            or parts.query
            or parts.fragment
        ):
            raise ValueError("Only credential-free HTTPS URLs on port 443 without query or fragment are allowed")
        try:
            host = host.rstrip(".").encode("idna").decode("ascii").lower()
        except UnicodeError as exc:
            raise ValueError("Invalid hostname") from exc
        if "." not in host or host in {"localhost", "localhost.localdomain"}:
            raise ValueError("A public fully-qualified hostname is required")
        if ":" in host or all(char in "0123456789." for char in host):
            raise ValueError("IP literal targets are not permitted")
        if len(host) > 253 or any(
            not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
            for label in host.split(".")
        ):
            raise ValueError("Invalid hostname")
        if any(ord(char) < 0x20 or ord(char) == 0x7F or char == "\\" for char in value):
            raise ValueError("URL contains disallowed characters")
        path = parts.path or "/"
        return urlunsplit(("https", host, path, "", ""))


def canonical_task_json(specification: TaskSpecification) -> str:
    """Match execution_core.TaskSpec.canonical_json exactly."""
    return json.dumps(
        specification.model_dump(mode="json"),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def task_digest(canonical_json: str) -> str:
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
