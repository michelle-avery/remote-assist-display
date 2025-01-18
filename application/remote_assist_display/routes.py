from flask import render_template, request, redirect, url_for, current_app
from http import HTTPStatus
from .websocket_manager import WebSocketManager
from .config_handler import get_saved_config, save_to_config
from .auth import fetch_access_token
from .navigate import load_dashboard


CONFIG_FILE = "config.ini"


def register_routes(app):

    @app.route("/", methods=["GET"])
    async def config():
        saved_config = get_saved_config()
        if "HomeAssistant" in saved_config:
            current_app.config["url"] = saved_config.get("HomeAssistant", "url", fallback=None)
            if current_app.config["url"]:
                # Todo: handle cases where we have a saved url, but no valid credentials
                return redirect(url_for("waiting"))
        return redirect(url_for("hass_login"))



    @app.route("/hass-login", methods=["GET"])
    def hass_login():
        return render_template("login.html")

    def save_url(url):
        save_to_config("HomeAssistant", "url", url)

        # Also save the URL on the Server object
        current_app.config["url"] = url

    @app.route("/connect", methods=["POST"])
    async def connect():

        url = request.form.get("haUrl")
        load_dashboard(url)
        try:
            await fetch_access_token(url=url, retries=current_app.config.get("TOKEN_RETRY_LIMIT"), app=current_app)
            # Save the URL to our config file
            save_url(url)
            load_dashboard(url_for('waiting'))
            return "", HTTPStatus.OK

        except Exception as e:
            return {"error": str(e)}, 500

    @app.route("/waiting", methods=["GET"])
    def waiting():
        return render_template("waiting.html")

    @app.route("/hass-config", methods=["POST"])
    async def hassconfig():
        manager = WebSocketManager.get_instance(current_app)
        await manager.initialize(current_app.config["url"])
        return "", HTTPStatus.OK