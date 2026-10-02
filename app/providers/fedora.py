import re
from .base import Provider, Release
from .http import get, text

URL = "https://fedoraproject.org/"


class FedoraProvider(Provider):
    async def latest(self) -> Release:
        body = text(await get(URL))
        # The Fedora homepage exposes the current stable release as "Latest ReleaseNN".
        matches = re.findall(r"Latest Release\s*(\d+)", body, re.I)
        if not matches:
            raise RuntimeError("Could not parse Fedora latest stable release")
        latest = max(map(int, matches))
        return Release("fedora", "Fedora", str(latest), None, URL)
