import asyncio
from playwright.async_api import async_playwright
import os

# Yeh pehle se aesa hi hoga, koi change nahi
BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")
if not BROWSERLESS_API_KEY:
    raise ValueError("FATAL: BROWSERLESS_API_KEY environment variable not set!")
    
BROWSERLESS_ENDPOINT = f'wss://production-sfo.browserless.io?token={BROWSERLESS_API_KEY}'

class Hdhub4uScraper: # Naam wahi rakha hai
    
    # Hum `get_movie_links` function ko `get_direct_link` bana rahe hain
    # aur yeh ab movie ka URL lega, search term nahi.
    async def get_direct_link(self, movie_url: str) -> str:
        async with async_playwright() as p:
            print("▶️ Connecting to Browserless.io via Playwright...")
            try:
                browser = await p.chromium.connect_over_cdp(BROWSERLESS_ENDPOINT)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
                context.set_default_navigation_timeout(90000)
                context.set_default_timeout(60000)
                page = await context.new_page()
                print("✅ Connection successful! Browser session is live.")
            except Exception as e:
                print(f"❌ CRITICAL ERROR: Failed to connect to Browserless.io. Error: {e}")
                raise

            try:
                # Step 1: Diye gaye Vegamovies URL par jaao
                print(f"🌐 Navigating to the Vegamovies page: {movie_url}")
                await page.goto(movie_url, wait_until="domcontentloaded")
                print("✅ Page navigation complete.")

                # Step 2: Iframe ko locate karo jisme player hai
                print("⏳ Searching for the video player iframe...")
                iframe_selector = "#IndStreamPlayer iframe"
                iframe = page.frame_locator(iframe_selector)
                
                # Check karo ki iframe load hua hai ya nahi
                if not await iframe.locator('body').is_visible(timeout=30000):
                     raise Exception("Could not find or load the iframe within 30 seconds.")
                
                print("👍 Found the iframe. Now searching for the <video> tag inside it...")

                # Step 3: Iframe ke andar <video> tag ko dhoondho
                video_selector = "video"
                video_tag = iframe.locator(video_selector)
                
                await video_tag.wait_for(state="attached", timeout=30000)
                print("👍 Found the <video> tag. Extracting the 'src' attribute...")

                # Step 4: Video ka 'src' link nikalo
                direct_link = await video_tag.get_attribute("src")

                if not direct_link:
                    raise Exception("Video tag found, but it has no 'src' attribute.")
                
                print(f"✨ BINGO! Direct link found: {direct_link[:70]}...")
                return [direct_link] # Isko list me return kar rahe hain taaki app.py ko aage dikkat na ho

            except Exception as e:
                print(f"❌ SCRAPING ERROR: An error occurred. Error: {e}")
                raise
            finally:
                print("🚪 Closing browser connection.")
                await browser.close()
    
    # Hum get_movie_links function ko bas ek wrapper bana denge
    async def get_movie_links(self, movie_url):
        # Yeh function ab direct link nikaalne wale function ko call karega
        return await self.get_direct_link(movie_url)
