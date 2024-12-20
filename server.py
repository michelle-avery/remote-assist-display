import os
from flask import Flask

from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    gui_dir = os.path.join(os.path.dirname(__file__), 'templates')  # development path
    if not os.path.exists(gui_dir): # frozen executable path
        gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gui')

    app.static_folder = gui_dir
    app.template_folder = gui_dir

    from remote_display import bp as app_bp
    app.register_blueprint(app_bp)
    from config import bp as config_bp
    app.register_blueprint(config_bp)
    from dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)

    return app
