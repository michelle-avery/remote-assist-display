import logging
import os
import re
from logging.handlers import RotatingFileHandler

from flask import Flask

from .flask_config import Config

class TokenMaskingFilter(logging.Filter):
    # Pattern matches "access_token": "..." or "refresh_token": "..." 
    TOKEN_PATTERN = r'["\']?(access_token|refresh_token)["\']?\s*:\s*["\']([^"\']*)["\']\s*'
    
    def filter(self, record):
        if isinstance(record.msg, str):
            # Replace tokens with a placeholder
            record.msg = re.sub(
                self.TOKEN_PATTERN,
                r'"\1": "[REDACTED]"',
                record.msg
            )
        return True
    
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

    logs_dir = app.config['LOG_DIR']
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
    file_handler.addFilter(TokenMaskingFilter()) 

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    console_handler.setLevel(log_level)
    console_handler.addFilter(TokenMaskingFilter())

    app.logger.setLevel(log_level)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    app.logger.handlers = [file_handler, console_handler]
    app.logger.info("=" * 80)
    app.logger.info(f"Remote Assist Display v{app.config['VERSION']}")
    app.logger.info("-" * 80)
    app.logger.info(f"Unique ID: {app.config['UNIQUE_ID']}")
    app.logger.info(f"Running on Android: {app.config['IS_ANDROID']}")
    app.logger.info(f"Frozen executable: {app.config['IS_FROZEN']}")
    app.logger.info(f"Log dir.: {logs_dir}")
    app.logger.info(f"Config dir.: {app.config['CONFIG_DIR']}")
    app.logger.info("=" * 80)
    gui_dir = os.path.join(os.path.dirname(__file__), "templates")  # development path
    if not os.path.exists(gui_dir):  # frozen executable path
        gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

    app.static_folder = gui_dir
    app.template_folder = gui_dir

    from .routes import register_routes

    register_routes(app)

    return app
