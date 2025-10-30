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
        
        def log_message(message):
            elapsed_time = f"[{time.time() - start_time:.2f}s]"
            return f"{elapsed_time} {message}"
        
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
                log_queue = []
                
                async def add_log_to_queue(message):
                    log_queue.append(message)

                mission_task = asyncio.create_task(mission_function(page, add_log_to_queue))

                # #################################################
                # ##### THE RACE CONDITION FIX! #####
                # #################################################
                # Wait for the VERY FIRST navigation to complete before we start
                # our snapshot loop. This ensures the page is in a stable state.
                yield log_message("⏳ Waiting for initial page navigation to complete...")
                await page.wait_for_load_state("load", timeout=60000)
                yield log_message("✅ Initial page is stable. Starting live sync.")
                # #################################################

                while not mission_task.done():
                    while log_queue:
                        yield log_message(log_queue.pop(0))
                    
                    html_content = await page.content()
                    yield f"--HTML-SNAPSHOT--{html_content.replace(chr(10), '').replace(chr(13), '')}"
                    
                    await asyncio.sleep(1)

                # Process any final logs from the mission
                while log_queue:
                    yield log_message(log_queue.pop(0))

                final_url = await mission_task
                
                yield log_message(f"✨ MISSION ACCOMPLISHED!")
                yield f"--LINK--{final_url}"

            except Exception as e:
                error_message = str(e).split('Call log:')[0].strip()
                yield log_message(f"❌ MISSION FAILED: {error_message}")
                # Don't try to get content here, as the page might still be unstable
                raise
            finally:
                yield log_message("🚪 Shutting down engine...")
                if context: await context.close()
                if browser: await browser.close()
                yield "--- MISSION COMPLETE ---"
