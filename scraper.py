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
        This is the main scraping function. It's a generator that yields
        live log messages as it works. It now includes the "Smart Shield"
        to prevent navigation from being aborted by aggressive pop-ups.
        """
        start_time = time.time()
        
        def log_message(message):
            """Helper function to format log messages with a timestamp."""
            elapsed_time = f"[{time.time() - start_time:.2f}s]"
            return f"{elapsed_time} {message}"

        # --- Main Playwright Logic ---
        async with async_playwright() as p:
            yield log_message("▶️ Initiating 'Smart Shield' Protocol...")
            browser, context, page = None, None, None
            
            # --- Stage 1: Connect and Deploy Smart Shield ---
            try:
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                
                yield log_message("💣 Engaging SMART SHIELD...")
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
                )
                
                # #################################################
                # ##### THE SMART SHIELD LOGIC! #####
                # #################################################
                # This function will handle any new page that tries to open.
                def handle_popup(new_page):
                    # We only close pages that have a real URL. `about:blank` is
                    # often used as a placeholder before a real navigation, and closing it
                    # can abort the main page's navigation.
                    if new_page.url != "about:blank":
                        # This print will appear in your Render server logs for debugging.
                        print(f"SMART SHIELD: Blocking and closing pop-up -> {new_page.url}")
                        # We must not `await` this, so it runs in the background
                        # without blocking our main script.
                        asyncio.create_task(new_page.close())
                    else:
                        print("SMART SHIELD: Ignoring harmless 'about:blank' page.")

                context.on("page", handle_popup)
                yield log_message("✅ Smart Shield engaged and listening for pop-ups.")

                page = await context.new_page()
                yield log_message("✅ Connection successful!")

            except Exception as e:
                yield log_message(f"❌ CRITICAL CONNECTION ERROR: Could not connect or set up context. Error: {e}")
                raise

            # --- Stage 2: Scrape the Page with Protection ---
            try:
                yield log_message(f"🌐 Navigating to main page with shield active...")
                # Using 'domcontentloaded' is safer for ad-heavy pages.
                # It waits for the main HTML to be ready, not for every single ad to finish loading.
                await page.goto(movie_url, wait_until="domcontentloaded", timeout=60000)
                yield log_message(f"✅ Navigation successful! Page title: '{await page.title()}'")
                
                # --- Optional "Watch" button click ---
                watch_button_selector = "h3 > a:has-text('Watch')"
                try:
                    yield log_message("🎯 Searching for an optional 'Watch' button...")
                    watch_button = page.locator(watch_button_selector).first
                    await watch_button.wait_for(state="visible", timeout=10000)
                    yield log_message("👍 'Watch' button found! Clicking it to ensure player is visible...")
                    await watch_button.click()
                    await asyncio.sleep(5)
                except Exception:
                     yield log_message("⚠️ 'Watch' button not found. Proceeding as if player is already visible.")

                # --- Iframe Interaction ---
                yield log_message("🕵️‍♂️ Searching for the player iframe...")
                iframe_selector = "#IndStreamPlayer iframe"
                player_frame = page.frame_locator(iframe_selector)

                await player_frame.locator("body").wait_for(state="visible", timeout=45000)
                yield log_message("👍 Found the iframe and it has loaded!")

                yield log_message("🎯 Performing a click INSIDE the iframe to start the video...")
                await player_frame.locator("body").click(timeout=20000)
                yield log_message("🖱️ Click inside iframe sent! Waiting for the video tag to be created...")
                await asyncio.sleep(10) # Crucial wait time for the player to initialize

                # --- Final Asset Extraction ---
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
                raise
            finally:
                # --- Cleanup ---
                yield log_message("🚪 Closing browser session...")
                if context:
                    await context.close()
                if browser:
                    await browser.close()
                yield "--- MISSION COMPLETE ---"
