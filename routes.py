from flask import Blueprint, jsonify, request
import pandas as pd
from utils import (
    get_db_connection,
    get_movie_image,
    get_movie_trailer,
    calculate_similarity
)

routes = Blueprint('routes', __name__)

@routes.route('/api/top-movies', methods=['GET'])
def get_top_movies():
    conn = get_db_connection()
    query = "SELECT original_title, year, avg_vote, imdb_title_id FROM movies ORDER BY worlwide_gross_income DESC LIMIT 10"
    movies = conn.execute(query).fetchall()
    conn.close()

    top_movies = [dict(movie) for movie in movies]
    for movie in top_movies:
        movie['img_src'] = get_movie_image(movie['imdb_title_id'])
    return jsonify(top_movies)

@routes.route('/api/featured-movies', methods=['GET'])
def get_top_featured_movies():
    conn = get_db_connection()
    query = "SELECT original_title, year, avg_vote, imdb_title_id FROM movies ORDER BY votes DESC LIMIT 10"
    movies = conn.execute(query).fetchall()
    conn.close()

    top_featured = [dict(movie) for movie in movies]
    for movie in top_featured:
        movie['img_src'] = get_movie_image(movie['imdb_title_id'])
    return jsonify(top_featured)

@routes.route('/api/movie/<imdb_id>', methods=['GET'])
def get_movie_details(imdb_id):
    conn = get_db_connection()
    query = "SELECT * FROM movies WHERE imdb_title_id = ?"
    movie = conn.execute(query, (imdb_id,)).fetchone()
    conn.close()

    if not movie:
        return jsonify({"error": "Movie not found"}), 404

    movie_details = dict(movie)
    movie_details['img_src'] = get_movie_image(imdb_id)
    title = movie_details['original_title']
    movie_details['trailer_link'] = get_movie_trailer(title)
    return jsonify(movie_details)

@routes.route('/api/movie/search', methods=['GET'])
def search_movie():
    search_query = request.args.get('search', '').strip()

    if not search_query:
        return jsonify({"error": "No search query provided"}), 400

    conn = get_db_connection()

    # Use SQL LIKE or full-text search for filtering
    query = """
    SELECT imdb_title_id, original_title, year, avg_vote, description, genre
    FROM movies
    WHERE description LIKE ? OR genre LIKE ? OR original_title LIKE ?
    LIMIT 12
    """
    like_query = f"%{search_query}%"
    movies = conn.execute(query, (like_query, like_query, like_query)).fetchall()
    conn.close()

    if not movies:
        return jsonify({"message": "No movies found"}), 200

    # Map results to a list of dictionaries
    search_results = []
    for movie in movies:
        movie_dict = dict(movie)
        movie_dict['img_src'] = get_movie_image(movie['imdb_title_id'])
        search_results.append(movie_dict)

    return jsonify(search_results), 200


@routes.route('/api/movie/<imdb_id>/similar', methods=['GET'])
def get_similar_movies(imdb_id):
    conn = get_db_connection()
    query = "SELECT imdb_title_id, original_title, year, avg_vote, description, genre FROM movies"
    movies = conn.execute(query).fetchall()
    conn.close()

    if not movies:
        return jsonify({"error": "No movies found"}), 404

    column_names = ['imdb_title_id', 'original_title', 'year', 'avg_vote', 'description', 'genre']
    movies_df = pd.DataFrame(movies, columns=column_names)

    # Fetch details of the movie to find similar ones
    movie = movies_df[movies_df['imdb_title_id'] == imdb_id]
    if movie.empty:
        return jsonify({"error": "Movie not found"}), 404

    # Calculate similarity based on combined features
    movie_features = movie.iloc[0]['description'] + ' ' + movie.iloc[0]['genre']
    movies_df['combined_features'] = movies_df['description'] + ' ' + movies_df['genre']
    similar_movies = calculate_similarity(movie_features, movies_df)

    # Exclude the original movie from the results
    similar_movies = [movie for movie in similar_movies if movie['imdb_title_id'] != imdb_id]
    return jsonify(similar_movies), 200


# Register routes
def register_routes(app):
    app.register_blueprint(routes)
