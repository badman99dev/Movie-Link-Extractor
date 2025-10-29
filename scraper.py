import asyncio
from playwright.async_api import async_playwright
import os
import time

BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")
if not BROWSERLESS_API_KEY:
    raise ValueError("FATAL: BROWSERLESS_API_KEY environment variable not set!")
    
BROWSERLESS_ENDPOINT = f'wss://production-sfo.browserless.io?token={BROWSERLESS_API_KEY}'

class VegamoviesScraper: # Naam change kar diya clarity ke liye
    
    async def stream_movie_link_extraction(self, movie_url: str):
        start_time = time.time()

        def log_message(message):
            elapsed_time = f"[{time.time() - start_time:.2f}s]"
            return f"{elapsed_time} {message}"

        async with async_playwright() as p:
            yield log_message("▶️ Connecting to Browserless.io via Playwright...")
            try:
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
                context.set_default_navigation_timeout(90000)
                context.set_default_timeout(60000)
                page = await context.new_page()
                yield log_message("✅ Connection successful! Browser session is live.")
            except Exception as e:
                yield log_message(f"❌ CRITICAL ERROR: Failed to connect to Browserless.io. Error: {e}")
                raise

            try:
                yield log_message(f"🌐 Navigating to the Vegamovies page: {movie_url}")
                await page.goto(movie_url, wait_until="domcontentloaded")
                yield log_message(f"✅ Page navigation complete. Page title: '{await page.title()}'")

                yield log_message("⏳ Searching for the video player iframe...")
                iframe_selector = "#IndStreamPlayer iframe"
                iframe = page.frame_locator(iframe_selector)
                
                if not await iframe.locator('body').is_visible(timeout=30000):
                     raise Exception("Could not find or load the iframe within 30 seconds.")
                
                yield log_message("👍 Found the iframe. Now searching for the <video> tag inside it...")

                video_selector = "video"
                video_tag = iframe.locator(video_selector)
                
                await video_tag.wait_for(state="attached", timeout=30000)
                yield log_message("👍 Found the <video> tag. Extracting the 'src' attribute...")

                direct_link = await video_tag.get_attribute("src")

                if not direct_link:
                    raise Exception("Video tag found, but it has no 'src' attribute.")
                
                yield log_message(f"✨ BINGO! Direct link found!")
                # Link ko ek special format me yield karenge taaki app.py use pehchaan le
                yield f"--LINK--{direct_link}"

            except Exception as e:
                yield log_message(f"❌ SCRAPING ERROR: An error occurred. Error: {e}")
                raise
            finally:
                yield log_message("🚪 Closing browser connection...")
                await browser.close()
                yield log_message("✅ Connection closed.")
