from quart import Quart, Response, render_template, stream_with_context
import asyncio
from scraper import LiveInspector # The class name is still LiveInspector
import os

app = Quart(__name__)

@app.route('/')
async def home():
    return await render_template('index.html')

@app.route('/health')
async def health_check():
    return "OK, I am alive! 🦾"

@app.route('/build')
async def build_and_run_test():
    
    @stream_with_context
    async def generate_logs():
        inspector = LiveInspector()
        try:
            # We call the same function name as before
            async for log_entry in inspector.run_test_mission():
                if log_entry.startswith(("--HTML-SNAPSHOT--", "--LINK--")):
                    yield f"data: {log_entry}\n\n"
                else:
                    yield f"data: {log_entry}\n\n"
        except Exception as e:
            yield f"data: ❌ Final error in app: {e}\n\n"

    return Response(generate_logs(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
