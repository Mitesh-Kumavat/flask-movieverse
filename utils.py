import sqlite3
import os
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

OMDB_API_KEY = os.getenv("OMDB_API_KEY") 
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def get_db_connection():
    conn = sqlite3.connect('movies.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_movie_image(imdb_id):
    url = f"http://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('Poster', '')
    return ''

def get_movie_trailer(title):
    print("START FINDING TRAILER")
    search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={title} trailer&key={YOUTUBE_API_KEY}"
    response = requests.get(search_url)
    if response.status_code == 200:
        data = response.json()
        if 'items' in data and len(data['items']) > 0:
            video_id = data['items'][0]['id']['videoId']
            trailer_url = f"https://www.youtube.com/embed/{video_id}?&autoplay=1&mute=0&rel=0"
            return trailer_url
    return None

def calculate_similarity(search_query, movies_df):
    movies_df['combined_features'] = movies_df['original_title'] + ' ' + movies_df['description'] + ' ' + movies_df['genre']
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(movies_df['combined_features'])
    query_vector = vectorizer.transform([search_query])
    cosine_sim = cosine_similarity(query_vector, tfidf_matrix).flatten()
    top_indices = cosine_sim.argsort()[-10:][::-1]
    top_movies = movies_df.iloc[top_indices][['imdb_title_id', 'original_title', 'year', 'avg_vote', 'description', 'genre']].to_dict(orient='records')

    return top_movies
