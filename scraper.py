import asyncio
from playwright.async_api import async_playwright, Error
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
            yield log_message_str("▶️ Initiating SmailPro Mission (v4 - FINAL)...")
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
                await page.goto(target_url, wait_until="domcontentloaded")
                yield log_message_str("✅ SmailPro page loaded.")
                
                create_button_selector = 'div.bg-green-700:has-text("Create")'
                await page.locator(create_button_selector).wait_for(state="visible", timeout=15000)
                async for item in yield_html_snapshot(page, "On SmailPro Homepage"): yield item

                yield log_message_str("🖱️ Clicking 'Create' to open modal...")
                await page.locator(create_button_selector).click()
                
                modal_content_selector = 'label:has-text("Email Type")'
                yield log_message_str("⏳ Waiting for modal content to be visible...")
                await page.locator(modal_content_selector).wait_for(state="visible", timeout=15000)
                yield log_message_str("✅ Modal content is ready.")
                
                yield log_message_str("🤖 Adding a human-like pause for reCAPTCHA...")
                await asyncio.sleep(2)

                # ===== THE FINAL FIX IS HERE! =====
                generate_button_selector = 'div[x-data="create()"] button:has-text("Generate")'
                yield log_message_str(f"🖱️ Attempting to click 'Generate' button...")
                try:
                    # Click without waiting for it to be stable, because it will disappear.
                    await page.locator(generate_button_selector).click(timeout=5000)
                except Error as e:
                    # We EXPECT a timeout or "not visible" error here, because the button
                    # is replaced by a spinner. This error means the click was successful.
                    if "is not visible" in str(e) or "Timeout" in str(e):
                        yield log_message_str("✅ Click successful (button disappeared as expected).")
                    else:
                        # If it's a different error, we should fail.
                        raise e
                # ==================================

                yield log_message_str("⏳ Waiting for new email to be displayed...")
                
                # Wait for the "No email selected" placeholder to disappear.
                await page.locator('text=No email selected').wait_for(state='hidden', timeout=25000)
                yield log_message_str("✅ Placeholder disappeared, new email is present.")

                email_display_selector = 'div[x-data="inbox()"] div.truncate'
                email_element = page.locator(email_display_selector).first()
                
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
