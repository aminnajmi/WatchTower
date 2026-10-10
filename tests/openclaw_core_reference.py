"""Minimal test oracle transcribed from the supplied OpenClaw execution_core.py."""
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit


class GateError(ValueError):
    pass


def canonical_public_url(url: Any) -> str:
    if not isinstance(url, str) or not url or len(url) > 2048:
        raise GateError("invalid URL")
    try:
        parts = urlsplit(url)
        host = parts.hostname
        port = parts.port
    except ValueError as exc:
        raise GateError("invalid URL") from exc
    if (
        parts.scheme.lower() != "https" or not host or parts.username or parts.password
        or port not in (None, 443) or parts.query or parts.fragment
    ):
        raise GateError("unsupported URL")
    try:
        host = host.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise GateError("invalid hostname") from exc
    if "." not in host or host in {"localhost", "localhost.localdomain"}:
        raise GateError("public FQDN required")
    if ":" in host or all(char in "0123456789." for char in host):
        raise GateError("IP literal")
    if len(host) > 253 or any(
        not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
        for label in host.split(".")
    ):
        raise GateError("invalid hostname")
    if any(ord(char) < 0x20 or ord(char) == 0x7F or char == "\\" for char in url):
        raise GateError("disallowed characters")
    path = parts.path or "/"
    return urlunsplit(("https", host, path, "", ""))


@dataclass(frozen=True)
class CoreTaskSpec:
    version: int
    task_type: str
    url: str

    def as_dict(self) -> dict[str, Any]:
        return {"version": self.version, "task_type": self.task_type, "url": self.url}

    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), ensure_ascii=True, sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()


def parse_task_spec(value: Any) -> CoreTaskSpec:
    if not isinstance(value, dict) or set(value) != {"version", "task_type", "url"}:
        raise GateError("unrecognized task specification shape")
    if type(value["version"]) is not int or value["version"] != 1 or value["task_type"] != "public_website_inspection":
        raise GateError("unsupported task specification version or type")
    return CoreTaskSpec(1, "public_website_inspection", canonical_public_url(value["url"]))


def verify_approval(
    response: dict[str, Any], *, notification_id: int, action_id: str,
    spec: CoreTaskSpec, now: datetime | None = None,
) -> datetime:
    """Verifier checks copied from execution_core.verify_approval."""
    if (
        type(notification_id) is not int or notification_id <= 0 or not action_id
        or type(response.get("notification_id")) is not int
        or response.get("notification_id") != notification_id
        or not isinstance(response.get("action_id"), str)
        or response.get("action_id") != action_id
    ):
        raise GateError("approval identity mismatch")
    if response.get("requires_approval") is not True or response.get("approval_status") != "approved":
        raise GateError("approval is not approved")
    raw_spec = response.get("task_spec")
    raw_digest = response.get("task_spec_sha256")
    if not isinstance(raw_spec, dict) or not isinstance(raw_digest, str):
        raise GateError("unbound task")
    approved_spec = parse_task_spec(raw_spec)
    if approved_spec.canonical_json() != spec.canonical_json():
        raise GateError("task mismatch")
    if raw_digest != approved_spec.digest() or raw_digest != spec.digest():
        raise GateError("digest mismatch")
    raw_expiry = response.get("approval_expires_at")
    if not isinstance(raw_expiry, str):
        raise GateError("missing expiry")
    try:
        expiry = datetime.fromisoformat(raw_expiry.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GateError("invalid expiry") from exc
    if expiry.tzinfo is None:
        raise GateError("naive expiry")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now >= expiry:
        raise GateError("expired")
    return expiry
