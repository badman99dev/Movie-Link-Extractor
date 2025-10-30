import asyncio

# =============================================================
# MISSION BLUEPRINTS
# =============================================================

async def mission_fireworks_signup(page, yield_log):
    """
    Mission: Automate the signup process on app.fireworks.ai.
    """
    await yield_log("MISSION: Fireworks AI Signup Automation")

    # --- Step 1: Navigate to the Signup Page ---
    target_url = "https://app.fireworks.ai/signup"
    await yield_log(f"🌐 Navigating to {target_url}...")
    await page.goto(target_url, wait_until="load")
    await yield_log("✅ Signup page loaded.")
    await asyncio.sleep(4)

    # --- Step 2: Fill in the Email Address ---
    # From the source, the email input is: <input type="email" name="email">
    email_selector = 'input[name="email"]'
    email_to_fill = "savannapatte.r.so.n7.04@gmail.com"
    await yield_log(f"🎯 Typing email '{email_to_fill}'...")
    await page.locator(email_selector).fill(email_to_fill)
    await asyncio.sleep(4)

    # --- Step 3: Click the "Next" Button ---
    # From the source: <button type="submit">Next</button>
    next_button_selector = 'button[type="submit"]:has-text("Next")'
    await yield_log(f"🖱️ Clicking 'Next' button...")
    await page.locator(next_button_selector).click()
    await yield_log("✅ Clicked! Waiting for password page...")
    # We wait for the new elements to appear instead of a full page load
    await asyncio.sleep(4)

    # --- Step 4: Fill in the Password Fields ---
    # Modern apps often have password fields with name="password" and name="confirmPassword"
    password_selector = 'input[name="password"]'
    confirm_password_selector = 'input[name="confirmPassword"]' # This is a common name, might need adjustment
    strong_password = "TestPassword@12345" # A sample strong password

    await yield_log(f"🔑 Typing a strong password...")
    # It's better to wait for the element to be visible before filling
    await page.locator(password_selector).wait_for(state="visible", timeout=30000)
    await page.locator(password_selector).fill(strong_password)
    
    await yield_log(f"🔑 Confirming the password...")
    await page.locator(confirm_password_selector).fill(strong_password)
    await asyncio.sleep(4)

    # --- Step 5: Click the "Continue" Button ---
    # The button text will likely change to "Continue" or "Sign Up"
    continue_button_selector = 'button[type="submit"]:has-text("Continue")'
    await yield_log(f"🖱️ Clicking 'Continue' button...")
    await page.locator(continue_button_selector).click()
    await yield_log("✅ Clicked 'Continue'!")
    
    # --- Step 6: Final Wait ---
    await yield_log("⏳ Final 15-second observation period commencing...")
    await asyncio.sleep(15)
    await yield_log("✅ Observation complete.")

    return page.url # Return the final URL


# =============================================================
# MISSION SELECTOR
# This is the ONLY part you need to change to switch missions.
# =============================================================

active_mission = mission_fireworks_signup
