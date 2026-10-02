import httpx
from ..config import settings


async def send(message: str) -> None:
    if not settings.discord_webhook_url:
        return
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(settings.discord_webhook_url, json={"content": message})
        r.raise_for_status()
