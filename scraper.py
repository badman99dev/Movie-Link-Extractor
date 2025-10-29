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
            yield log_message("▶️ Initiating 'Project Live Inspector'...")
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
                # --- Step 1: Go to Google ---
                yield log_message("🌐 Navigating to www.google.com...")
                await page.goto("https://www.google.com", wait_until="load")
                yield log_message("✅ Google page loaded.")
                async for log in yield_html_snapshot(page, "On Google homepage"): yield log
                await asyncio.sleep(3)

                # --- Step 2: Search for Wikipedia ---
                search_box_selector = 'textarea[name="q"]'
                yield log_message(f"🎯 Typing 'Wikipedia' into search box: {search_box_selector}")
                await page.locator(search_box_selector).fill("Wikipedia")
                async for log in yield_html_snapshot(page, "After typing 'Wikipedia'"): yield log
                await asyncio.sleep(3)

                yield log_message("⌨️ Pressing Enter to search...")
                await page.press(search_box_selector, 'Enter')
                yield log_message("✅ Search executed. Waiting for results page...")
                await page.wait_for_load_state("load")
                async for log in yield_html_snapshot(page, "On Google search results"): yield log
                await asyncio.sleep(3)

                # --- Step 3: Click the Wikipedia link ---
                wiki_link_selector = 'a[href*="wikipedia.org"]'
                yield log_message(f"🎯 Clicking the first Wikipedia link: {wiki_link_selector}")
                # We use .first to ensure we click the main link
                await page.locator(wiki_link_selector).first.click()
                yield log_message("✅ Clicked! Waiting for Wikipedia page to load...")
                await page.wait_for_load_state("load")
                yield log_message("✅ Wikipedia homepage loaded.")
                async for log in yield_html_snapshot(page, "On Wikipedia homepage"): yield log
                await asyncio.sleep(3)

                # --- Step 4: Search for Amitabh Bachchan on Wikipedia ---
                wiki_search_selector = 'input[name="search"]'
                yield log_message(f"🎯 Typing 'Amitabh Bachchan' into Wikipedia search box...")
                await page.locator(wiki_search_selector).fill("Amitabh Bachchan")
                async for log in yield_html_snapshot(page, "After typing 'Amitabh Bachchan'"): yield log
                await asyncio.sleep(3)
                
                yield log_message("⌨️ Clicking the search button...")
                await page.locator('button:has-text("Search")').click()
                yield log_message("✅ Search executed. Waiting for the final page...")
                await page.wait_for_load_state("load")
                yield log_message("✅ Final page loaded!")
                async for log in yield_html_snapshot(page, "On Amitabh Bachchan's page"): yield log
                
                yield log_message(f"✨ MISSION ACCOMPLISHED! Test completed successfully.")
                yield f"--LINK--{page.url}" # Return the final URL as the "link"

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
