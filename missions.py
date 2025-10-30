import asyncio

async def mission_fireworks_signup(page, yield_log, yield_html):
    """
    Mission: Automate signup on app.fireworks.ai.
    This is now a generator function that controls the flow.
    """
    await yield_log("MISSION: Fireworks AI Signup Automation")

    # Step 1
    await yield_log("🌐 Navigating to signup page...")
    await page.goto("https://app.fireworks.ai/signup", wait_until="load")
    await yield_log("✅ Page loaded.")
    async for item in yield_html("On Signup Page"): yield item
    await asyncio.sleep(4)

    # Step 2
    email_selector = 'input[name="email"]'
    await yield_log("🎯 Typing email...")
    await page.locator(email_selector).fill("savannapatte.r.so.n7.04@gmail.com")
    async for item in yield_html("After typing email"): yield item
    await asyncio.sleep(4)

    # Step 3
    next_button_selector = 'button[type="submit"]:has-text("Next")'
    await yield_log("🖱️ Clicking 'Next'...")
    await page.locator(next_button_selector).click()
    await yield_log("✅ Clicked! Waiting for password fields...")
    await asyncio.sleep(4) # Wait for JS to render new fields
    async for item in yield_html("On Password Page"): yield item

    # Step 4
    password_selector = 'input[name="password"]'
    confirm_password_selector = 'input[name="confirmPassword"]'
    strong_password = "TestPassword@12345"

    await yield_log("🔑 Typing password...")
    await page.locator(password_selector).wait_for(state="visible", timeout=30000)
    await page.locator(password_selector).fill(strong_password)
    
    await yield_log("🔑 Confirming password...")
    await page.locator(confirm_password_selector).fill(strong_password)
    async for item in yield_html("After typing passwords"): yield item
    await asyncio.sleep(4)

    # Step 5
    continue_button_selector = 'button[type="submit"]:has-text("Continue")'
    await yield_log("🖱️ Clicking 'Continue'...")
    await page.locator(continue_button_selector).click()
    await yield_log("✅ Clicked 'Continue'!")
    
    # Step 6
    await yield_log("⏳ Final 15-second observation...")
    await asyncio.sleep(15)
    async for item in yield_html("Final State"): yield item

# =============================================================
# MISSION SELECTOR
# =============================================================
active_mission = mission_fireworks_signup
