from flask import Blueprint, jsonify, request
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from database.db_utils import get_db_connection
import json

routes = Blueprint('users', __name__)

@routes.route('/register', methods=['POST'])
def register_user():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not all([name, email, password]):
        return jsonify({"error": "All fields are required."}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', 
                     (name, email, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists."}), 409
    finally:
        conn.close()

    return jsonify({"message": "User registered successfully."}), 201

@routes.route('/login', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"error": "Email and password are required."}), 400

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user['password'], password):
        return jsonify({"error": "Invalid email or password."}), 401

    return jsonify({"message": "Login successful.", "userId": user['userId']}), 200

@routes.route('/<int:user_id>/watchlist', methods=['POST'])
def add_to_watchlist(user_id):
    data = request.json
    movie = {
        "movieName": data.get('movieName'),
        "movieImdbId": data.get('movieImdbId'),
        "imgPoster": data.get('imgPoster')
    }

    conn = get_db_connection()
    user = conn.execute('SELECT watchlist FROM users WHERE userId = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "User not found."}), 404

    watchlist = json.loads(user['watchlist'])
    watchlist.append(movie)

    conn.execute('UPDATE users SET watchlist = ? WHERE userId = ?', 
                 (json.dumps(watchlist), user_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Movie added to watchlist."}), 200

@routes.route('/<int:user_id>/favorites', methods=['POST'])
def add_to_favorites(user_id):
    data = request.json
    movie = {
        "movieName": data.get('movieName'),
        "movieImdbId": data.get('movieImdbId'),
        "imgPoster": data.get('imgPoster')
    }

    conn = get_db_connection()
    user = conn.execute('SELECT favorites FROM users WHERE userId = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "User not found."}), 404

    favorites = json.loads(user['favorites'])
    favorites.append(movie)

    conn.execute('UPDATE users SET favorites = ? WHERE userId = ?', 
                 (json.dumps(favorites), user_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Movie added to favorites."}), 200

@routes.route('/<int:user_id>', methods=['GET'])
def get_user_details(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE userId = ?', (user_id,)).fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "User not found."}), 404

    user_details = {
        "userId": user['userId'],
        "name": user['name'],
        "email": user['email'],
        "watchlist": json.loads(user['watchlist']),
        "favorites": json.loads(user['favorites'])
    }

    return jsonify(user_details), 200
