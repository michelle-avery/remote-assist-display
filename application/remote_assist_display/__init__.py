import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask

from .flask_config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.debug = app.config['FLASK_DEBUG']

    # Changing environment variables on andoroid is challenging, and we definitely
    # want to see debug logs on android, so we'll set the log level to DEBUG
    # if we are running on android.
    if app.config['IS_ANDROID']:
        app.config['LOG_LEVEL'] = 'DEBUG'
    log_level = getattr(logging, app.config['LOG_LEVEL'])
    
    logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'remote_assist_display.log'),
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    file_handler.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    console_handler.setLevel(log_level)

    app.logger.setLevel(log_level)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    app.logger.handlers = [file_handler, console_handler]
    app.logger.info(f"Starting Remote Assist Display version {app.config['VERSION']}")
    gui_dir = os.path.join(os.path.dirname(__file__), "templates")  # development path
    if not os.path.exists(gui_dir):  # frozen executable path
        gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

    app.static_folder = gui_dir
    app.template_folder = gui_dir

    from .routes import register_routes

    register_routes(app)

    return app
