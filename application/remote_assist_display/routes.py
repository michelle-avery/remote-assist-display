from http import HTTPStatus

from flask import current_app, redirect, render_template, request, url_for

from .auth import fetch_access_token
from .config_handler import get_saved_config, save_to_config

# from .websocket_manager import WebSocketManager
from .ha_websocket_manager import WebSocketManager
from .navigate import load_dashboard

CONFIG_FILE = "config.ini"


def register_routes(app):
    @app.route("/", methods=["GET"])
    async def config():
        saved_config = get_saved_config(current_app.config["CONFIG_DIR"])
        if "HomeAssistant" in saved_config:
            current_app.logger.debug("Found existing config file")
            current_app.config["url"] = saved_config.get(
                "HomeAssistant", "url", fallback=None
            )
            current_app.logger.debug(f"Found configured URL: {current_app.config['url']}")
            if current_app.config["url"]:
                # Todo: handle cases where we have a saved url, but no valid credentials
                current_app.logger.debug("Redirecting to waiting page")
                return redirect(url_for("waiting"))
        current_app.logger.debug("No existing config file found, redirecting to login")
        return redirect(url_for("hass_login"))

    @app.route("/hass-login", methods=["GET"])
    def hass_login():
        return render_template("login.html")

    def save_url(url):
        save_to_config("HomeAssistant", "url", url, current_app.config["CONFIG_DIR"])
        current_app.logger.debug(f"Saved URL to config file: {url}")
        # Also save the URL on the Server object
        current_app.config["url"] = url

    @app.route("/connect", methods=["POST"])
    async def connect():
        url = request.form.get("haUrl")
        # Since we won't have settings from the server yet, we can't set the 
        # device name in localStorage.
        current_app.logger.debug(f"Getting credentials from Home Assistant at {url}")
        await load_dashboard(url, local_storage=False)
        try:
            retries = current_app.config.get(
                "TOKEN_RETRY_LIMIT", 5
            ) 
            await fetch_access_token(
                url=url,
                retries=retries,
                delay=10,
                app=current_app,
            )
            # Save the URL to our config file
            save_url(url)
            current_app.logger.debug("Redirecting to waiting page")
            await load_dashboard(url_for("waiting"), local_storage=False)
            return "", HTTPStatus.OK

        except Exception as e:
            return {"error": str(e)}, 500

    @app.route("/waiting", methods=["GET"])
    def waiting():
        return render_template("waiting.html")

    @app.route("/hass-config", methods=["POST"])
    def hassconfig():
        if "url" not in current_app.config:
            return {"error": "Missing Home Assistant URL"}, HTTPStatus.BAD_REQUEST

        try:
            manager = WebSocketManager.get_instance(current_app)
            manager.initialize(current_app.config["url"])
            return "", HTTPStatus.OK
        except Exception as e:
            current_app.logger.error(
                f"Failed to configure Home Assistant: {str(e)}", exc_info=True
            )
            return {"error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
