from quart import Quart, Response, render_template, stream_with_context
import asyncio
from scraper import VegamoviesScraper
import os

app = Quart(__name__) # Flask ki jagah Quart

TEST_URL = "https://vegamovies.you/45078-thamma-2025-hindi-audio-hdtc-720p-480p-1080p.html"

@app.route('/')
async def home():
    return await render_template('index.html')

@app.route('/health')
async def health_check():
    return "OK, I am alive! 🦾"

@app.route('/build')
async def build_and_get_link():
    
    @stream_with_context
    async def generate_logs():
        scraper = VegamoviesScraper()
        try:
            # Ab hum aasaani se async for loop chala sakte hain
            async for log_entry in scraper.stream_movie_link_extraction(TEST_URL):
                if log_entry.startswith("--LINK--"):
                    yield f"data: {log_entry}\n\n"
                else:
                    yield f"data: {log_entry}\n\n"
        except Exception as e:
            yield f"data: ❌ Final error in app: {e}\n\n"
        
        yield "data: --- MISSION COMPLETE ---\n\n"

    return Response(generate_logs(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    # Quart's own way to run
    app.run(debug=True, host='0.0.0.0', port=port)
