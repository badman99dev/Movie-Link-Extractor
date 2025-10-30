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
        
        def log_message_str(message):
            elapsed_time = f"[{time.time() - start_time:.2f}s]"
            return f"data: {elapsed_time} {message}\n\n"
        
        async def yield_html_snapshot(page, description):
            yield log_message_str(f"🔄 Syncing HTML: {description}")
            try:
                html_content = await page.content()
                yield f"data: --HTML-SNAPSHOT--{html_content.replace(chr(10), '').replace(chr(13), '')}\n\n"
            except Exception as e:
                yield log_message_str(f"⚠️ Could not sync HTML: {e}")

        async with async_playwright() as p:
            yield log_message_str("▶️ Initiating SmailPro Mission (v2)...") # Version 2!
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
                target_url = "https://smailpro.com/temporary-email"
                yield log_message_str(f"🌐 Navigating to {target_url}...")
                await page.goto(target_url, wait_until="load")
                yield log_message_str("✅ SmailPro page loaded.")
                async for item in yield_html_snapshot(page, "On SmailPro Homepage"): yield item

                create_button_selector = 'div.bg-green-700:has-text("Create")'
                yield log_message_str("🖱️ Clicking 'Create' to open modal...")
                await page.locator(create_button_selector).click()
                yield log_message_str("✅ Clicked 'Create'. Waiting for modal content to load...")
                
                # ===== FIX IS HERE! =====
                # Wait for a stable element inside the modal to ensure it's fully loaded
                modal_content_selector = 'label:has-text("Email Type")'
                yield log_message_str("⏳ Waiting for modal content to be visible...")
                await page.locator(modal_content_selector).wait_for(state="visible", timeout=15000)
                yield log_message_str("✅ Modal content is ready.")
                # ========================
                
                async for item in yield_html_snapshot(page, "Create Email Modal Open"): yield item
                
                generate_button_selector = 'div[x-data="create()"] button:has-text("Generate")'
                yield log_message_str(f"🖱️ Clicking 'Generate' button inside modal...")
                await page.locator(generate_button_selector).click()
                yield log_message_str("✅ Clicked 'Generate'. Waiting for email to appear on main page...")
                
                email_display_selector = 'div[x-data="inbox()"] div.truncate'
                yield log_message_str(f"⏳ Waiting for email element ('{email_display_selector}') to be visible...")
                email_element = page.locator(email_display_selector)
                await email_element.wait_for(state="visible", timeout=20000) 
                
                generated_email = await email_element.inner_text()
                yield log_message_str(f"🎉 SUCCESS! Generated Email: {generated_email}")
                async for item in yield_html_snapshot(page, "After Email Generation"): yield item
                
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
