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
        
        # HTML Snapshot function is still here, but we will not call it.
        async def yield_html_snapshot(page, description):
            # This function is now disabled for a logs-only run.
            pass
            # yield log_message_str(f"🔄 Syncing HTML: {description}")
            # try:
            #     html_content = await page.content()
            #     yield f"data: --HTML-SNAPSHOT--{html_content.replace(chr(10), '').replace(chr(13), '')}\n\n"
            # except Exception as e:
            #     yield log_message_str(f"⚠️ Could not sync HTML: {e}")

        async with async_playwright() as p:
            yield log_message_str("▶️ Initiating SmailPro Mission (v6 - Logs Only)...")
            browser, context, page = None, None, None
            try:
                yield log_message_str("    Connecting to remote browser...")
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                context = await browser.new_context(viewport={'width': 1280, 'height': 800})
                page = await context.new_page()
                yield log_message_str("    ✅ Browser connection successful.")
            except Exception as e:
                yield log_message_str(f"    ❌ Connection Failure: {e}")
                raise

            try:
                # ===== STEP 1: NAVIGATION =====
                target_url = "https://smailpro.com/temporary-email"
                yield log_message_str(f"    Navigating to {target_url}...")
                await page.goto(target_url, wait_until="domcontentloaded")
                yield log_message_str("    ✅ Page DOM content loaded.")
                
                # ===== STEP 2: OPEN MODAL =====
                create_button_selector = 'div.bg-green-700:has-text("Create")'
                yield log_message_str(f"    Waiting for main 'Create' button ('{create_button_selector}')...")
                await page.locator(create_button_selector).wait_for(state="visible", timeout=15000)
                yield log_message_str("    ✅ 'Create' button found. Clicking it now...")
                await page.locator(create_button_selector).click()
                
                # ===== STEP 3: PREPARE TO GENERATE =====
                modal_content_selector = 'label:has-text("Email Type")'
                yield log_message_str(f"    Waiting for modal content to appear ('{modal_content_selector}')...")
                await page.locator(modal_content_selector).wait_for(state="visible", timeout=15000)
                yield log_message_str("    ✅ Modal is open and ready.")
                
                yield log_message_str("    Pausing for 1 second to appear more human...")
                await asyncio.sleep(1)

                # ===== STEP 4: GENERATE AND WAIT =====
                generate_button_selector = 'div[x-data="create()"] button:has-text("Generate")'
                yield log_message_str(f"    Clicking the 'Generate' button inside modal...")
                await page.locator(generate_button_selector).click()

                # LOGIC: Wait for spinner to appear, then wait for it to disappear.
                spinner_selector = 'div:has-text("Generating")'
                yield log_message_str(f"    Waiting for spinner ('{spinner_selector}') to show up...")
                await page.locator(spinner_selector).wait_for(state="visible", timeout=5000)
                yield log_message_str("    ✅ Spinner is visible. Email generation is in progress.")
                
                yield log_message_str("    Now, waiting for spinner to vanish (this confirms completion)...")
                await page.locator(spinner_selector).wait_for(state="hidden", timeout=25000)
                yield log_message_str("    ✅ Spinner is gone. Generation is complete.")
                
                # ===== STEP 5: EXTRACT THE RESULT =====
                email_display_selector = 'div[x-data="inbox()"] div.truncate'
                yield log_message_str(f"    Locating the new email address using selector ('{email_display_selector}')...")
                email_element = page.locator(email_display_selector).first()
                
                generated_email = await email_element.inner_text()
                yield log_message_str("    ✅ Email text extracted successfully.")
                yield log_message_str(f"🎉 SUCCESS! Generated Email: {generated_email}")
                
                yield log_message_str("    Final 10-second observation as requested...")
                await asyncio.sleep(10)

                yield log_message_str(f"✨ MISSION ACCOMPLISHED!")

            except Exception as e:
                error_message = str(e).split('Call log:')[0].strip()
                yield log_message_str(f"❌ MISSION FAILED: {error_message}")
                # We are not sending HTML on failure either.
                # if page and not page.is_closed():
                #     async for item in yield_html_snapshot(page, "At the moment of failure"):
                #         yield item
                raise
            finally:
                yield log_message_str("    Closing browser session...")
                if context: await context.close()
                if browser: await browser.close()
                yield log_message_str("--- MISSION COMPLETE ---")
