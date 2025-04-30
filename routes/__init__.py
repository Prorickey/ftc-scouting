from flask import Flask
from .auth import auth

def create_app():
    app = Flask(__name__)

    # Register Blueprints
    app.register_blueprint(auth, url_prefix='/api')

    return app