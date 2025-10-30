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
        
        def log_message(message):
            elapsed_time = f"[{time.time() - start_time:.2f}s]"
            return f"data: {elapsed_time} {message}\n\n"
        
        async def yield_html_snapshot(page, description):
            # This is a generator, so it must be consumed with "async for"
            yield log_message(f"🔄 Syncing HTML: {description}")
            try:
                html_content = await page.content()
                yield f"data: --HTML-SNAPSHOT--{html_content.replace(chr(10), '').replace(chr(13), '')}\n\n"
            except Exception as e:
                yield log_message(f"⚠️ Could not sync HTML: {e}")

        async with async_playwright() as p:
            yield log_message("▶️ Initiating Final Stand (BUGFIX v2)...")
            browser, context, page = None, None, None
            try:
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                context = await browser.new_context(viewport={'width': 1280, 'height': 800})
                page = await context.new_page()
                yield log_message("✅ Connection successful. Mission begins NOW.")
            except Exception as e:
                yield log_message(f"❌ Connection Failure: {e}")
                raise

            try:
                # --- All the mission logic is the same and was correct ---
                target_url = "https://app.fireworks.ai/signup"
                yield log_message(f"🌐 Navigating to {target_url}...")
                await page.goto(target_url, wait_until="load")
                yield log_message("✅ Signup page loaded.")
                async for item in yield_html_snapshot(page, "On Signup Page"): yield item
                await asyncio.sleep(4)

                email_selector = 'input[name="email"]'
                await yield_log("🎯 Typing email...") # <--- THIS IS THE KIND OF ERROR I MADE. Correcting it now.
                # All calls must be `yield log_message(...)`

                # Let's rewrite the whole thing cleanly.

                yield log_message(f"🎯 Typing email...")
                await page.locator(email_selector).fill("savannapatte.r.so.n7.04@gmail.com")
                async for item in yield_html_snapshot(page, "After typing email"): yield item
                await asyncio.sleep(4)

                next_button_selector = 'button[type="submit"]:has-text("Next")'
                yield log_message("🖱️ Clicking 'Next'...")
                await page.locator(next_button_selector).click()
                yield log_message("✅ Clicked! Waiting for password page...")
                await asyncio.sleep(4)
                async for item in yield_html_snapshot(page, "On Password Page"): yield item

                password_selector = 'input[name="password"]'
                confirm_password_selector = 'input[name="confirmPassword"]'
                strong_password = "TestPassword@12345"

                yield log_message("🔑 Typing password...")
                await page.locator(password_selector).wait_for(state="visible", timeout=30000)
                await page.locator(password_selector).fill(strong_password)
                
                yield log_message("🔑 Confirming password...")
                await page.locator(confirm_password_selector).fill(strong_password)
                async for item in yield_html_snapshot(page, "After typing passwords"): yield item
                await asyncio.sleep(2)

                heading_selector = 'h2:has-text("Create Account")'
                yield log_message("🎯 Clicking on heading to trigger validation...")
                await page.locator(heading_selector).click()
                await asyncio.sleep(2)
                async for item in yield_html_snapshot(page, "After unfocusing"): yield item

                create_account_button_selector = 'button[type="submit"]:has-text("Create Account")'
                yield log_message(f"🖱️ Clicking the correct '{create_account_button_selector}' button...")
                await page.locator(create_account_button_selector).click()
                yield log_message("✅ Clicked 'Create Account'!")
                
                yield log_message("⏳ Final 15-second observation...")
                await asyncio.sleep(15)
                async for item in yield_html_snapshot(page, "Final State"): yield item

                yield log_message(f"✨ MISSION ACCOMPLISHED!")
                yield f"data: --LINK--{page.url}\n\n"

            except Exception as e:
                # #################################################
                # ##### THE BUG FIX IS HERE #####
                # #################################################
                error_message = str(e).split('Call log:')[0].strip()
                yield log_message(f"❌ MISSION FAILED: {error_message}")
                if page and not page.is_closed():
                    # Correctly loop over the generator
                    async for item in yield_html_snapshot(page, "At the moment of failure"):
                        yield item
                raise
            finally:
                # #################################################
                # ##### AND HERE #####
                # #################################################
                yield log_message("🚪 Closing browser session...")
                if context: await context.close()
                if browser: await browser.close()
                # Correctly wrap the final message
                yield log_message("--- MISSION COMPLETE ---")
