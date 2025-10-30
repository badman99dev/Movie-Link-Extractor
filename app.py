from quart import Quart, Response, render_template, stream_with_context
from scraper import ScraperEngine
from missions import mission_google_to_wikipedia # Import the specific mission we want to run
import os

app = Quart(__name__)

@app.route('/')
async def home():
    return await render_template('index.html')

@app.route('/build')
async def run_mission_endpoint():
    
    @stream_with_context
    async def log_streamer():
        engine = ScraperEngine()
        try:
            # We tell the engine to run the `mission_google_to_wikipedia` mission
            async for log_entry in engine.run_mission(mission_google_to_wikipedia):
                yield f"data: {log_entry}\n\n"
        except Exception as e:
            yield f"data: ❌ Final error in app: {e}\n\n"

    return Response(log_streamer(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
