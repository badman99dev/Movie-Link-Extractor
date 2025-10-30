import asyncio
from playwright.async_api import async_playwright
import os
import time

BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")
if not BROWSERLESS_API_KEY:
    raise ValueError("FATAL: BROWSERLESS_API_KEY environment variable not set!")
    
BROWSERLESS_ENDPOINT = f'wss://production-sfo.browserless.io?token={BROWSERLESS_API_KEY}'

class Scraper:
    
    async def run_fireworks_mission(self):
        start_time = time.time()
        
        # Helper function to create formatted log messages
        def log_message_str(message):
            elapsed_time = f"[{time.time() - start_time:.2f}s]"
            return f"data: {elapsed_time} {message}\n\n"
        
        # Helper function to yield HTML snapshots
        async def yield_html_snapshot(page, description):
            yield log_message_str(f"🔄 Syncing HTML: {description}")
            try:
                html_content = await page.content()
                yield f"data: --HTML-SNAPSHOT--{html_content.replace(chr(10), '').replace(chr(13), '')}\n\n"
            except Exception as e:
                yield log_message_str(f"⚠️ Could not sync HTML: {e}")

        async with async_playwright() as p:
            yield log_message_str("▶️ Initiating SmailPro Mission...")
            browser, context, page = None, None, None
            try:
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                context = await browser.new_context(viewport={'width': 1280, 'height': 800})
                page = await context.new_page()
                yield log_message_str("✅ Browser connection successful.")
            except Exception as e:
                yield log_message_str(f"❌ Connection Failure: {e}")
                raise

            try:
                # #################################################
                # #####       NEW SMAILPRO MISSION LOGIC      #####
                # #################################################
                
                target_url = "https://smailpro.com/temporary-email"
                yield log_message_str(f"🌐 Navigating to {target_url}...")
                await page.goto(target_url, wait_until="load")
                yield log_message_str("✅ SmailPro page loaded.")
                async for item in yield_html_snapshot(page, "On SmailPro Homepage"): yield item

                # Step 1: Click the main "Create" button to open the modal
                create_button_selector = 'div.bg-green-700:has-text("Create")'
                yield log_message_str("🖱️ Clicking 'Create' to open modal...")
                await page.locator(create_button_selector).click()
                yield log_message_str("✅ Modal opened. Waiting for content...")
                await asyncio.sleep(2) # Give modal animation time to finish
                async for item in yield_html_snapshot(page, "Create Email Modal Open"): yield item
                
                # Step 2: Click the "Generate" button inside the modal
                generate_button_selector = 'div[x-data="create()"] button:has-text("Generate")'
                yield log_message_str(f"🖱️ Clicking 'Generate' button inside modal...")
                await page.locator(generate_button_selector).wait_for(state="visible", timeout=10000)
                await page.locator(generate_button_selector).click()
                yield log_message_str("✅ Clicked 'Generate'. Waiting for email to appear on main page...")
                
                # Step 3: Wait for the email to be generated and displayed
                email_display_selector = 'div[x-data="inbox()"] div.truncate'
                yield log_message_str(f"⏳ Waiting for email element ('{email_display_selector}') to be visible...")
                email_element = page.locator(email_display_selector)
                await email_element.wait_for(state="visible", timeout=20000) # Wait up to 20 seconds
                
                generated_email = await email_element.inner_text()
                yield log_message_str(f"🎉 SUCCESS! Generated Email: {generated_email}")
                async for item in yield_html_snapshot(page, "After Email Generation"): yield item
                
                # Step 4: Final wait as requested by the user
                yield log_message_str("⏳ Observing for 10 seconds before mission end...")
                await asyncio.sleep(10)

                yield log_message_str(f"✨ MISSION ACCOMPLISHED!")

            except Exception as e:
                error_message = str(e).split('Call log:')[0].strip()
                yield log_message_str(f"❌ MISSION FAILED: {error_message}")
                if page and not page.is_closed():
                    async for item in yield_html_snapshot(page, "At the moment of failure"):
                        yield item
                raise
            finally:
                yield log_message_str("🚪 Closing browser session...")
                if context: await context.close()
                if browser: await browser.close()
                yield log_message_str("--- MISSION COMPLETE ---")
