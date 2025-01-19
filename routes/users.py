from flask import Blueprint, jsonify, request
import sqlite3
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

@routes.route('/user/<int:user_id>/watchlist', methods=['GET'])
def get_watchlist(user_id):
    conn = get_db_connection()
    movies = conn.execute(
        "SELECT movieName, movieImdbId, movieImg FROM watchlist WHERE userId = ?",
        (user_id,)
    ).fetchall()
    conn.close()

    return jsonify([dict(movie) for movie in movies]), 200


@routes.route('/user/<int:user_id>/watchlist', methods=['POST'])
def toggle_watchlist(user_id):
    data = request.json
    movie_name = data.get('movieName')
    movie_imdb_id = data.get('movieImdbId')
    movie_img = data.get('movieImg')

    if not movie_name or not movie_imdb_id or not movie_img:
        return jsonify({"error": "All movie fields are required"}), 400

    conn = get_db_connection()
    movie = conn.execute(
        "SELECT * FROM watchlist WHERE userId = ? AND movieImdbId = ?",
        (user_id, movie_imdb_id)
    ).fetchone()

    if movie:
        # Remove movie from watchlist
        conn.execute(
            "DELETE FROM watchlist WHERE userId = ? AND movieImdbId = ?",
            (user_id, movie_imdb_id)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Movie removed from watchlist"}), 200
    else:
        # Add movie to watchlist
        conn.execute(
            "INSERT INTO watchlist (userId, movieName, movieImdbId, movieImg) VALUES (?, ?, ?, ?)",
            (user_id, movie_name, movie_imdb_id, movie_img)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Movie added to watchlist"}), 201
    
@routes.route("/user/<int:user_id>", methods=['GET'])
def get_user_details(user_id):
    conn = get_db_connection()

    # Fetch user details from the users table
    user = conn.execute("SELECT userId, username, email FROM users WHERE userId = ?", (user_id,)).fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    # Fetch the user's watchlist from the watchlist table
    watchlist = conn.execute("""
        SELECT movieName, movieImdbId, movieImg
        FROM watchlist
        WHERE userId = ?
    """, (user_id,)).fetchall()

    conn.close()

    # Prepare the response data
    user_details = {
        "userId": user["userId"],
        "username": user["username"],
        "email": user["email"],
        "watchlist": [
            {
                "movieName": movie["movieName"],
                "movieImdbId": movie["movieImdbId"],
                "movieImg": movie["movieImg"]
            }
            for movie in watchlist
        ]
    }

    return jsonify(user_details), 200
