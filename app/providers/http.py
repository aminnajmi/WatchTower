import httpx
from bs4 import BeautifulSoup
from ..config import settings


async def get(url: str) -> str:
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, follow_redirects=True, headers={"User-Agent": "OS-Release-Tracker/1.0"}) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


def text(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
