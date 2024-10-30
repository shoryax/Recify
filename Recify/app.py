from flask import Flask, render_template, request
import requests
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Spotify API credentials from .env
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Get Access Token for Spotify API
def get_access_token():
    token_url = 'https://accounts.spotify.com/api/token'
    payload = {
        'grant_type': 'client_credentials',
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    
    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        raise Exception("Failed to obtain access token")
    
    return response.json().get('access_token')

# Function to make a request to Spotify API with rate limit handling
def spotify_api_request(url, headers):
    for i in range(5):  # Retry up to 5 times
        response = requests.get(url, headers=headers)

        if response.status_code == 429:  # Too Many Requests
            retry_after = int(response.headers.get('Retry-After', 1))
            time.sleep(retry_after)  # Wait before retrying
            continue
        
        if response.status_code != 200:
            raise Exception(f"Spotify API request failed with status {response.status_code}")
        
        return response.json()

# Home route
@app.route('/')
def index():
    return render_template('index.html', songs=[], error=None)

# Search route
@app.route('/search', methods=['POST'])
def search():
    try:
        search_term = request.form.get('search')  # Get the search term from the input
        category = request.form.get('category')
        language = request.form.get('language')
        
        # Construct the search query based on available inputs
        search_query = []
        if search_term:
            search_query.append(search_term)
        if category:
            search_query.append(category)
        if language:
            search_query.append(language)
        
        search_query_string = ' '.join(search_query).strip()  # Join non-empty queries

        # Ensure that at least one search term is present.
        if not search_query_string:
            return render_template('index.html', songs=[], error="Please enter a search term, category, or language.")

        token = get_access_token()
        headers = {'Authorization': f'Bearer {token}'}
        search_url = f'https://api.spotify.com/v1/search?q={search_query_string}&type=track&limit=10'
        data = spotify_api_request(search_url, headers)
        songs = data.get('tracks', {}).get('items', [])
        
        return render_template('index1.html', songs=songs, error=None)
    except Exception as e:
        error_message = f"Error: {e}"
        return render_template('index.html', songs=[], error=error_message)

# Run the app in debug mode
if __name__ == '__main__':
    app.run(debug=True)
