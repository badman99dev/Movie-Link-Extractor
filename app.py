from quart import Quart, Response, render_template, stream_with_context
from scraper import ScraperEngine
# Import the specific 'active_mission' variable from the missions file
from missions import active_mission
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
            # We tell the engine to run whatever mission is currently active.
            # We don't care what its name is.
            async for log_entry in engine.run_mission(active_mission):
                yield f"data: {log_entry}\n\n"
        except Exception as e:
            yield f"data: ❌ Final error in app: {e}\n\n"

    return Response(log_streamer(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
