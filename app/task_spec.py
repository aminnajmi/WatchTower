"""Versioned, deliberately small task language for external execution."""
import hashlib
import ipaddress
import json
import re
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator


class InspectionParameters(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    scope: str = "public_pages"
    max_pages: StrictInt = Field(default=5, ge=1, le=20)

    @field_validator("scope")
    @classmethod
    def supported_scope(cls, value: str) -> str:
        if value != "public_pages":
            raise ValueError("Only public_pages scope is supported")
        return value


class TaskSpecification(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: StrictInt = 1
    task_type: str = "public_website_inspection"
    target: str
    parameters: InspectionParameters = Field(default_factory=InspectionParameters)

    @field_validator("schema_version")
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

    @field_validator("target")
    @classmethod
    def normalize_public_target(cls, value: str) -> str:
        if not isinstance(value, str) or not value or value != value.strip():
            raise ValueError("Target must be a normalized HTTP or HTTPS URL")
        if any(ord(ch) < 0x20 or ord(ch) == 0x7f for ch in value) or "\\" in value:
            raise ValueError("Target contains forbidden characters")
        if re.search(r"%(?![0-9A-Fa-f]{2})", value):
            raise ValueError("Target contains an invalid percent encoding")
        if "?" in value or "#" in value:
            raise ValueError("Target query strings and fragments are not supported")
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("Target URL is malformed") from exc
        scheme = parsed.scheme.lower()
        if scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Target must use HTTP or HTTPS and include a host")
        if parsed.username is not None or parsed.password is not None or "@" in parsed.netloc:
            raise ValueError("Target credentials are forbidden")
        if parsed.fragment:
            raise ValueError("Target fragments are forbidden")
        # Query strings can carry access tokens and are not needed for a public
        # page crawl. Encoded separators/dots are rejected to avoid parser drift.
        if parsed.query:
            raise ValueError("Target query strings are not supported")
        if re.search(r"%(?:25|2f|5c|2e|00|0[0-9a-f]|1[0-9a-f]|7f)", parsed.path, re.IGNORECASE):
            raise ValueError("Target contains an ambiguous encoded path")
        if re.search(r"(?:^|/)(?:access[_-]?token|api[_-]?key|authorization|password|secret|session|token)(?:/|=|$)", parsed.path, re.IGNORECASE):
            raise ValueError("Target path appears to contain credential material")
        host = parsed.hostname.rstrip(".").lower()
        if not host:
            raise ValueError("Target host is invalid")
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            try:
                host = host.encode("idna").decode("ascii")
            except UnicodeError as exc:
                raise ValueError("Target host is invalid") from exc
            if host in {"localhost", "localhost.localdomain"} or host.endswith((".localhost", ".local", ".internal")):
                raise ValueError("Local and internal targets are forbidden")
            if re.fullmatch(r"(?:[0-9]+\.)*[0-9]+", host) or host.startswith("0x"):
                raise ValueError("Non-canonical numeric IP targets are forbidden")
        else:
            if not ip.is_global:
                raise ValueError("Private and reserved IP targets are forbidden")
            host = f"[{host}]" if ip.version == 6 else host
        if port is not None and not 1 <= port <= 65535:
            raise ValueError("Target port is invalid")
        netloc = host
        if port is not None and not (scheme == "http" and port == 80 or scheme == "https" and port == 443):
            netloc += f":{port}"
        path = parsed.path or "/"
        # Keep path bytes stable, but normalize percent escape hex digits.
        path = re.sub(r"%[0-9a-fA-F]{2}", lambda match: match.group(0).upper(), path)
        return urlunsplit((scheme, netloc, path, "", ""))


def canonical_task_json(specification: TaskSpecification) -> str:
    """UTF-8 JSON contract: compact separators, sorted keys, UTF-8 characters."""
    return json.dumps(
        specification.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def task_digest(canonical_json: str) -> str:
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
