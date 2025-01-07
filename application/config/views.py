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
        current_app.config["assist_entity"] = saved_config.get("HomeAssistant", "assist_entity", fallback=None)
        current_app.config["default_dashboard"] = saved_config.get("HomeAssistant", "default_dashboard_path", fallback=None)
        current_app.config["url"] = saved_config.get("HomeAssistant", "url", fallback=None)
        current_app.config["device_name"] = saved_config.get("Remote Assist Display", "device_name", fallback=None)
        if current_app.config["assist_entity"] and current_app.config["default_dashboard"] and current_app.config["device_name"]:
            return redirect(url_for("dashboard.dashboard"))
        else:
            # Get a list of voice assistants from the API
            websocket_helper = WebSocketHelper(url=current_app.config.get("url"), retry_limit=current_app.config.get("TOKEN_RETRY_LIMIT"))
            await websocket_helper.connect_client()
            asyncio.create_task(websocket_helper.client.start_listening())
            voice_assistants = await websocket_helper.send_command("assist_pipeline/device/list")
            return render_template("config.html", voice_assistants=voice_assistants)
    return redirect(url_for("config.hass_login"))

@bp.route("/save", methods=["POST"])
def save_config():
    assist_entity = request.form.get("assistEntity")
    default_dashboard = request.form.get("defaultDashboard")
    device_name = request.form.get("deviceName")
    save_to_config("HomeAssistant", "assist_entity", assist_entity)
    save_to_config("HomeAssistant", "default_dashboard_path", default_dashboard)
    save_to_config("Remote Assist Display", "device_name", device_name)

    # Also set the values on the server object so they can be accessed later
    current_app.config["assist_entity"] = assist_entity
    current_app.config["default_dashboard"] = default_dashboard
    current_app.config["device_name"] = device_name

    return redirect(url_for("dashboard.dashboard"))

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
