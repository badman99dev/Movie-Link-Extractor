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
        
        # Helper function for basic log messages
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
                # #################################################
                # ##### THE CORRECTED LOGIC! #####
                # #################################################

                # We create a simple log queue (a list)
                log_queue = []
                
                # This simple async function will be passed to the mission.
                # It just adds logs to our queue.
                async def add_log_to_queue(message):
                    log_queue.append(message)

                # We start the mission in the background.
                # It will run its steps and add logs to the queue.
                mission_task = asyncio.create_task(mission_function(page, add_log_to_queue))

                # While the mission is running, our main loop will process the queue
                while not mission_task.done():
                    # Send any logs that the mission has generated
                    while log_queue:
                        yield log_message(log_queue.pop(0))
                    
                    # Send an HTML snapshot
                    html_content = await page.content()
                    yield f"--HTML-SNAPSHOT--{html_content.replace(chr(10), '').replace(chr(13), '')}"
                    
                    # Wait a bit before the next update
                    await asyncio.sleep(1) # Controls the "frame rate" of the mirror

                # Get the final result from the completed mission task
                final_url = await mission_task
                
                yield log_message(f"✨ MISSION ACCOMPLISHED!")
                yield f"--LINK--{final_url}"

            except Exception as e:
                error_message = str(e).split('Call log:')[0].strip()
                yield log_message(f"❌ MISSION FAILED: {error_message}")
                if page and not page.is_closed():
                    html_content = await page.content()
                    yield f"--HTML-SNAPSHOT--{html_content.replace(chr(10), '').replace(chr(13), '')}"
                raise
            finally:
                yield log_message("🚪 Shutting down engine...")
                if context: await context.close()
                if browser: await browser.close()
                yield "--- MISSION COMPLETE ---"
