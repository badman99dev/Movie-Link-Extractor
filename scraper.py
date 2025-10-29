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
        
        def log_message(message):
            elapsed_time = f"[{time.time() - start_time:.2f}s]"
            return f"{elapsed_time} {message}"

        async with async_playwright() as p:
            yield log_message("▶️ Connecting to Browserless.io...")
            try:
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
                # Increase default timeout to 90 seconds to be safe
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

                yield log_message("⏳ Searching for the video player iframe...")
                iframe_selector = "#IndStreamPlayer iframe"
                # Locate the iframe itself, not just the frame locator
                iframe_element = page.locator(iframe_selector)
                
                await iframe_element.wait_for(state="visible", timeout=30000)
                yield log_message("👍 Found iframe.")

                # #################################################
                # ##### THE BRUTE FORCE CLICK! 💣 #####
                # #################################################
                yield log_message("🎯 Executing BRUTE FORCE CLICK on the center of the player...")
                try:
                    # We click the iframe element directly. This simulates a user click.
                    await iframe_element.click(timeout=15000)
                    yield log_message("🖱️ Click successful! Giving the player 10 seconds to wake up and load the video stream...")
                    await asyncio.sleep(10) # Wait for the video to initialize after click
                except Exception as click_error:
                    yield log_message(f"⚠️ Could not perform the click, but continuing anyway. Error: {click_error}")

                # Now that we've clicked, the <video> tag should exist.
                # We need to switch to the frame's content to find elements inside it.
                iframe = page.frame_locator(iframe_selector)
                yield log_message("🎬 Searching for the <video> tag post-click...")
                video_selector = "video"
                video_tag = iframe.locator(video_selector)
                
                # Now, wait for the video tag to have a 'src'
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
                # For better debugging, let's get the iframe's HTML on failure
                try:
                    iframe_content = await page.frame_locator(iframe_selector).locator('body').inner_html(timeout=5000)
                    yield log_message(f"🕵️‍♂️ IFRAME CONTENT ON FAILURE (first 500 chars):\n{iframe_content[:500]}")
                except Exception as ie:
                    yield log_message(f"🕵️‍♂️ Could not get iframe content on failure. Error: {ie}")
                raise
            finally:
                yield log_message("🚪 Closing browser session...")
                await browser.close()
                yield log_message("✅ Connection closed.")
