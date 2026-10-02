import re
from .base import Provider, Release
from .http import get
from .html import tables

URL = "https://docs.rockylinux.org/latest/releases/"


class RockyLinuxProvider(Provider):
    async def latest(self) -> Release:
        html = await get(URL)
        candidates: list[tuple[tuple[int, int], str, str | None]] = []

        for rows in tables(html):
            for row in rows[1:]:
                if not row:
                    continue
                # Current supported releases table has the latest minor version in the last column.
                for cell in reversed(row):
                    match = re.fullmatch(r"(\d+)\.(\d+)(?:\s*\([^)]*\))?", cell.strip())
                    if match:
                        version = f"{match.group(1)}.{match.group(2)}"
                        release_date = None
                        for value in row:
                            date = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", value)
                            if date:
                                release_date = date.group(1)
                                break
                        candidates.append(((int(match.group(1)), int(match.group(2))), version, release_date))
                        break

        if not candidates:
            raise RuntimeError("Could not parse Rocky Linux stable releases")

        _, version, release_date = max(candidates, key=lambda item: item[0])
        return Release("rockylinux", "Rocky Linux", version, release_date, URL)
