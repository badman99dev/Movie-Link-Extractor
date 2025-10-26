from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
from scraper import Hdhub4uScraper

app = Flask(__name__)
CORS(app)  # तुम्हारी लोकल HTML फ़ाइल से टेस्टिंग के लिए CORS इनेबल कर दिया है

# Render को बताने के लिए कि हमारा सर्वर ज़िंदा है
@app.route('/health')
def health_check():
    return jsonify({"status": "OK, I am alive! 🦾"})

# हमारा मेन API endpoint, जहाँ से मिशन शुरू होगा
@app.route('/api/start-mission', methods=['POST'])
def start_mission():
    data = request.json
    movie_name = data.get('movie_name')

    if not movie_name:
        return jsonify({"status": "error", "message": "Movie name is required."}), 400

    try:
        # Hdhub4uScraper क्लास का इस्तेमाल करके लिंक्स निकालते हैं
        scraper = Hdhub4uScraper()
        # asyncio.run() का इस्तेमाल करके async scraper को चलाते हैं
        links = asyncio.run(scraper.get_movie_links(movie_name))
        
        if not links:
            return jsonify({"status": "error", "message": f"Could not find download links for '{movie_name}'."})

        return jsonify({
            "status": "success",
            "movie_title": movie_name,
            "download_pages": links
        })

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
