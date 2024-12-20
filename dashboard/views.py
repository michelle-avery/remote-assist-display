from . import bp
from flask import current_app, render_template
from functools import partial
import webview
import asyncio
import json
from hass_client import HomeAssistantClient
from remote_display.websocket_helper import WebSocketHelper

from .navigate import load_card, load_dashboard

@bp.route("/", methods=["GET"])
def dashboard():
    return render_template("dashboard.html")

@bp.route("/listen", methods=["POST"])
async def listen():
    url = current_app.config["url"]
    dashboard = current_app.config["default_dashboard"]
    load_dashboard(f"{url}/{dashboard}")

    websocket_helper = WebSocketHelper(url=url, retry_limit=current_app.config.get("TOKEN_RETRY_LIMIT"))

    await websocket_helper.connect_client()
    listener_task = asyncio.create_task(websocket_helper.client.start_listening())
    callback = partial(load_card, expire_time=current_app.config.get("DEFAULT_DASHBOARD_TIMEOUT"))
    await websocket_helper.subscribe_events(callback, current_app.config.get("EVENT_TYPE"), )
    await listener_task
    return "Listening for events..."

