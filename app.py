from quart import Quart, Response, render_template, stream_with_context
import asyncio
# scraper.py se ab LiveInspector class import karenge
from scraper import LiveInspector 
import os

app = Quart(__name__)

@app.route('/')
async def home():
    return await render_template('index.html')

@app.route('/health')
async def health_check():
    return "OK, I am alive! 🦾"

# `/build` endpoint ab naya test mission chalayega
@app.route('/build')
async def build_and_run_test():
    
    @stream_with_context
    async def generate_logs():
        # LiveInspector ka object banaya
        inspector = LiveInspector()
        try:
            # `run_test_mission` function ko call kiya
            async for log_entry in inspector.run_test_mission():
                # HTML aur LINK messages ko waise hi handle kiya
                if log_entry.startswith(("--HTML-SNAPSHOT--", "--LINK--")):
                    yield f"data: {log_entry}\n\n"
                else:
                    yield f"data: {log_entry}\n\n"
        except Exception as e:
            yield f"data: ❌ Final error in app: {e}\n\n"
        
        # --- MISSION COMPLETE --- ko alag se handle karne ki zaroorat nahi,
        # woh scraper se aa jaayega.

    return Response(generate_logs(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
