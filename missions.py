import asyncio

# This file contains the step-by-step instructions for different missions.
# The `engine` (scraper.py) will provide the `page` and `yield_log` objects.

async def mission_google_to_wikipedia(page, yield_log):
    """
    Mission: Go to Google, search for Wikipedia, navigate to it, 
    and then search for 'Amitabh Bachchan'.
    """
    await yield_log("MISSION: Google -> Wikipedia -> Amitabh Bachchan")

    # Step 1: Go to Google
    await yield_log("🌐 Navigating to www.google.com...")
    await page.goto("https://www.google.com", wait_until="load")
    await yield_log("✅ Google page loaded.")
    await asyncio.sleep(2)

    # Step 2: Search for Wikipedia
    search_box = page.locator('textarea[name="q"]')
    await yield_log("🎯 Typing 'Wikipedia' into search box...")
    await search_box.fill("Wikipedia")
    await asyncio.sleep(2)

    await yield_log("⌨️ Pressing Enter...")
    await search_box.press('Enter')
    await page.wait_for_load_state("load")
    await yield_log("✅ Google search results loaded.")
    await asyncio.sleep(2)

    # Step 3: Click the Wikipedia link
    wiki_link = page.locator('a[href*="wikipedia.org"]').first
    await yield_log("🎯 Clicking the first Wikipedia link...")
    await wiki_link.click()
    await page.wait_for_load_state("load")
    await yield_log("✅ Wikipedia homepage loaded.")
    await asyncio.sleep(2)

    # Step 4: Search for Amitabh Bachchan
    wiki_search_box = page.locator('input[name="search"]')
    await yield_log("🎯 Typing 'Amitabh Bachchan'...")
    await wiki_search_box.fill("Amitabh Bachchan")
    await asyncio.sleep(2)
    
    await yield_log("⌨️ Clicking search button...")
    await page.locator('button:has-text("Search")').click()
    await page.wait_for_load_state("load")
    await yield_log("✅ Final page loaded!")

    return page.url # Return the final URL
