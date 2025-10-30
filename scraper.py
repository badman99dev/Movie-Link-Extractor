import asyncio
from playwright.async_api import async_playwright
import os
import time

BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")
if not BROWSERLESS_API_KEY:
    raise ValueError("FATAL: BROWSERLESS_API_KEY environment variable not set!")
    
BROWSERLESS_ENDPOINT = f'wss://production-sfo.browserless.io?token={BROWSERLESS_API_KEY}'

class ScraperEngine:
    
    async def run_mission(self, mission_function):
        start_time = time.time()
        
        # Helper functions are now part of the engine
        def log_message(message):
            elapsed_time = f"[{time.time() - start_time:.2f}s]"
            return f"{elapsed_time} {message}"
        
        async def yield_html_snapshot(page, description):
            yield log_message(f"🔄 Syncing HTML: {description}")
            html_content = await page.content()
            yield f"--HTML-SNAPSHOT--{html_content.replace(chr(10), '').replace(chr(13), '')}"

        async with async_playwright() as p:
            yield log_message("▶️ Scraper Engine Initializing...")
            browser, context, page = None, None, None
            try:
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                context = await browser.new_context(viewport={'width': 1280, 'height': 800})
                page = await context.new_page()
                yield log_message("✅ Engine Online. Handing over control to mission plan...")
            except Exception as e:
                yield log_message(f"❌ Engine Failure: {e}")
                raise

            try:
                # This is the magic. The engine calls the mission function we pass to it.
                # It provides the `page` object and a way to send logs back.
                async def send_log(message):
                    yield log_message(message)
                    # Every time the mission sends a log, we also send an HTML snapshot.
                    async for log in yield_html_snapshot(page, "Live Update"): yield log

                final_url = await mission_function(page, send_log)
                
                yield log_message(f"✨ MISSION ACCOMPLISHED!")
                yield f"--LINK--{final_url}"

            except Exception as e:
                error_message = str(e).split('Call log:')[0].strip()
                yield log_message(f"❌ MISSION FAILED: {error_message}")
                if page and not page.is_closed():
                    async for log in yield_html_snapshot(page, "At the moment of failure"): yield log
                raise
            finally:
                yield log_message("🚪 Shutting down engine...")
                if context: await context.close()
                if browser: await browser.close()
                yield "--- MISSION COMPLETE ---"
