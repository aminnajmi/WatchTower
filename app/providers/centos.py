import re
from .base import Provider, Release
from .http import get, text

URL = "https://mirror.stream.centos.org/10-stream/BaseOS/x86_64/iso/"


class CentOSProvider(Provider):
    async def latest(self) -> Release:
        body = text(await get(URL))
        versions = re.findall(r"CentOS-Stream-(\d+)-(\d{8}\.0)", body)
        if not versions:
            raise RuntimeError("Could not parse CentOS Stream releases")
        latest = max((f"{major}-{stamp}" for major, stamp in versions), key=lambda x: x.split('-')[1])
        return Release("centos", "CentOS Stream", latest, latest.split('-')[1][:8], URL)
