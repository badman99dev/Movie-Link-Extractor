import asyncio
from playwright.async_api import async_playwright
import os

BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")
BROWSERLESS_ENDPOINT = f'wss://production-sfo.browserless.io?token={BROWSERLESS_API_KEY}'

class Hdhub4uScraper:
    async def get_movie_links(self, movie_name):
        async with async_playwright() as p:
            print("Connecting to Browserless.io...")
            try:
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                context = await browser.new_context()
                context.set_default_navigation_timeout(90000) # 90 second timeout for navigation
                context.set_default_timeout(90000) # 90 second timeout for actions
                page = await context.new_page()
                print("Connection successful!")
            except Exception as e:
                print(f"Failed to connect to Browserless: {e}")
                raise

            try:
                # Phase 1: Search for the movie
                search_url = f"https://hdhub4u.pictures/?s={movie_name.replace(' ', '+')}"
                print(f"Navigating to search page: {search_url}")
                await page.goto(search_url, wait_until="domcontentloaded")

                # Phase 2: Find the correct movie link
                movie_link_element = page.locator("ul.recent-movies li.thumb figcaption a").first
                try:
                    await movie_link_element.wait_for(state="visible", timeout=10000)
                    movie_page_url = await movie_link_element.get_attribute("href")
                except Exception:
                    raise Exception("Movie not found on the search page. No results.")

                if not movie_page_url:
                    raise Exception("Movie link could not be extracted.")

                print(f"Movie found! Navigating to movie page: {movie_page_url}")
                await page.goto(movie_page_url, wait_until="domcontentloaded")
                
                # Phase 3: Extract intermediate links
                print("Extracting intermediate links...")
                link_locators = page.locator("main.page-body h3 > a")
                count = await link_locators.count()
                
                intermediate_links = {}
                for i in range(count):
                    element = link_locators.nth(i)
                    text = await element.inner_text()
                    href = await element.get_attribute("href")
                    if href and ("viralkhabarbull.com" in href or "hblinks.dad" in href):
                        quality = text.split('[')[0].strip().replace('⚡', '')
                        intermediate_links[quality] = href
                
                if not intermediate_links:
                    raise Exception("No initial download links (like viralkhabarbull) found on the movie page.")
                
                print(f"Found intermediate links: {intermediate_links}")

                # Phase 4: Solve the puzzle for each link, one by one
                final_links = {}
                for quality, url in intermediate_links.items():
                    if "viralkhabarbull.com" in url:
                        result = await self.solve_puzzle_like_a_human(context, quality, url)
                        if result:
                            final_links.update(result)
                    else:
                        # If it's already a final link, just add it
                        final_links[quality] = url

                return final_links

            finally:
                print("Closing browser connection.")
                await browser.close()

    async def solve_puzzle_like_a_human(self, context, quality, url):
        page = None
        try:
            # Create a new page for each puzzle to keep things clean
            page = await context.new_page()
            
            print(f"--- Solving for [{quality}] ---")
            print(f"Navigating to: {url}")
            await page.goto(url, wait_until="domcontentloaded")
            
            # Wait for the redirect to the main puzzle page
            await page.wait_for_url("**/homelander/**", timeout=30000)
            print("Redirect successful. On the puzzle page.")

            # --- Handle "Click to Continue" button and its pop-up ---
            continue_button = page.locator("#verify_btn:has-text('Click To Continue')")
            await continue_button.wait_for(state="visible", timeout=10000)
            
            print("Waiting for pop-up after first click...")
            async with context.expect_page() as popup_info:
                await continue_button.click()
            
            popup_page = await popup_info.value
            await popup_page.wait_for_load_state("domcontentloaded", timeout=20000)
            print(f"Pop-up appeared: {popup_page.url}. Closing it.")
            await popup_page.close()
            print("Returned to main page.")

            # --- Wait for timer and "Get Links" button ---
            get_links_button = page.locator("a.get-link:has-text('Get Links')")
            print("Waiting for the timer and 'Get Links' button...")
            await get_links_button.wait_for(state="visible", timeout=15000)
            print("'Get Links' button is visible.")

            final_url = await get_links_button.get_attribute("href")
            print(f"SUCCESS for [{quality}]! Final URL: {final_url}")
            return {quality: final_url}

        except Exception as e:
            error_message = f"Error for [{quality}]: {type(e).__name__} - {str(e).split('Call log:')[0].strip()}"
            print(error_message)
            return {quality: error_message}
        finally:
            if page:
                await page.close()
