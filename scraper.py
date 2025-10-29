import asyncio
from playwright.async_api import async_playwright
import os
import time

BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")
if not BROWSERLESS_API_KEY:
    raise ValueError("FATAL: BROWSERLESS_API_KEY environment variable not set!")
    
BROWSERLESS_ENDPOINT = f'wss://production-sfo.browserless.io?token={BROWSERLESS_API_KEY}'

class VegamoviesScraper:
    
    async def stream_movie_link_extraction(self, movie_url: str):
        start_time = time.time()
        
        # --- Helper Functions ---
        def log_message(message):
            elapsed_time = f"[{time.time() - start_time:.2f}s]"
            return f"{elapsed_time} {message}"
        
        async def yield_html_snapshot(page, description):
            yield log_message(f"🔄 Syncing HTML: {description}")
            html_content = await page.content()
            yield f"--HTML-SNAPSHOT--{html_content.replace(chr(10), '').replace(chr(13), '')}"

        # --- Main Logic ---
        async with async_playwright() as p:
            yield log_message("▶️ Initiating Ultimate Mission...")
            browser, page = None, None
            try:
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                context = await browser.new_context(viewport={'width': 1280, 'height': 800})
                context.set_default_timeout(60000)
                page = await context.new_page()
                yield log_message("✅ Connection successful!")
            except Exception as e:
                yield log_message(f"❌ Connection failed: {e}")
                raise

            try:
                # --- Step 1: Navigate to the main movie page ---
                yield log_message(f"🌐 Navigating to main page...")
                await page.goto(movie_url, wait_until="load")
                yield log_message(f"✅ Main page loaded.")
                async for log in yield_html_snapshot(page, "After main page load"): yield log

                # --- Step 2: Click the "Watch" button to reveal the player ---
                watch_button_selector = "h3 > a:has-text('Watch')"
                try:
                    yield log_message("🎯 Searching for the 'Watch' button...")
                    watch_button = page.locator(watch_button_selector).first
                    await watch_button.wait_for(state="visible", timeout=15000)
                    yield log_message("👍 'Watch' button found! Clicking it...")
                    await watch_button.click()
                    yield log_message("🖱️ Clicked! Waiting for player to render...")
                    await asyncio.sleep(5)
                    async for log in yield_html_snapshot(page, "After clicking 'Watch' button"): yield log
                except Exception:
                     yield log_message("⚠️ 'Watch' button not found, assuming player is already on page.")

                # --- Step 3: Locate the iframe and click inside it ---
                yield log_message("🕵️‍♂️ Searching for the revealed iframe...")
                iframe_selector = "#IndStreamPlayer iframe"
                
                player_frame = page.frame_locator(iframe_selector)

                await player_frame.locator("body").wait_for(state="visible", timeout=45000)
                yield log_message("👍 Found the iframe and it's loaded!")
                async for log in yield_html_snapshot(page, "After iframe is loaded"): yield log

                yield log_message("🎯 Performing a click INSIDE the iframe to start the video...")
                await player_frame.locator("body").click(timeout=20000)
                yield log_message("🖱️ Click inside iframe successful! Waiting for video tag to be created...")
                
                # Continuously sync HTML after click to see the changes
                for i in range(5):
                    await asyncio.sleep(2)
                    async for log in yield_html_snapshot(page, f"Sync #{i+1} post-click"): yield log

                # --- Step 4: Find the final video tag and extract the link ---
                yield log_message("🎬 Now searching for the final <video> tag INSIDE the iframe...")
                video_tag = player_frame.locator("video")
                
                await video_tag.wait_for(state="attached", timeout=45000)
                yield log_message("👍 Found the <video> tag!")

                direct_link = await video_tag.get_attribute("src")

                if not direct_link:
                    raise Exception("Video tag found, but no 'src' attribute.")
                
                yield log_message(f"✨ MISSION ACCOMPLISHED! Link Found!")
                yield f"--LINK--{direct_link}"

            except Exception as e:
                error_message = str(e).split('Call log:')[0].strip()
                yield log_message(f"❌ FAILED: {error_message}")
                if page and not page.is_closed():
                    async for log in yield_html_snapshot(page, "At the moment of failure"): yield log
                raise
            finally:
                yield log_message("🚪 Closing browser session...")
                if browser:
                    await browser.close()
                yield "--- MISSION COMPLETE ---"
