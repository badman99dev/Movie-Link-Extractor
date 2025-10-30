import asyncio

# =============================================================
# MISSION BLUEPRINTS
# Define all your different missions here as functions.
# =============================================================

async def mission_google_to_wikipedia(page, yield_log):
    """
    Mission: Go to Google, search for Wikipedia, navigate to it, 
    and then search for 'Amitabh Bachchan'.
    """
    await yield_log("MISSION: Google -> Wikipedia -> Amitabh Bachchan")

    await yield_log("🌐 Navigating to www.google.com...")
    await page.goto("https://www.google.com", wait_until="load")
    await yield_log("✅ Google page loaded.")
    await asyncio.sleep(2)

    search_box = page.locator('textarea[name="q"]')
    await yield_log("🎯 Typing 'Wikipedia'...")
    await search_box.fill("Wikipedia")
    await asyncio.sleep(2)

    await yield_log("⌨️ Pressing Enter...")
    await search_box.press('Enter')
    await page.wait_for_load_state("load")
    
    wiki_link = page.locator('a[href*="wikipedia.org"]').first
    await yield_log("🎯 Clicking Wikipedia link...")
    await wiki_link.click()
    await page.wait_for_load_state("load")
    await yield_log("✅ Wikipedia loaded.")
    await asyncio.sleep(2)

    wiki_search_box = page.locator('input[name="search"]')
    await yield_log("🎯 Typing 'Amitabh Bachchan'...")
    await wiki_search_box.fill("Amitabh Bachchan")
    await asyncio.sleep(2)
    
    await yield_log("⌨️ Clicking search button...")
    await page.locator('button:has-text("Search")').click()
    await page.wait_for_load_state("load")
    
    return page.url

async def mission_get_imdb_rating(page, yield_log):
    """
    Mission: Go to IMDb, search for 'Inception', and extract its rating.
    """
    await yield_log("MISSION: Find IMDb Rating for 'Inception'")
    
    await yield_log("🌐 Navigating to www.imdb.com...")
    await page.goto("https://www.imdb.com/", wait_until="load")
    await asyncio.sleep(2)
    
    search_box = page.locator('input#suggestion-search')
    await yield_log("🎯 Typing 'Inception'...")
    await search_box.fill("Inception")
    await search_box.press('Enter')
    await page.wait_for_load_state("load")
    await asyncio.sleep(2)
    
    rating_element = page.locator('[data-testid="hero-rating-bar__aggregate-rating__score"] span').first
    await yield_log("⭐ Finding the rating...")
    rating = await rating_element.inner_text()
    
    return f"The rating for Inception is {rating}/10"


# =============================================================
# MISSION SELECTOR
# This is the ONLY part you need to change to switch missions.
# =============================================================

# Simply set `active_mission` to the function name of the mission you want to run.
active_mission = mission_google_to_wikipedia
# To run the IMDb mission instead, you would change the line above to:
# active_mission = mission_get_imdb_rating
