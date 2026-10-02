import re
from .base import Provider, Release
from .http import get
from .html import tables

URL = "https://wiki.almalinux.org/release-notes/"


class AlmaLinuxProvider(Provider):
    async def latest(self) -> Release:
        html = await get(URL)
        candidates: list[tuple[tuple[int, int], str, str | None]] = []

        for rows in tables(html):
            for row in rows[1:]:
                if not row:
                    continue
                version = row[0].strip()
                match = re.fullmatch(r"(\d+)\.(\d+)", version)
                if not match:
                    continue
                # Ignore Beta/RC rows; only accept rows with a release date.
                row_text = " | ".join(row)
                if "Beta" in row_text or "RC" in row_text:
                    continue
                release_date = None
                for cell in row:
                    date = re.search(r"\b(\d{1,2} [A-Z][a-z]{2} \d{4})\b", cell)
                    if date:
                        release_date = date.group(1)
                        break
                candidates.append(((int(match.group(1)), int(match.group(2))), version, release_date))

        if not candidates:
            raise RuntimeError("Could not parse AlmaLinux stable releases")

        _, version, release_date = max(candidates, key=lambda item: item[0])
        return Release("almalinux", "AlmaLinux", version, release_date, URL)
