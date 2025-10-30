
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
            yield log_message("▶️ Scraper Engine Initializing (v3 - Stable)...")
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
                
                # Helper function to send logs
                async def send_log(message):
                    yield log_message(message)
                
                # Helper function to send HTML
                async def send_html_snapshot(description):
                    yield log_message(f"🔄 Syncing HTML: {description}")
                    try:
                        html_content = await page.content()
                        yield f"--HTML-SNAPSHOT--{html_content.replace(chr(10), '').replace(chr(13), '')}"
                    except Exception as e:
                        yield log_message(f"⚠️ Could not sync HTML: {e}")

                # The engine now directly awaits the mission generator.
                # The mission itself is now in full control of logging and snapshots.
                async for log_entry in mission_function(page, send_log, send_html_snapshot):
                    yield log_entry

                # The mission will return the final URL at the end
                final_url = page.url # Get the final url after the generator is done
                
                yield log_message(f"✨ MISSION ACCOMPLISHED!")
                yield f"--LINK--{final_url}"

            except Exception as e:
                error_message = str(e).split('Call log:')[0].strip()
                yield log_message(f"❌ MISSION FAILED: {error_message}")
                raise
            finally:
                yield log_message("🚪 Shutting down engine...")
                if context: await context.close()
                if browser: await browser.close()
                yield "--- MISSION COMPLETE ---"
