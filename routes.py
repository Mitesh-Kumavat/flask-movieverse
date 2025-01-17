from flask import Blueprint, jsonify, request
import pandas as pd
from utils import (
    get_db_connection,
    get_movie_trailer,
    calculate_similarity
)

routes = Blueprint('routes', __name__)

@routes.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "Server is alive"}), 200

@routes.route('/api/top-movies', methods=['GET'])
def get_top_movies():
    conn = get_db_connection()
    query = "SELECT original_title, year, avg_vote, imdb_title_id FROM movies ORDER BY worlwide_gross_income DESC LIMIT 15"
    movies = conn.execute(query).fetchall()
    conn.close()

    top_movies = [dict(movie) for movie in movies]
    return jsonify(top_movies)

@routes.route('/api/featured-movies', methods=['GET'])
def get_top_featured_movies():
    conn = get_db_connection()
    query = "SELECT original_title, year, avg_vote, imdb_title_id FROM movies ORDER BY votes DESC LIMIT 15"
    movies = conn.execute(query).fetchall()
    conn.close()

    top_featured = [dict(movie) for movie in movies]
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
    title = movie_details['original_title']
    movie_details['trailer_link'] = get_movie_trailer(title)
    return jsonify(movie_details)

@routes.route('/api/movie/search', methods=['GET'])
def search_movie():
    search_query = request.args.get('search', '').strip()

    if not search_query:
        return jsonify({"error": "No search query provided"}), 400

    conn = get_db_connection()

    query = """
    SELECT imdb_title_id, original_title, year, avg_vote, description, genre
    FROM movies
    WHERE description LIKE ? OR genre LIKE ? OR original_title LIKE ?
    LIMIT 15
    """
    like_query = f"%{search_query}%"
    movies = conn.execute(query, (like_query, like_query, like_query)).fetchall()
    conn.close()

    if not movies:
        return jsonify({"message": "No movies found"}), 200

    # Map results to a list of dictionaries
    search_results = [dict(movie) for movie in movies]
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

@routes.route('/api/movies/filter', methods=['GET'])
def filter_and_sort_movies():
    """
    Optimized API to filter and sort movies based on genres, languages, release years, ratings, and more.
    """
    import time

    # Start timer
    start_time = time.time()

    # Get query parameters
    genre = request.args.get('genre', '').lower()
    language = request.args.get('language', '').lower()
    min_year = request.args.get('min_year', None, type=int)
    max_year = request.args.get('max_year', None, type=int)
    min_rating = request.args.get('min_rating', None, type=float)
    max_rating = request.args.get('max_rating', None, type=float)
    sort_by = request.args.get('sort_by', 'avg_vote')  # Default sorting by rating
    order = request.args.get('order', 'desc').lower()  # Default order descending
    limit = int(request.args.get('limit', 20))  # Default limit
    offset = int(request.args.get('offset', 0))  # Default offset

    # Connect to the database
    conn = get_db_connection()
    try:
        query = """
            SELECT imdb_title_id, original_title, year, avg_vote, description, genre, language_1 
            FROM movies
            WHERE 
                (:genre IS NULL OR LOWER(genre) LIKE '%' || :genre || '%') AND
                (:language IS NULL OR LOWER(language_1) LIKE '%' || :language || '%') AND
                (:min_year IS NULL OR year >= :min_year) AND
                (:max_year IS NULL OR year <= :max_year) AND
                (:min_rating IS NULL OR avg_vote >= :min_rating) AND
                (:max_rating IS NULL OR avg_vote <= :max_rating)
            ORDER BY {sort_by} {order}
            LIMIT :limit OFFSET :offset
        """.format(sort_by=sort_by, order=order)

        movies = conn.execute(query, {
            'genre': genre if genre else None,
            'language': language if language else None,
            'min_year': min_year,
            'max_year': max_year,
            'min_rating': min_rating,
            'max_rating': max_rating,
            'limit': limit,
            'offset': offset
        }).fetchall()
    except Exception as e:
        conn.close()
        return jsonify({"error": "Query execution failed", "details": str(e)}), 500

    conn.close()

    # Convert to JSON
    column_names = ['imdb_title_id', 'original_title', 'year', 'avg_vote', 'description', 'genre', 'language_1']
    filtered_movies = [dict(zip(column_names, movie)) for movie in movies]

    # Add execution time to response
    execution_time = time.time() - start_time
    return jsonify({"movies": filtered_movies, "execution_time": execution_time}), 200

# Register routes
def register_routes(app):
    app.register_blueprint(routes)
