import asyncio
from playwright.async_api import async_playwright
import os
import time
import base64 # Screenshot ko encode karne ke liye

BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")
if not BROWSERLESS_API_KEY:
    raise ValueError("FATAL: BROWSERLESS_API_KEY environment variable not set!")
    
BROWSERLESS_ENDPOINT = f'wss://production-sfo.browserless.io?token={BROWSERLESS_API_KEY}'

class VegamoviesScraper:
    
    async def stream_movie_link_extraction(self, movie_url: str):
        start_time = time.time()
        
        def log_message(message):
            elapsed_time = f"[{time.time() - start_time:.2f}s]"
            return f"{elapsed_time} {message}"

        async with async_playwright() as p:
            yield log_message("▶️ Connecting to Browserless.io...")
            page = None # page ko bahar define kiya taaki finally block me use kar sakein
            try:
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                                                    viewport={'width': 1280, 'height': 720}) # Set a viewport for consistent screenshots
                context.set_default_timeout(90000)
                page = await context.new_page()
                yield log_message("✅ Connection successful!")
            except Exception as e:
                yield log_message(f"❌ CRITICAL ERROR: Connection failed. Error: {e}")
                raise

            try:
                yield log_message(f"🌐 Navigating to Vegamovies page...")
                await page.goto(movie_url, wait_until="domcontentloaded")
                yield log_message(f"✅ Page navigation complete. Title: '{await page.title()}'")
                
                # --- Intelligence Gathering Step ---
                yield log_message("📸 Taking a pre-action screenshot of the whole page...")
                screenshot_bytes = await page.screenshot(full_page=True)
                base64_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
                yield f"--SCREENSHOT--data:image/png;base64,{base64_screenshot}"

                yield log_message("⏳ Searching for the video player iframe...")
                iframe_selector = "#IndStreamPlayer iframe"
                iframe_element = page.locator(iframe_selector)
                
                await iframe_element.wait_for(state="visible", timeout=30000)
                yield log_message("👍 Found iframe.")
                
                yield log_message("🎬 Searching for the <video> tag now...")
                iframe = page.frame_locator(iframe_selector)
                video_selector = "video"
                video_tag = iframe.locator(video_selector)
                
                await video_tag.wait_for(state="attached", timeout=60000)
                yield log_message("👍 Found <video> tag. Extracting 'src' attribute...")
                
                direct_link = await video_tag.get_attribute("src")

                if not direct_link:
                    raise Exception("Video tag found, but no 'src' attribute.")
                
                yield log_message(f"✨ MISSION ACCOMPLISHED! Link Found!")
                yield f"--LINK--{direct_link}"

            except Exception as e:
                error_message = str(e).split('Call log:')[0].strip()
                yield log_message(f"❌ SCRAPING FAILED: {error_message}")
                
                # --- X-Ray Vision and Spy Cam on Failure ---
                yield log_message("🕵️‍♂️ GATHERING INTELLIGENCE ON FAILURE...")
                try:
                    # Spy Cam: Take a screenshot
                    yield log_message("📸 Taking a screenshot at the moment of failure...")
                    screenshot_bytes = await page.screenshot(full_page=True)
                    base64_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
                    yield f"--SCREENSHOT--data:image/png;base64,{base64_screenshot}"
                    
                    # X-Ray Vision: Get the full HTML
                    yield log_message("📄 Getting the full page HTML source code...")
                    full_html = await page.content()
                    yield f"--HTML--{full_html}" # Send the full HTML
                except Exception as ie:
                    yield log_message(f"🕵️‍♂️ Could not gather intelligence. Error: {ie}")
                raise
            finally:
                yield log_message("🚪 Closing browser session...")
                if page and not page.is_closed():
                    await page.context.close()
                elif page and page.context and not page.context.is_closed():
                     await page.context.close()
