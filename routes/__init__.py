from flask import Flask

from .teams import teams
from .auth import auth

def create_app():
    app = Flask(__name__)

    # Register Blueprints
    app.register_blueprint(auth, url_prefix='/api')
    app.register_blueprint(teams, url_prefix='/api/teams')

    return app