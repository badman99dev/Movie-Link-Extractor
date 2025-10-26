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
                context.set_default_navigation_timeout(90000)
                context.set_default_timeout(60000)
                page = await context.new_page()
                print("Connection successful!")
            except Exception as e:
                print(f"Failed to connect to Browserless: {e}")
                raise

            try:
                # स्टेप 1 & 2: मूवी खोजना और उसके पेज पर जाना
                search_url = f"https://hdhub4u.pictures/?s={movie_name.replace(' ', '+')}"
                print(f"Navigating to search page: {search_url}")
                await page.goto(search_url, wait_until="domcontentloaded")

                movie_link_element = page.locator("ul.recent-movies li.thumb figcaption a").first
                try:
                    await movie_link_element.wait_for(state="visible", timeout=15000)
                    movie_page_url = await movie_link_element.get_attribute("href")
                except Exception:
                    raise Exception(f"Movie '{movie_name}' not found on the search page.")

                if not movie_page_url:
                    raise Exception("Movie link could not be extracted.")

                print(f"Movie found! Navigating to movie page: {movie_page_url}")
                await page.goto(movie_page_url, wait_until="domcontentloaded")
                
                # स्टेप 3: सिर्फ 720p वाले लिंक को ढूंढना
                print("Searching for the '720p' link...")
                # locator को और सटीक बनाया गया है
                link_720p = page.locator("main.page-body h3 > a:has-text('720p')").first
                
                try:
                    await link_720p.wait_for(state="visible", timeout=10000)
                except Exception:
                    raise Exception("720p link not found on the movie page.")

                intermediate_url = await link_720p.get_attribute("href")
                quality_text = await link_720p.inner_text()
                quality = quality_text.split('[')[0].strip().replace('⚡', '')

                print(f"Found target link for '{quality}': {intermediate_url}")

                # स्टेप 4: सिर्फ एक पहेली को सॉल्व करना
                final_link_data = await self.solve_puzzle_like_a_human(context, quality, intermediate_url)
                
                return final_link_data

            finally:
                print("Closing browser connection.")
                await browser.close()

    async def solve_puzzle_like_a_human(self, context, quality, url):
        page = None
        try:
            page = await context.new_page()
            
            print(f"--- Solving for [{quality}] ---")
            print(f"Navigating to: {url}")
            await page.goto(url, wait_until="domcontentloaded")
            
            print("Waiting for Cloudflare challenge or redirect...")
            await page.wait_for_url("**/homelander/**", timeout=30000)
            print("Cloudflare passed! On the puzzle page.")

            # --- "Click to Continue" को इंसान की तरह हैंडल करना ---
            continue_button = page.locator("#verify_btn:has-text('Click To Continue')")
            await continue_button.wait_for(state="visible", timeout=15000)
            
            print("Preparing to click and handle potential pop-up...")
            try:
                async with context.expect_page(timeout=5000) as popup_info:
                    await continue_button.click()
                
                popup_page = await popup_info.value
                await popup_page.wait_for_load_state("domcontentloaded", timeout=20000)
                print(f"Pop-up appeared: {popup_page.url}. Closing it.")
                await popup_page.close()
            except asyncio.TimeoutError:
                print("No pop-up on first click. Continuing.")
                pass

            print("Returned to main page. Waiting for timer...")

            # --- टाइमर और "Get Links" बटन ---
            get_links_button = page.locator("a.get-link:has-text('Get Links')")
            await get_links_button.wait_for(state="visible", timeout=15000)
            print("'Get Links' button is now visible.")

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
