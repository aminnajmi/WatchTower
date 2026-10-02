from dataclasses import dataclass
import re

from .providers.base import Release


@dataclass(frozen=True)
class ParsedVersion:
    major_version: str
    release_type: str


@dataclass(frozen=True)
class ReleaseComparison:
    changed: bool
    major_release: bool
    event_type: str | None


@dataclass(frozen=True)
class ReleaseState:
    version: str
    major_version: str
    is_rolling: bool = False


def compare_releases(previous: ReleaseState | None, current: ReleaseState) -> ReleaseComparison:
    """Compare stored and fetched releases; current-version classification is separate."""
    if previous is None or previous.version == current.version:
        return ReleaseComparison(False, False, None)

    if current.is_rolling:
        return ReleaseComparison(True, False, "new_rolling_release")

    is_major = previous.major_version not in ("", "unknown", "rolling") and previous.major_version != current.major_version
    return ReleaseComparison(True, is_major, "new_major_release" if is_major else "new_minor_release")


def parse_version(release: Release) -> ParsedVersion:
    """Normalize major version and classify the release for deployment tracking."""
    if release.is_rolling:
        return ParsedVersion(major_version="rolling", release_type="rolling")

    version = release.version.strip()

    # Ubuntu uses YY.MM for its major releases and YY.MM.patch for point releases.
    if release.slug == "ubuntu":
        match = re.match(r"^(\d{2})\.(\d{2})(?:\.\d+)?$", version)
        if not match:
            raise ValueError(f"Unsupported Ubuntu version format: {version}")
        major = match.group(1)
        release_type = "minor" if version.count(".") >= 2 else "major"
        return ParsedVersion(major_version=major, release_type=release_type)

    # CentOS Stream versions are e.g. 10-20260930.0. The stream number is the major version.
    if release.slug == "centos":
        match = re.match(r"^(\d+)(?:-|$)", version)
        if not match:
            raise ValueError(f"Unsupported CentOS Stream version format: {version}")
        return ParsedVersion(major_version=match.group(1), release_type="major")

    # Fedora/Debian use integer major versions; Alma/Rocky use X.Y for minor releases.
    match = re.match(r"^(\d+)(?:\.(\d+))?(?:\..*)?$", version)
    if not match:
        raise ValueError(f"Unsupported version format for {release.slug}: {version}")

    major = match.group(1)
    release_type = "minor" if "." in version else "major"
    return ParsedVersion(major_version=major, release_type=release_type)
