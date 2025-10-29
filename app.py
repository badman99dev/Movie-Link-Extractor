from flask import Flask, Response, stream_with_context
import asyncio
from scraper import VegamoviesScraper # Naam update kiya
import os

app = Flask(__name__)

# Hard-coded URL for testing and building
TEST_URL = "https://vegamovies.you/45078-thamma-2025-hindi-audio-hdtc-720p-480p-1080p.html"

# Health check endpoint
@app.route('/health')
def health_check():
    return "OK, I am alive! 🦾"

# Naya "Build" endpoint jo scraping shuru karega aur logs stream karega
@app.route('/build')
def build_and_get_link():
    
    async def generate_logs():
        scraper = VegamoviesScraper()
        final_link = None
        
        # Scraper ke generator se live logs praapt karo
        try:
            async for log_entry in scraper.stream_movie_link_extraction(TEST_URL):
                if log_entry.startswith("--LINK--"):
                    final_link = log_entry[8:] # '--LINK--' prefix hatao
                    yield f"data: {log_entry}\n\n" # Link ko bhi stream karo
                else:
                    # Har log message ko Server-Sent Event format me bhejo
                    yield f"data: {log_entry}\n\n"
        except Exception as e:
            yield f"data: ❌ Final error in app: {e}\n\n"
        
        # Stream ke end me ek final message
        yield "data: --- MISSION COMPLETE ---\n\n"

    # Response ko 'text/event-stream' mimetype ke saath bhejo
    return Response(stream_with_context(generate_logs()), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
