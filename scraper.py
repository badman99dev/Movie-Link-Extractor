import asyncio
from playwright.async_api import async_playwright
import os
import time

# --- Configuration ---
BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")
if not BROWSERLESS_API_KEY:
    raise ValueError("FATAL: BROWSERLESS_API_KEY environment variable not set!")
    
BROWSERLESS_ENDPOINT = f'wss://production-sfo.browserless.io?token={BROWSERLESS_API_KEY}'

class VegamoviesScraper:
    
    async def stream_movie_link_extraction(self, movie_url: str):
        """
        This is the main function that performs the scraping. It's a generator that yields
        live log messages as it works.
        """
        start_time = time.time()
        
        def log_message(message):
            """Helper function to format log messages with a timestamp."""
            elapsed_time = f"[{time.time() - start_time:.2f}s]"
            return f"{elapsed_time} {message}"

        # --- Main Playwright Logic ---
        async with async_playwright() as p:
            yield log_message("▶️ Initiating Final Strategy: Anti-Redirect + Iframe Interaction...")
            browser, context, page = None, None, None
            
            # --- Stage 1: Connect and Disarm Traps ---
            try:
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                
                yield log_message("💣 DISARMING POP-UP TRAPS...")
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
                )
                
                # THE SHIELD: This is the most critical part. It blocks all new tabs/pop-ups.
                context.on("page", lambda new_page: new_page.close())
                yield log_message("✅ Pop-up blocker engaged. New pages will be closed instantly.")

                page = await context.new_page()
                yield log_message("✅ Connection successful!")

            except Exception as e:
                yield log_message(f"❌ CRITICAL CONNECTION ERROR: Could not connect to Browserless or set up context. Error: {e}")
                raise

            # --- Stage 2: Scrape the Page ---
            try:
                yield log_message(f"🌐 Navigating to main page...")
                await page.goto(movie_url, wait_until="load", timeout=60000)
                yield log_message(f"✅ Main page loaded. Title: '{await page.title()}'")

                # --- Step 2a (Optional but good): Try to click the "Watch" button ---
                watch_button_selector = "h3 > a:has-text('Watch')"
                try:
                    yield log_message("🎯 Searching for a 'Watch' button to reveal the player...")
                    watch_button = page.locator(watch_button_selector).first
                    await watch_button.wait_for(state="visible", timeout=10000) # Short wait
                    yield log_message("👍 'Watch' button found! Clicking it...")
                    await watch_button.click()
                    yield log_message("🖱️ Clicked 'Watch' button! Waiting for player to render...")
                    await asyncio.sleep(5)
                except Exception:
                     yield log_message("⚠️ 'Watch' button not found or not needed. Proceeding...")

                # --- Step 3: Locate the iframe and interact with it ---
                yield log_message("🕵️‍♂️ Searching for the player iframe...")
                iframe_selector = "#IndStreamPlayer iframe"
                player_frame = page.frame_locator(iframe_selector)

                await player_frame.locator("body").wait_for(state="visible", timeout=45000)
                yield log_message("👍 Found the iframe and it has loaded successfully!")

                yield log_message("🎯 Performing a click INSIDE the iframe to start the video...")
                # Our pop-up shield should protect this click.
                await player_frame.locator("body").click(timeout=20000)
                yield log_message("🖱️ Click inside iframe sent! Waiting for video tag to be created...")
                await asyncio.sleep(10) # Give it 10 seconds to create the video element

                # --- Step 4: Find the video link ---
                yield log_message("🎬 Now searching for the final <video> tag INSIDE the iframe...")
                video_tag = player_frame.locator("video")
                
                await video_tag.wait_for(state="attached", timeout=45000)
                yield log_message("👍 Found the <video> tag!")

                direct_link = await video_tag.get_attribute("src")

                if not direct_link:
                    raise Exception("Video tag found, but it has no 'src' attribute.")
                
                yield log_message(f"✨ MISSION ACCOMPLISHED! Link Found!")
                yield f"--LINK--{direct_link}"

            except Exception as e:
                error_message = str(e).split('Call log:')[0].strip()
                yield log_message(f"❌ MISSION FAILED: {error_message}")
                # Optional: Add a screenshot on failure here if you want
                # screenshot_bytes = await page.screenshot()
                # base64_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
                # yield f"--SCREENSHOT--data:image/png;base64,{base64_screenshot}"
                raise
            finally:
                # --- Stage 5: Cleanup ---
                yield log_message("🚪 Closing browser session...")
                if context:
                    await context.close()
                if browser:
                    await browser.close()
                yield "--- MISSION COMPLETE ---"
