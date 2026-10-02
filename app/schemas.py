from datetime import datetime
from pydantic import BaseModel


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
