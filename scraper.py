import asyncio
from playwright.async_api import async_playwright
import os

BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")
BROWSERLESS_ENDPOINT = f'wss://production-sfo.browserless.io?token={BROWSERLESS_API_KEY}'

class Hdhub4uScraper:
    # ... get_movie_links फ़ंक्शन में कोई बदलाव नहीं ...
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
                search_url = f"https://hdhub4u.pictures/?s={movie_name.replace(' ', '+')}"
                print(f"Navigating to search page: {search_url}")
                await page.goto(search_url, wait_until="load")

                movie_link_element = page.locator("ul.recent-movies li.thumb figcaption a").first
                try:
                    await movie_link_element.wait_for(state="visible", timeout=15000)
                    movie_page_url = await movie_link_element.get_attribute("href")
                except Exception:
                    raise Exception(f"Movie '{movie_name}' not found on the search page.")

                if not movie_page_url:
                    raise Exception("Movie link could not be extracted.")

                print(f"Movie found! Navigating to movie page: {movie_page_url}")
                await page.goto(movie_page_url, wait_until="load")
                
                print("Searching for the '720p' link...")
                link_720p = page.locator("main.page-body h3 > a:has-text('720p')").first
                
                try:
                    await link_720p.wait_for(state="visible", timeout=10000)
                except Exception:
                    raise Exception("720p link not found on the movie page.")

                intermediate_url = await link_720p.get_attribute("href")
                quality_text = await link_720p.inner_text()
                quality = quality_text.split('[')[0].strip().replace('⚡', '')

                print(f"Found target link for '{quality}': {intermediate_url}")

                final_link_data = await self.solve_puzzle_like_a_human_spy_mode(context, quality, intermediate_url)
                
                return final_link_data

            finally:
                print("Closing browser connection.")
                await browser.close()
                
    # --- यह हमारा नया जासूसी फ़ंक्शन है ---
    async def solve_puzzle_like_a_human_spy_mode(self, context, quality, url):
        page = None
        try:
            page = await context.new_page()
            
            # --- URL Path Tracker ---
            navigation_path = []
            def log_nav(response):
                if response and response.url:
                    navigation_path.append(response.url)
            
            page.on("response", log_nav)
            # --- End Tracker ---

            print(f"--- Solving for [{quality}] with SPY CAM ---")
            print(f"Navigating to: {url}")
            await page.goto(url, wait_until="load", timeout=90000)
            
            continue_button = page.locator("#verify_btn:has-text('Click To Continue')")
            print("Now waiting for the 'Click To Continue' button to become visible...")
            await continue_button.wait_for(state="visible", timeout=45000)
            print("SUCCESS! 'Click To Continue' button is on screen.")
            
            # ... (बाकी का लॉजिक अगर यह काम करता है) ...
            # ... (Human mimic logic for pop-up and get links) ...
            
            return {"status": "This part is not yet implemented"} # अस्थायी रिटर्न

        except Exception as e:
            final_url_on_fail = page.url
            page_content_on_fail = await page.content()
            
            error_message = (
                f"Error for [{quality}]: {type(e).__name__} - {str(e).split('Call log:')[0].strip()}\n"
                f"--- SPY REPORT ---\n"
                f"URL at time of failure: {final_url_on_fail}\n"
                f"Navigation Path: {navigation_path}\n"
                f"--- End of Report ---"
            )
            # हम पूरा HTML नहीं दिखाएंगे क्योंकि वह logs को बहुत बड़ा कर देगा,
            # लेकिन URL Path हमें सब कुछ बता देगा।
            
            print(error_message)
            return {quality: error_message}
        finally:
            if page:
                page.remove_listener("response", log_nav)
                await page.close()
