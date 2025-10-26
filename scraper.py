import asyncio
from playwright.async_api import async_playwright
import os

# तुम्हारी Browserless.io API Key यहाँ डालनी है।
# Render पर हम इसे Environment Variable में सेट करेंगे।
BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")
# NEW and CORRECT endpoint
BROWSERLESS_ENDPOINT = f'wss://production-sfo.browserless.io?token={BROWSERLESS_API_KEY}'

class Hdhub4uScraper:
    async def get_movie_links(self, movie_name):
        async with async_playwright() as p:
            print("Connecting to Browserless.io...")
            browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
            context = await browser.new_context()
            page = await context.new_page()
            print("Connection successful!")

            try:
                # स्टेप 1: मूवी सर्च करना
                search_url = f"https://hdhub4u.pictures/?s={movie_name.replace(' ', '+')}"
                print(f"Navigating to search page: {search_url}")
                await page.goto(search_url, wait_until="domcontentloaded")

                # स्टेप 2: सबसे सही मूवी लिंक ढूंढना और उस पर जाना
                movie_link_element = page.locator("ul.recent-movies li.thumb figcaption a").first
                movie_page_url = await movie_link_element.get_attribute("href")
                
                if not movie_page_url:
                    raise Exception("Movie not found on the search page.")

                print(f"Movie found! Navigating to movie page: {movie_page_url}")
                await page.goto(movie_page_url, wait_until="domcontentloaded")
                
                # स्टेप 3: मूवी पेज से viralkhabarbull के लिंक्स निकालना
                print("Extracting intermediate links...")
                link_locators = page.locator("main.page-body h3 > a")
                count = await link_locators.count()
                
                intermediate_links = {}
                for i in range(count):
                    element = link_locators.nth(i)
                    text = await element.inner_text()
                    href = await element.get_attribute("href")
                    if href and "viralkhabarbull.com" in href:
                        quality = text.split('[')[0].strip() # '480p⚡[450MB]' से '480p⚡' निकालना
                        intermediate_links[quality] = href
                
                if not intermediate_links:
                    raise Exception("No viralkhabarbull links found on the movie page.")
                
                print(f"Found intermediate links: {intermediate_links}")

                # स्टेप 4: हर लिंक के लिए फाइनल hblinks.dad URL निकालना
                final_links = {}
                for quality, url in intermediate_links.items():
                    try:
                        final_url = await self.solve_viralkhabarbull(context, url)
                        final_links[quality] = final_url
                    except Exception as e:
                        print(f"Could not solve for quality '{quality}': {e}")
                        final_links[quality] = f"Error: {e}"

                return final_links

            finally:
                await browser.close()

    async def solve_viralkhabarbull(self, context, initial_url):
        # हर लिंक के लिए एक नया पेज खोलेंगे ताकि वो एक-दूसरे को डिस्टर्ब न करें
        page = await context.new_page()
        
        # पॉप-अप को ऑटोमेटिकली बंद करने का जुगाड़
        page.context.on("page", lambda new_page: new_page.close())
        
        try:
            print(f"Solving labyrinth for: {initial_url}")
            await page.goto(initial_url, wait_until="networkidle")
            await page.wait_for_url("**/homelander/**", timeout=15000)
            print("Redirect successful.")

            continue_button = page.locator("#verify_btn:has-text('Click To Continue')")
            await continue_button.wait_for(state="visible", timeout=10000)
            await continue_button.click()
            print("'Click To Continue' pressed.")

            get_links_button = page.locator("a.get-link:has-text('Get Links')")
            await get_links_button.wait_for(state="visible", timeout=15000)
            print("'Get Links' button appeared.")

            final_url = await get_links_button.get_attribute("href")
            print(f"Final URL Extracted: {final_url}")
            
            return final_url
        finally:
            await page.close()
