from flask import Flask, Response, stream_with_context, render_template # render_template add kiya
import asyncio
from scraper import VegamoviesScraper
import os

app = Flask(__name__)

TEST_URL = "https://vegamovies.you/45078-thamma-2025-hindi-audio-hdtc-720p-480p-1080p.html"

# Naya route jo HTML page serve karega
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health_check():
    return "OK, I am alive! 🦾"

@app.route('/build')
def build_and_get_link():
    async def generate_logs():
        scraper = VegamoviesScraper()
        try:
            async for log_entry in scraper.stream_movie_link_extraction(TEST_URL):
                if log_entry.startswith("--LINK--"):
                    yield f"data: {log_entry}\n\n"
                else:
                    yield f"data: {log_entry}\n\n"
        except Exception as e:
            yield f"data: ❌ Final error in app: {e}\n\n"
        yield "data: --- MISSION COMPLETE ---\n\n"

    return Response(stream_with_context(generate_logs()), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
