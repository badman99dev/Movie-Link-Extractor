import asyncio
from playwright.async_api import async_playwright
import os
import time
import json

BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")
if not BROWSERLESS_API_KEY:
    raise ValueError("FATAL: BROWSERLESS_API_KEY environment variable not set!")
    
BROWSERLESS_ENDPOINT = f'wss://production-sfo.browserless.io?token={BROWSERLESS_API_KEY}'

class VegamoviesScraper:
    
    async def stream_movie_link_extraction(self, movie_url: str):
        start_time = time.time()
        network_log = [] # Saare network events yahan record honge

        def log_message(message):
            elapsed_time = f"[{time.time() - start_time:.2f}s]"
            return f"{elapsed_time} {message}"
        
        async def handle_response(response):
            # Har network response ko log karo
            try:
                request = response.request
                network_log.append({
                    "url": response.url,
                    "method": request.method,
                    "status": response.status,
                    "resource_type": request.resource_type,
                })
            except Exception:
                pass # Kuch requests fail ho sakti hain, unhe ignore karo

        async with async_playwright() as p:
            yield log_message("▶️ Initiating Full Surveillance...")
            browser, page = None, None
            try:
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                context = await browser.new_context(viewport={'width': 1280, 'height': 720})
                context.set_default_timeout(60000)
                page = await context.new_page()

                # Network monitoring shuru karo
                page.on("response", handle_response)
                yield log_message("✅ Connection successful! Network monitor is ACTIVE.")
            except Exception as e:
                yield log_message(f"❌ Connection failed: {e}")
                raise

            try:
                # ... (baaki ka scraping logic bilkul waisa hi rahega) ...
                yield log_message(f"🌐 Navigating to page...")
                await page.goto(movie_url, wait_until="load")
                yield log_message(f"✅ Page loaded.")
                
                html_content = await page.content()
                yield f"--HTML-SNAPSHOT--{html_content.replace(chr(10), '').replace(chr(13), '')}"

                iframe_selector = "#IndStreamPlayer iframe"
                iframe_element = page.locator(iframe_selector)
                await iframe_element.wait_for(state="visible", timeout=30000)
                await iframe_element.scroll_into_view_if_needed()
                yield log_message("👍 Found iframe.")

                await iframe_element.click(timeout=15000)
                yield log_message("🖱️ Clicked! Waiting...")
                
                for i in range(5):
                    await asyncio.sleep(2)
                    html_content = await page.content()
                    yield f"--HTML-SNAPSHOT--{html_content.replace(chr(10), '').replace(chr(13), '')}"
                
                iframe = page.frame_locator(iframe_selector)
                video_tag = iframe.locator("video")
                await video_tag.wait_for(state="attached", timeout=30000)
                direct_link = await video_tag.get_attribute("src")

                if not direct_link:
                    raise Exception("Video tag found, but no 'src' attribute.")
                
                yield log_message(f"✨ MISSION ACCOMPLISHED!")
                yield f"--LINK--{direct_link}"

            except Exception as e:
                error_message = str(e).split('Call log:')[0].strip()
                yield log_message(f"❌ FAILED: {error_message}")
                html_content = await page.content()
                yield f"--HTML-SNAPSHOT--{html_content.replace(chr(10), '').replace(chr(13), '')}"
                raise
            finally:
                # Network log ko JSON me convert karke bhejo
                yield log_message("📦 Compiling final network report...")
                yield f"--NETWORK-LOG--{json.dumps(network_log, indent=2)}"

                yield log_message("🚪 Closing browser session...")
                if browser:
                    page.remove_listener("response", handle_response)
                    await browser.close()
