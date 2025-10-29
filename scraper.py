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
        
        async def yield_html_snapshot(page, description):
            """Helper to send live HTML snapshots."""
            yield log_message(f"🔄 Syncing HTML: {description}")
            try:
                html_content = await page.content()
                yield f"--HTML-SNAPSHOT--{html_content.replace(chr(10), '').replace(chr(13), '')}"
            except Exception as e:
                yield log_message(f"⚠️ Could not sync HTML: {e}")

        async with async_playwright() as p:
            yield log_message("▶️ Initiating 'JS Injection' Protocol...")
            browser, context, page = None, None, None
            try:
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                context = await browser.new_context(viewport={'width': 1280, 'height': 800})
                
                # We keep the pop-up blocker, it doesn't hurt.
                def handle_popup(new_page):
                    if new_page.url != "about:blank":
                        print(f"POP-UP BLOCKER: Closing {new_page.url}")
                        asyncio.create_task(new_page.close())
                context.on("page", handle_popup)
                
                page = await context.new_page()
                yield log_message("✅ Connection successful!")
            except Exception as e:
                yield log_message(f"❌ Connection failed: {e}")
                raise

            try:
                yield log_message(f"🌐 Navigating to main page...")
                await page.goto(movie_url, wait_until="domcontentloaded")
                yield log_message(f"✅ Page loaded. Title: '{await page.title()}'")
                async for log in yield_html_snapshot(page, "After page load"): yield log

                yield log_message("🕵️‍♂️ Searching for the player iframe...")
                iframe_selector = "#IndStreamPlayer iframe"
                iframe_element = page.locator(iframe_selector).first # Use .first to get the element handle

                await iframe_element.wait_for(state="visible", timeout=45000)
                yield log_message("👍 Found the iframe!")
                async for log in yield_html_snapshot(page, "After finding iframe"): yield log

                # #################################################
                # ##### JAVASCRIPT INJECTION ATTACK! #####
                # #################################################
                yield log_message("💉 Preparing to inject JavaScript for a forced click...")
                
                # Get the handle to the iframe's content
                frame = await iframe_element.content_frame()
                if not frame:
                    raise Exception("Could not get the content frame of the iframe.")
                
                # Inject and execute JavaScript inside the iframe
                await frame.evaluate("() => { document.body.click(); }")
                yield log_message("💥 JS INJECTED! Forced click command sent to the iframe's body.")
                
                yield log_message("⏳ Waiting 10 seconds for the video to initialize post-injection...")
                await asyncio.sleep(10)
                async for log in yield_html_snapshot(page, "After JS injection click"): yield log

                yield log_message("🎬 Searching for <video> tag INSIDE iframe...")
                # We still use the frame_locator to find the video tag
                video_tag = page.frame_locator(iframe_selector).locator("video")
                
                await video_tag.wait_for(state="attached", timeout=45000)
                yield log_message("👍 Found the <video> tag!")

                direct_link = await video_tag.get_attribute("src")
                if not direct_link:
                    raise Exception("Video tag found, but no 'src' attribute.")
                
                yield log_message(f"✨ MISSION ACCOMPLISHED! Link Found!")
                yield f"--LINK--{direct_link}"

            except Exception as e:
                error_message = str(e).split('Call log:')[0].strip()
                yield log_message(f"❌ MISSION FAILED: {error_message}")
                if page and not page.is_closed():
                    async for log in yield_html_snapshot(page, "At the moment of failure"): yield log
                raise
            finally:
                yield log_message("🚪 Closing browser session...")
                if context: await context.close()
                if browser: await browser.close()
                yield "--- MISSION COMPLETE ---"
