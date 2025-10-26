import asyncio
from playwright.async_api import async_playwright
import os

# तुम्हारी Browserless.io API Key यहाँ डालनी है।
# Render पर हम इसे Environment Variable में सेट करेंगे।
BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")

# नया और सही पता (UPDATED ENDPOINT)
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
                # स्टेप 1: मूवी सर्च करना
                search_url = f"https://hdhub4u.pictures/?s={movie_name.replace(' ', '+')}"
                print(f"Navigating to search page: {search_url}")
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)

                # स्टेप 2: सबसे सही मूवी लिंक ढूंढना और उस पर जाना
                # हम `.first` का इस्तेमाल कर रहे हैं यह मानकर कि पहला रिजल्ट सबसे सही होगा।
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
                
                # स्टेप 3: मूवी पेज से viralkhabarbull के लिंक्स निकालना
                print("Extracting intermediate links...")
                link_locators = page.locator("main.page-body h3 > a")
                count = await link_locators.count()
                
                intermediate_links = {}
                for i in range(count):
                    element = link_locators.nth(i)
                    text = await element.inner_text()
                    href = await element.get_attribute("href")
                    # हम सिर्फ viralkhabarbull वाले लिंक्स में इंटरेस्टेड हैं
                    if href and ("viralkhabarbull.com" in href or "hblinks.dad" in href):
                        quality = text.split('[')[0].strip().replace('⚡', '')
                        intermediate_links[quality] = href
                
                if not intermediate_links:
                    raise Exception("No initial download links (like viralkhabarbull) found on the movie page.")
                
                print(f"Found intermediate links: {intermediate_links}")

                # स्टेप 4: हर लिंक के लिए फाइनल hblinks.dad URL निकालना
                final_links = {}
                tasks = []
                for quality, url in intermediate_links.items():
                    if "viralkhabarbull.com" in url:
                        # हर viralkhabarbull लिंक को सॉल्व करने के लिए एक async task बनाओ
                        tasks.append(self.solve_viralkhabarbull_and_get_final_link(context, quality, url))
                    else:
                        # अगर लिंक पहले से ही hblinks.dad का है, तो उसे सीधा डाल दो
                        final_links[quality] = url

                # सभी tasks को एक साथ चलाओ ताकि समय बचे
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
        """
        यह हेल्पर फ़ंक्शन एक क्वालिटी और उसके URL के लिए पूरा प्रोसेस चलाता है।
        """
        try:
            final_url = await self.solve_viralkhabarbull(context, url)
            return {quality: final_url}
        except Exception as e:
            error_message = f"Error: {type(e).__name__} - {str(e).splitlines()[0]}"
            print(f"Could not solve for quality '{quality}': {error_message}")
            return {quality: error_message}

    async def solve_viralkhabarbull(self, context, initial_url):
        # हर लिंक के लिए एक नया पेज खोलेंगे
        page = await context.new_page()
        try:
            print(f"Solving labyrinth for URL: {initial_url}")
            
            # 1. ज़्यादा समय दो: टाइमआउट को 60 सेकंड (60000 ms) कर दिया है
            await page.goto(initial_url, wait_until="networkidle", timeout=60000)
            
            # पेज के पूरी तरह लोड होने का इंतज़ार करो
            await page.wait_for_url("**/homelander/**", timeout=20000)
            print("Redirect successful.")

            # 2. पॉप-अप ब्लॉकर को सही समय पर एक्टिवेट करो: क्लिक करने से ठीक पहले
            # 'once' का मतलब है कि यह सिर्फ अगली बार खुलने वाले पेज को ही बंद करेगा।
            page.context.once("page", lambda new_page: new_page.close())

            continue_button = page.locator("#verify_btn:has-text('Click To Continue')")
            await continue_button.wait_for(state="visible", timeout=10000)
            await continue_button.click()
            print("'Click To Continue' pressed.")

            get_links_button = page.locator("a.get-link:has-text('Get Links')")
            await get_links_button.wait_for(state="visible", timeout=15000) # 11 सेकंड के टाइमर के लिए इंतज़ार
            print("'Get Links' button has appeared.")

            final_url = await get_links_button.get_attribute("href")
            print(f"Final URL Extracted: {final_url}")
            
            return final_url
        finally:
            await page.close()
