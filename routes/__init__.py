from flask import Flask

from .teams import teams
from .auth import auth
from .content import content
from .stats import stats
from .scout import scout

def create_app():
    app = Flask(__name__, static_folder="../static")

    # API Routes
    app.register_blueprint(auth, url_prefix="/api")
    app.register_blueprint(teams, url_prefix="/api/teams")
    app.register_blueprint(stats, url_prefix="/api/stats")

    # Content Routes
    app.register_blueprint(content, url_prefix="/")
    app.register_blueprint(scout, url_prefix="/scout")

    return app