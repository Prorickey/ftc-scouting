from flask import Flask

from .teams import teams
from .auth import auth
from .stats import stats

def create_app():
    app = Flask(__name__)

    # Register Blueprints
    app.register_blueprint(auth, url_prefix='/api')
    app.register_blueprint(teams, url_prefix='/api/teams')
    app.register_blueprint(stats, url_prefix="/api/stats")

    return app