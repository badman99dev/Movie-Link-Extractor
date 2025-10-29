import asyncio
from playwright.async_api import async_playwright
import os
import time

BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")
if not BROWSERLESS_API_KEY:
    raise ValueError("FATAL: BROWSERLESS_API_KEY environment variable not set!")
    
BROWSERLESS_ENDPOINT = f'wss://production-sfo.browserless.io?token={BROWSERLESS_API_KEY}'

class LiveInspector:
    
    async def run_test_mission(self):
        start_time = time.time()
        
        def log_message(message):
            elapsed_time = f"[{time.time() - start_time:.2f}s]"
            return f"{elapsed_time} {message}"
        
        async def yield_html_snapshot(page, description):
            yield log_message(f"🔄 Syncing HTML: {description}")
            html_content = await page.content()
            yield f"--HTML-SNAPSHOT--{html_content.replace(chr(10), '').replace(chr(13), '')}"

        async with async_playwright() as p:
            yield log_message("▶️ Initiating 'Project Source Inspector'...")
            browser, context, page = None, None, None
            try:
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                context = await browser.new_context(viewport={'width': 1280, 'height': 800})
                page = await context.new_page()
                yield log_message("✅ Connection successful!")
            except Exception as e:
                yield log_message(f"❌ Connection failed: {e}")
                raise

            try:
                # --- Step 1: Go to view-page-source.com ---
                target_url = "https://www.view-page-source.com/"
                yield log_message(f"🌐 Navigating to {target_url}...")
                await page.goto(target_url, wait_until="load")
                yield log_message("✅ Homepage loaded.")
                async for log in yield_html_snapshot(page, "On homepage"): yield log
                await asyncio.sleep(3)

                # --- Step 2: Fill the URL input field ---
                # From the source code, the input has id="uri"
                url_input_selector = '#uri'
                yield log_message(f"🎯 Typing 'www.google.com' into input box: {url_input_selector}")
                await page.locator(url_input_selector).fill("www.google.com")
                async for log in yield_html_snapshot(page, "After typing URL"): yield log
                await asyncio.sleep(3)

                # --- Step 3: Click the submit button ---
                # From the source, the button is: <input value="View Source Code" type="submit">
                submit_button_selector = 'input[type="submit"][value="View Source Code"]'
                yield log_message(f"🖱️ Clicking the submit button: {submit_button_selector}")
                await page.locator(submit_button_selector).click()
                
                yield log_message("✅ Clicked! Waiting for source code results page to load...")
                await page.wait_for_load_state("load", timeout=60000) # Wait up to 60s for results
                yield log_message("✅ Source code page loaded.")
                async for log in yield_html_snapshot(page, "On results page"): yield log
                await asyncio.sleep(3)

                # --- Step 4: Scroll to the footer and click 'Security' ---
                # From the source, the link is in the footer: <li><a href=".../security-policy/" title="Security">Security</a></li>
                security_link_selector = 'footer a[title="Security"]'
                yield log_message(f"👇 Scrolling to the footer to find the 'Security' link...")
                security_link = page.locator(security_link_selector)
                
                # Scroll the element into view before clicking
                await security_link.scroll_into_view_if_needed()
                yield log_message(f"🎯 Found 'Security' link. Now clicking it...")
                async for log in yield_html_snapshot(page, "After scrolling to footer"): yield log
                await asyncio.sleep(2)
                
                await security_link.click()
                
                yield log_message("✅ Clicked! Waiting for the final page to load...")
                await page.wait_for_load_state("load")
                yield log_message("✅ Final 'Security Policy' page loaded!")
                async for log in yield_html_snapshot(page, "On final page"): yield log
                
                yield log_message(f"✨ MISSION ACCOMPLISHED! Test completed successfully.")
                yield f"--LINK--{page.url}" # Return the final URL

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
