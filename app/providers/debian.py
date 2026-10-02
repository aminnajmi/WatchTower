import re
from .base import Provider, Release
from .http import get, text

URL = "https://www.debian.org/releases/"


class DebianProvider(Provider):
    async def latest(self) -> Release:
        body = text(await get(URL))
        # Example: "current stable ... version 13 ... latest update, version 13.7".
        matches = re.findall(r"latest update,?\s*version\s+(\d+(?:\.\d+)?)", body, re.I)
        if matches:
            latest = max(matches, key=lambda v: tuple(map(int, v.split("."))))
            return Release("debian", "Debian", latest, None, URL)

        match = re.search(r"current\s+stable.*?version\s+(\d+(?:\.\d+)?)", body, re.I | re.S)
        if not match:
            raise RuntimeError("Could not parse Debian stable release")
        return Release("debian", "Debian", match.group(1), None, URL)
