import re
from .base import Provider, Release
from .http import get, text

URL = "https://releases.ubuntu.com/"


class UbuntuProvider(Provider):
    async def latest(self) -> Release:
        body = text(await get(URL))

        versions = set(
            re.findall(
                r"\b(2[0-9]\.(?:04|10)(?:\.[0-9]+)?)\b",
                body
            )
        )

        if not versions:
            raise RuntimeError("Could not parse Ubuntu releases")

        def version_key(version: str):
            return tuple(int(x) for x in version.split("."))

        latest = max(versions, key=version_key)

        return Release(
            slug="ubuntu",
            name="Ubuntu",
            version=latest,
            release_date=None,
            source_url=URL
        )