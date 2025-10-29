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
        # ... (log_message function is the same) ...
        def log_message(message):
            elapsed_time = f"[{time.time() - start_time:.2f}s]"
            return f"{elapsed_time} {message}"

        async with async_playwright() as p:
            yield log_message("▶️ Connecting to Browserless.io via Playwright...")
            try:
                # ... (connection logic is the same) ...
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
                context.set_default_navigation_timeout(90000)
                context.set_default_timeout(60000)
                page = await context.new_page()
                yield log_message("✅ Connection successful!")
            except Exception as e:
                yield log_message(f"❌ CRITICAL ERROR: Connection failed. Error: {e}")
                raise

            try:
                yield log_message(f"🌐 Navigating to Vegamovies page: {movie_url}")
                await page.goto(movie_url, wait_until="domcontentloaded")
                yield log_message(f"✅ Page navigation complete. Title: '{await page.title()}'")

                yield log_message("⏳ Searching for the video player iframe...")
                iframe_selector = "#IndStreamPlayer iframe"
                iframe = page.frame_locator(iframe_selector)
                
                if not await iframe.locator('body').is_visible(timeout=30000):
                     raise Exception("Could not find or load the iframe body.")
                
                yield log_message("👍 Found iframe. Now executing FINAL BATTLE PLAN inside it...")

                # #################################################
                # ##### FINAL BOSS STRATEGY! #####
                # #################################################

                # STRATEGY 1: Play button ko dhoondho aur click karo.
                play_button_selector = ".jw-icon-playback" # Yeh JWPlayer ka common play button hai
                try:
                    yield log_message("🕵️‍♂️ Searching for a Play button inside the iframe...")
                    play_button = iframe.locator(play_button_selector)
                    await play_button.wait_for(state="visible", timeout=15000) # 15s wait
                    yield log_message("🎯 Play button found! Simulating a click to load the video...")
                    await play_button.click()
                    yield log_message("🖱️ Click successful! Giving video 5s to load...")
                    await asyncio.sleep(5) # Click ke baad video ko load hone ka time do
                except Exception:
                    yield log_message("⚠️ Play button not found or not needed. Proceeding to find video tag directly.")
                
                # STRATEGY 2: Ab video tag dhoondho
                yield log_message("🎬 Searching for the <video> tag...")
                video_selector = "video"
                video_tag = iframe.locator(video_selector)
                
                # Iske liye wait time badha dete hain
                await video_tag.wait_for(state="attached", timeout=45000) 
                yield log_message("👍 Found <video> tag. Extracting 'src' attribute...")

                direct_link = await video_tag.get_attribute("src")

                if not direct_link:
                    raise Exception("Video tag found, but no 'src' attribute.")
                
                yield log_message(f"✨ MISSION ACCOMPLISHED! Link Found!")
                yield f"--LINK--{direct_link}"

            except Exception as e:
                error_message = str(e).split('Call log:')[0].strip()
                yield log_message(f"❌ SCRAPING FAILED: {error_message}")
                raise
            finally:
                yield log_message("🚪 Closing browser session...")
                await browser.close()
                yield log_message("✅ Connection closed.")
