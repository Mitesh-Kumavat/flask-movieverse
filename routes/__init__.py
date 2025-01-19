from routes.movies import routes as movie_routes
from routes.users import routes as user_routes

def register_routes(app):
    app.register_blueprint(movie_routes, url_prefix='/api')
    app.register_blueprint(user_routes, url_prefix='/api')
