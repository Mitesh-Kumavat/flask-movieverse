from flask import Flask
from flask_cors import CORS
from routes import register_routes
import threading
import time
import requests

app = Flask(__name__)
CORS(app)

# Register routes
register_routes(app)

def keep_server_awake():
    while True:
        try:
            server_url = "https://flask-movieverse.onrender.com/api/ping"
            response = requests.get(server_url)
            print(f"Pinged server: {response.status_code}")
        except Exception as e:
            print(f"Error pinging server: {e}")
        time.sleep(60)

def start_background_thread():
    thread = threading.Thread(target=keep_server_awake, daemon=True)
    thread.start()

if __name__ == '__main__':
    start_background_thread()
    app.run()