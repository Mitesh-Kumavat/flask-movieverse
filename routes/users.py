from flask import Blueprint, jsonify, request
import sqlite3
from DataStrucure.queue import Queue
from werkzeug.security import generate_password_hash, check_password_hash
from database.db_utils import get_db_connection

routes = Blueprint('users', __name__)
@routes.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Username or email already exists"}), 400

    conn.close()
    return jsonify({"message": "User registered successfully"}), 201

@routes.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user['password'], password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"message": "Login successful", "userId": user['userId']}), 200

user_queues = {}

@routes.route('/user/<int:user_id>/watchlist', methods=['GET'])
def get_watchlist(user_id):
    if user_id not in user_queues:
        user_queues[user_id] = Queue()

    watchlist_queue = user_queues[user_id]
    watchlist_items = watchlist_queue.get_all()

    return jsonify(watchlist_items), 200

@routes.route('/user/<int:user_id>/watchlist', methods=['POST'])
def toggle_watchlist(user_id):
    data = request.json
    movie_id = data.get('movieId')

    if not movie_id:
        return jsonify({"error": "Movie ID is required"}), 400

    conn = get_db_connection()

    movie_details = conn.execute(
        "SELECT original_title, imdb_title_id, img FROM movies WHERE imdb_title_id = ?",
        (movie_id,)
    ).fetchone()

    if not movie_details:
        conn.close()
        return jsonify({"error": "Movie not found"}), 404

    if user_id not in user_queues:
        user_queues[user_id] = Queue()

    watchlist_queue = user_queues[user_id]

    existing_movies = [movie for movie in watchlist_queue.get_all() if movie["imdb_title_id"] == movie_details["imdb_title_id"]]

    if existing_movies:
        watchlist_queue.items = [movie for movie in watchlist_queue.items if movie["imdb_title_id"] != movie_details["imdb_title_id"]]
        conn.execute(
            "DELETE FROM watchlist WHERE userId = ? AND movieImdbId = ?",
            (user_id, movie_details['imdb_title_id'])
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Movie removed from watchlist"}), 200
    else:
        movie_entry = {
            "original_title": movie_details["original_title"],
            "imdb_title_id": movie_details["imdb_title_id"],
            "img": movie_details["img"]
        }
        watchlist_queue.enqueue(movie_entry)

        conn.execute(
            "INSERT INTO watchlist (userId, movieName, movieImdbId, movieImg) VALUES (?, ?, ?, ?)",
            (user_id, movie_details['original_title'], movie_details['imdb_title_id'], movie_details['img'])
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Movie added to watchlist"}), 201
  
  
    
@routes.route("/user/<int:user_id>", methods=['GET'])
def get_user_details(user_id):
    conn = get_db_connection()

    user = conn.execute("SELECT userId, username, email FROM users WHERE userId = ?", (user_id,)).fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    watchlist = conn.execute("""
        SELECT movieName, movieImdbId, movieImg
        FROM watchlist
        WHERE userId = ?
    """, (user_id,)).fetchall()

    conn.close()

    user_details = {
        "userId": user["userId"],
        "username": user["username"],
        "email": user["email"],
        "watchlist": [
            {
                "original_title": movie["movieName"],
                "imdb_title_id": movie["movieImdbId"],
                "img": movie["movieImg"]
            }
            for movie in watchlist
        ]
    }

    return jsonify(user_details), 200
