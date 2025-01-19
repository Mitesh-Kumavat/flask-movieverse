from flask import Blueprint, jsonify, request
from database.db_utils import get_db_connection
routes = Blueprint('users', __name__)

@routes.route('/register', methods=['POST'])
def register_user():
    data = request.json
    # Add logic to register a user
    return jsonify({"message": "User registered successfully"}), 201

@routes.route("/users",  methods= ["GET"])
def user():
    return jsonify({"message": "User route setup"}), 200

@routes.route('/login', methods=['POST'])
def login_user():
    data = request.json
    # Add logic for user login
    return jsonify({"message": "User logged in successfully"}), 200
