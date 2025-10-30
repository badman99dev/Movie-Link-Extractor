from quart import Quart, Response, render_template, stream_with_context
from scraper import Scraper # Import the single Scraper class
import os

app = Quart(__name__)

@app.route('/')
async def home():
    return await render_template('index.html')

@app.route('/build')
async def run_mission_endpoint():
    
    @stream_with_context
    async def log_streamer():
        # Create an instance of our simple, all-in-one scraper
        scraper = Scraper()
        try:
            # Directly call the mission. No more passing functions around.
            async for log_entry in scraper.run_fireworks_mission():
                # No need to check the format, the scraper now sends SSE format directly
                yield log_entry
        except Exception as e:
            # Just in case an error escapes the scraper
            yield f"data: ❌ Final unhandled error in app: {e}\n\n"

    return Response(log_streamer(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
