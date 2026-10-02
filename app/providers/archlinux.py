import re
from .base import Provider, Release
from .http import get, text

URL = "https://archlinux.org/releng/releases/"


class ArchLinuxProvider(Provider):
    async def latest(self) -> Release:
        body = text(await get(URL))
        versions = re.findall(r"\b(20\d{2}\.\d{2}\.\d{2})\b", body)
        if not versions:
            raise RuntimeError("Could not parse Arch Linux ISO releases")
        latest = max(set(versions), key=lambda v: tuple(map(int, v.split("."))))
        return Release("archlinux", "Arch Linux", latest, latest, URL, "rolling", True)
