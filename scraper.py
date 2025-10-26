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
                page = await context.new_page()
                print("Connection successful!")
            except Exception as e:
                print(f"Failed to connect to Browserless: {e}")
                raise

            try:
                search_url = f"https://hdhub4u.pictures/?s={movie_name.replace(' ', '+')}"
                print(f"Navigating to search page: {search_url}")
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)

                movie_link_element = page.locator("ul.recent-movies li.thumb figcaption a").first
                try:
                    await movie_link_element.wait_for(state="visible", timeout=10000)
                    movie_page_url = await movie_link_element.get_attribute("href")
                except Exception:
                    raise Exception("Movie not found on the search page. No results.")

                if not movie_page_url:
                    raise Exception("Movie link could not be extracted.")

                print(f"Movie found! Navigating to movie page: {movie_page_url}")
                await page.goto(movie_page_url, wait_until="domcontentloaded", timeout=60000)
                
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

                final_links = {}
                tasks = []
                for quality, url in intermediate_links.items():
                    if "viralkhabarbull.com" in url:
                        tasks.append(self.solve_viralkhabarbull_and_get_final_link(context, quality, url))
                    else:
                        final_links[quality] = url

                if tasks:
                    results = await asyncio.gather(*tasks)
                    for result in results:
                        if result:
                            final_links.update(result)

                return final_links

            finally:
                print("Closing browser connection.")
                await browser.close()

    async def solve_viralkhabarbull_and_get_final_link(self, context, quality, url):
        try:
            final_url = await self.solve_viralkhabarbull(context, url)
            return {quality: final_url}
        except Exception as e:
            error_message = f"Error: {type(e).__name__} - {str(e).splitlines()[0]}"
            print(f"Could not solve for quality '{quality}': {error_message}")
            return {quality: error_message}

    async def solve_viralkhabarbull(self, context, initial_url):
        page = await context.new_page()
        
        # --- START OF THE NEW STRATEGY ---
        # हम पॉप-अप को हैंडल करने के लिए एक इवेंट लिसनर बनाएंगे।
        async def handle_popup(popup):
            # हम मुख्य पेज को बंद नहीं करना चाहते, इसलिए हम इंतज़ार करेंगे
            # यह सुनिश्चित करने के लिए कि यह पॉप-अप है।
            await asyncio.sleep(1) # 1 सेकंड रुको
            if popup != page: # अगर यह हमारा मुख्य पेज नहीं है...
                print(f"Pop-up detected and closed: {popup.url}")
                await popup.close()

        context.on("page", handle_popup)
        # --- END OF THE NEW STRATEGY ---

        try:
            print(f"Solving labyrinth for URL: {initial_url}")
            await page.goto(initial_url, wait_until="domcontentloaded", timeout=60000)
            
            await page.wait_for_url("**/homelander/**", timeout=20000)
            print("Redirect successful.")

            continue_button = page.locator("#verify_btn:has-text('Click To Continue')")
            await continue_button.wait_for(state="visible", timeout=10000)
            await continue_button.click()
            print("'Click To Continue' pressed.")

            get_links_button = page.locator("a.get-link:has-text('Get Links')")
            await get_links_button.wait_for(state="visible", timeout=15000)
            print("'Get Links' button has appeared.")

            final_url = await get_links_button.get_attribute("href")
            print(f"Final URL Extracted: {final_url}")
            
            return final_url
        finally:
            context.remove_listener("page", handle_popup) # इवेंट लिसनर को हटाना ज़रूरी है
            await page.close()
