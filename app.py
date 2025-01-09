from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import sqlite3
import numpy as np

app = Flask(__name__)
CORS(app)
OMDB_API_KEY = os.getenv('OMDB_API_KEY') 
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") 


# Helper function to connect to SQLite
def get_db_connection():
    conn = sqlite3.connect('movies.db')
    conn.row_factory = sqlite3.Row
    return conn

# Helper function to fetch image source from OMDb API
def fetch_movie_image(imdb_id):
    url = f"http://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('Poster', '')
    return ''

# Search for the movie trailer on YouTube using YouTube Data API
def fetch_trailer_link(movie_title):
    search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={movie_title} trailer&key={YOUTUBE_API_KEY}"
    response = requests.get(search_url)
    if response.status_code == 200:
        data = response.json()
        if 'items' in data and len(data['items']) > 0:
            video_id = data['items'][0]['id']['videoId']
            return f"https://www.youtube.com/watch?v={video_id}"
    return None

# Get trailer link using IMDb ID
def get_movie_trailer(title):
    if title:
        trailer_link = fetch_trailer_link(title)
        return trailer_link
    return None

# Fetch top 10 movies by average vote
@app.route('/api/top-movies', methods=['GET'])
def get_top_movies():
    conn = get_db_connection()
    query = "SELECT original_title, year, avg_vote, imdb_title_id FROM movies ORDER BY worlwide_gross_income DESC LIMIT 10"
    movies = conn.execute(query).fetchall()
    conn.close()

    top_movies = [dict(movie) for movie in movies]
    for movie in top_movies:
        movie['img_src'] = fetch_movie_image(movie['imdb_title_id'])
    return jsonify(top_movies)

# Fetch top 10 best-featured movies (e.g., based on votes)
@app.route('/api/featured-movies', methods=['GET'])
def get_top_featured_movies():
    conn = get_db_connection()
    query = "SELECT original_title, year, avg_vote, imdb_title_id FROM movies ORDER BY votes DESC LIMIT 10"
    movies = conn.execute(query).fetchall()
    conn.close()

    top_featured = [dict(movie) for movie in movies]
    for movie in top_featured:
        movie['img_src'] = fetch_movie_image(movie['imdb_title_id'])
    return jsonify(top_featured)

# Fetch movie details by IMDB ID
@app.route('/api/movie/<imdb_id>', methods=['GET'])
def get_movie_details(imdb_id):
    conn = get_db_connection()
    query = "SELECT * FROM movies WHERE imdb_title_id = ?"
    movie = conn.execute(query, (imdb_id,)).fetchone()
    conn.close()

    if not movie:
        return jsonify({"error": "Movie not found"}), 404

    movie_details = dict(movie)
    movie_details['img_src'] = fetch_movie_image(imdb_id)
    title = movie_details['original_title']
    movie_details['trailer_link'] = get_movie_trailer( title)  # Add trailer link
    return jsonify(movie_details)


# Fetch similar movies using cosine similarity
@app.route('/api/movie/<imdb_id>/similar', methods=['GET'])
def get_similar_movies(imdb_id):
    conn = get_db_connection()
    query = '''SELECT imdb_title_id, original_title, year, genre, avg_vote, description, actors, director 
               FROM movies'''
    movies = conn.execute(query).fetchall()
    conn.close()

    # Convert to DataFrame for similarity calculations
    column_names = ['imdb_title_id', 'original_title', 'year', 'genre', 'avg_vote', 'description', 'actors', 'director']
    movies_df = pd.DataFrame(movies, columns=column_names)

    if imdb_id not in movies_df['imdb_title_id'].values:
        return jsonify({"error": "Movie not found"}), 404

    # Precompute TF-IDF matrix for description
    vectorizer = TfidfVectorizer(stop_words='english')
    movies_df['description'] = movies_df['description'].fillna('')
    tfidf_matrix = vectorizer.fit_transform(movies_df['description'])

    # Additional Feature Processing (e.g., genre, actors, director)
    def process_genre(genre):
        return genre.split(',') if genre else []

    movies_df['genre'] = movies_df['genre'].apply(process_genre)

    # Combine TF-IDF with additional features (e.g., genre, actors, director)
    def create_feature_vector(row):
    # Ensure genre is a space-separated string, if it's a list
        genre_str = ' '.join(row['genre']) if isinstance(row['genre'], list) else row['genre']
        
        # Ensure actors and director are strings
        actors_str = str(row['actors']) if row['actors'] else ''
        director_str = str(row['director']) if row['director'] else ''
        
        # Combine all features into one string
        features = ' '.join([genre_str, actors_str, director_str])
        return features

    movies_df['combined_features'] = movies_df.apply(create_feature_vector, axis=1)

    # Recompute TF-IDF matrix for combined features
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix_combined = vectorizer.fit_transform(movies_df['combined_features'])

    # Find similar movies based on combined features and description
    movie_index = movies_df[movies_df['imdb_title_id'] == imdb_id].index[0]
    
    # Compute cosine similarity for both description and combined features
    cosine_sim_description = cosine_similarity(tfidf_matrix[movie_index], tfidf_matrix).flatten()
    cosine_sim_combined = cosine_similarity(tfidf_matrix_combined[movie_index], tfidf_matrix_combined).flatten()

    # Weighting the similarities (adjust the weights as needed)
    similarity_score = 0.7 * cosine_sim_description + 0.3 * cosine_sim_combined

    # Get top 10 most similar movies (excluding the movie itself)
    similar_indices = similarity_score.argsort()[-11:-1][::-1]

    similar_movies = movies_df.iloc[similar_indices][['original_title', 'year', 'avg_vote', 'imdb_title_id', 'genre']].to_dict(orient='records')

    # Add movie images and other details
    for movie in similar_movies:
        try:
            movie['img_src'] = fetch_movie_image(movie['imdb_title_id'])  # Assuming this function is defined elsewhere
        except Exception as e:
            movie['img_src'] = None  # Handle any error gracefully
            print(f"Error fetching image for {movie['imdb_title_id']}: {e}")

    return jsonify(similar_movies)


@app.route('/api/movie/search', methods=['GET'])
def search_movie():
    search_query = request.args.get('search', '')
    
    # If no search query is provided, return an error
    if not search_query:
        return jsonify({"error": "No search query provided"}), 400
    
    # Fetch all movies for comparison
    conn = get_db_connection()
    query = '''SELECT imdb_title_id, original_title, year, avg_vote, description, genre FROM movies'''
    movies = conn.execute(query).fetchall()
    conn.close()

    # Convert to DataFrame for easier processing
    column_names = ['imdb_title_id', 'original_title', 'year', 'avg_vote', 'description', 'genre']
    movies_df = pd.DataFrame(movies, columns=column_names)

    # Preprocess the search query
    search_query = [search_query]  # Wrap it in a list for vectorization

    # Combine movie title, description, and genre into a single string for each movie
    movies_df['combined_features'] = movies_df['original_title'] + ' ' + movies_df['description'] + ' ' + movies_df['genre']
    
    # Initialize TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(stop_words='english')
    
    # Fit and transform the movie data combined features and the search query
    tfidf_matrix = vectorizer.fit_transform(movies_df['combined_features'])
    query_vector = vectorizer.transform(search_query)
    
    # Calculate cosine similarity between the search query and each movie
    cosine_sim = cosine_similarity(query_vector, tfidf_matrix).flatten()

    # Get the indices of the top 10 most similar movies
    top_indices = cosine_sim.argsort()[-10:][::-1]

    # Get the top 10 most similar movies
    top_movies = movies_df.iloc[top_indices][['imdb_title_id', 'original_title', 'year', 'avg_vote', 'description', 'genre']].to_dict(orient='records')

    # Add movie images and other details to the response
    for movie in top_movies:
        movie['img_src'] = fetch_movie_image(movie['imdb_title_id'])  # Assuming fetch_movie_image is already defined

    return jsonify(top_movies), 200

if __name__ == '__main__':
    app.run()
