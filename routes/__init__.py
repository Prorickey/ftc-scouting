from flask import Flask

from .teams import teams
from .auth import auth
from .content import content

def create_app():
    app = Flask(__name__, static_folder="../static")

    # API Routes
    app.register_blueprint(auth, url_prefix='/api')
    app.register_blueprint(teams, url_prefix='/api/teams')

    # Content Routes
    app.register_blueprint(content, url_prefix="/")

    return app