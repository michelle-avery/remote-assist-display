import asyncio

from . import bp
from dashboard.navigate import load_dashboard
from flask import render_template, request, redirect, url_for, current_app
from .config_handler import get_saved_config, save_to_config
from remote_display.websocket_helper import WebSocketHelper

CONFIG_FILE = "config.ini"


@bp.route("/", methods=["GET"])
async def config():
    saved_config = get_saved_config()
    if "HomeAssistant" in saved_config:
        current_app.config["url"] = saved_config.get("HomeAssistant", "url", fallback=None)
        if current_app.config["url"]:
            return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("config.hass_login"))


@bp.route("/hass-login", methods=["GET"])
def hass_login():
    return render_template("login.html")

def save_url(url):
    save_to_config("HomeAssistant", "url", url)

    # Also save the URL on the Server object
    current_app.config["url"] = url

@bp.route("/connect", methods=["POST"])
async def connect():

    url = request.form.get("haUrl")

    load_dashboard(url)
    websocket_helper = WebSocketHelper(url=url, retry_limit=current_app.config.get("TOKEN_RETRY_LIMIT"))

    try:
        await websocket_helper.fetch_access_token()
        save_url(url)
        load_dashboard(url_for("config.config"))

    except Exception as e:
        return {"error": str(e)}, 500
