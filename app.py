from flask import Flask, jsonify, request
import pandas as pd
from flask_cors import CORS
import os
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

df = pd.read_csv('./movies.csv')

app = Flask(__name__)
CORS(app)
OMDB_API_KEY = os.getenv('OMDB_API_KEY')

# Precompute TF-IDF matrix for movie descriptions
vectorizer = TfidfVectorizer(stop_words='english')
df['description'] = df['description'].fillna('')
tfidf_matrix = vectorizer.fit_transform(df['description'])


# Helper function to fetch image source from OMDb API
def fetch_movie_image(imdb_id):
    url = f"http://www.omdbapi.com/?i={imdb_id}&apikey=1e64c9b4"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('Poster', '')
    return ''



# Fetch top 10 movies by average vote
@app.route('/api/top-movies', methods=['GET'])
def get_top_movies():
    top_movies = df.nlargest(10, 'avg_vote')[['original_title', 'year', 'avg_vote', 'imdb_title_id']].to_dict(orient='records')
    for movie in top_movies:
        movie['img_src'] = fetch_movie_image(movie['imdb_title_id']) 
    return (top_movies)



# Fetch top 10 best-featured movies (e.g., based on votes)
@app.route('/api/featured-movies', methods=['GET'])
def get_top_featured_movies():
    top_featured = df.nlargest(10, 'votes')[['original_title', 'year', 'avg_vote', 'imdb_title_id']].to_dict(orient='records')
    for movie in top_featured:
        movie['img_src'] = fetch_movie_image(movie['imdb_title_id'])  # Add image URL
    return (top_featured)



# Fetch movie details by IMDB ID
@app.route('/api/movie/<imdb_id>', methods=['GET'])
def get_movie_details(imdb_id):
    movie = df[df['imdb_title_id'] == imdb_id].to_dict(orient='records')
    if not movie:
        return jsonify({"error": "Movie not found"}), 404

    movie_details = movie[0]
    movie_details['img_src'] = fetch_movie_image(imdb_id)  # Add image URL
    return (movie_details)



# Fetch similar movies using cosine similarity
@app.route('/api/movie/<imdb_id>/similar', methods=['GET'])
def get_similar_movies(imdb_id):
    try:
        movie_index = df[df['imdb_title_id'] == imdb_id].index[0]
    except IndexError:
        return jsonify({"error": "Movie not found"}), 404

    cosine_similarities = cosine_similarity(tfidf_matrix[movie_index], tfidf_matrix).flatten()
    similar_indices = cosine_similarities.argsort()[-11:-1][::-1]  # Exclude the movie itself

    similar_movies = df.iloc[similar_indices][['original_title', 'year', 'avg_vote', 'imdb_title_id']].to_dict(orient='records')
    for movie in similar_movies:
        movie['img_src'] = fetch_movie_image(movie['imdb_title_id'])  # Add image URL

    return (similar_movies)

if __name__ == '__main__':
    app.run()
