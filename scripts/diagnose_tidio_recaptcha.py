"""Check reCAPTCHA loading in a fresh Playwright context without signing in."""

from __future__ import annotations

import asyncio
import logging

from playwright.async_api import async_playwright

from app.tidio import TIDIO_INBOX_URL, TidioMonitor


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    monitor = TidioMonitor()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False,
            ignore_default_args=["--disable-dev-shm-usage"],
        )
        try:
            context = await browser.new_context(
                viewport={"width": 1440, "height": 1000},
                locale="en-US",
                java_script_enabled=True,
                ignore_https_errors=False,
            )
            try:
                page = await context.new_page()
                monitor._context = context
                monitor._page = page
                monitor._diagnose_page(page)
                response = await page.goto(
                    TIDIO_INBOX_URL,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )
                logging.getLogger("app.tidio.diagnostic").info(
                    "Fresh context navigation complete http_status=%s path=%s",
                    response.status if response else "unknown",
                    monitor._safe_location(page.url),
                )
                await page.wait_for_timeout(5_000)
                await monitor._log_login_phase(
                    "fresh_context_after_load",
                    response.status if response else None,
                )
                await monitor._log_recaptcha_diagnostics(
                    "fresh_context_after_load",
                    wait_for_ready=True,
                )
            finally:
                await context.close()
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
