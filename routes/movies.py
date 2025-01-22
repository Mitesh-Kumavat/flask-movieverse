from flask import Blueprint, jsonify, request
from database.db_utils import get_db_connection
import pandas as pd
from util.utils import (
    get_movie_trailer,
    calculate_similarity
)

routes = Blueprint('routes', __name__)

@routes.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "Server is alive"}), 200

@routes.route('/top-movies', methods=['GET'])
def get_top_movies():
    conn = get_db_connection()
    query = "SELECT original_title, year, img, avg_vote, imdb_title_id FROM movies ORDER BY worlwide_gross_income DESC LIMIT 20"
    movies = conn.execute(query).fetchall()
    conn.close()

    top_movies = [dict(movie) for movie in movies]
    return jsonify(top_movies)

@routes.route('/featured-movies', methods=['GET'])
def get_top_featured_movies():
    conn = get_db_connection()
    query = "SELECT original_title, year, avg_vote, img, imdb_title_id FROM movies ORDER BY votes DESC LIMIT 20"
    movies = conn.execute(query).fetchall()
    conn.close()

    top_featured = [dict(movie) for movie in movies]
    return jsonify(top_featured)

@routes.route('/movie/<imdb_id>', methods=['GET'])
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

@routes.route('/movie/search', methods=['GET'])
def search_movie():
    search_query = request.args.get('search', '').strip()

    if not search_query:
        return jsonify({"error": "No search query provided"}), 400

    conn = get_db_connection()

    query = """
    SELECT imdb_title_id, original_title, img, year, avg_vote, description, genre
    FROM movies
    WHERE genre LIKE ? OR original_title LIKE ?
    """
    like_query = f"%{search_query}%"
    movies = conn.execute(query, (like_query, like_query)).fetchall()
    conn.close()

    if not movies:
        return jsonify({"message": "No movies found"}), 200

    
    search_results = [dict(movie) for movie in movies]
    return jsonify(search_results), 200

@routes.route('/movie/<imdb_id>/similar', methods=['GET'])
def get_similar_movies(imdb_id):
    conn = get_db_connection()
    query = "SELECT imdb_title_id, original_title, img, year, avg_vote, description, genre FROM movies"
    movies = conn.execute(query).fetchall()
    conn.close()

    if not movies:
        return jsonify({"error": "No movies found"}), 404

    column_names = ['imdb_title_id', 'original_title','img', 'year', 'avg_vote', 'description', 'genre' ]
    movies_df = pd.DataFrame(movies, columns=column_names)
    
    movie = movies_df[movies_df['imdb_title_id'] == imdb_id]
    if movie.empty:
        return jsonify({"error": "Movie not found"}), 404

    movie_features = movie.iloc[0]['description'] + ' ' + movie.iloc[0]['genre']
    movies_df['combined_features'] = movies_df['description'] + ' ' + movies_df['genre']
    similar_movies = calculate_similarity(movie_features, movies_df)
 
    similar_movies = [movie for movie in similar_movies if movie['imdb_title_id'] != imdb_id]
    return jsonify(similar_movies), 200

@routes.route('/movies/filter', methods=['GET'])
def filter_and_sort_movies():
    genre = request.args.get('genre', '').lower()
    language = request.args.get('language', '').lower()
    min_year = request.args.get('min_year', None, type=int)
    max_year = request.args.get('max_year', None, type=int)
    min_rating = request.args.get('min_rating', None, type=float)
    max_rating = request.args.get('max_rating', None, type=float)
    sort_by = request.args.get('sort_by', 'avg_vote')  
    order = request.args.get('order', 'desc').lower()  
    limit = int(request.args.get('limit', 20))  
    offset = int(request.args.get('offset', 0))  

    conn = get_db_connection()
    try:
        query = """
            SELECT imdb_title_id,img, original_title, year, avg_vote, description, genre, language_1 
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
    
    column_names = ['imdb_title_id','img', 'original_title', 'year', 'avg_vote', 'description', 'genre', 'language_1']
    filtered_movies = [dict(zip(column_names, movie)) for movie in movies]

    return jsonify({"movies": filtered_movies}), 200

def register_routes(app):
    app.register_blueprint(routes)
