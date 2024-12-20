from . import bp
from flask import current_app, render_template
from functools import partial
import webview
import asyncio
import json
from hass_client import HomeAssistantClient

from .navigate import load_card, load_dashboard

@bp.route("/", methods=["GET"])
def dashboard():
    return render_template("dashboard.html")

@bp.route("/listen", methods=["POST"])
async def listen():
    url = current_app.config["url"]
    dashboard = current_app.config["default_dashboard"]
    load_dashboard(f"{url}/{dashboard}")
    retry_limit = current_app.config.get("TOKEN_RETRY_LIMIT")
    for _ in range(retry_limit):
        token = webview.windows[0].evaluate_js("""
                    localStorage.getItem("hassTokens")
                """)
        if token:
            break
        await asyncio.sleep(1)
    if not token:
        raise Exception("Unable to fetch token from localStorage")
    access_token = json.loads(token)["access_token"]
    ws_url = url.replace("http", "ws")
    ws_url = f"{ws_url}/api/websocket"
    client = HomeAssistantClient(ws_url, access_token)
    await client.connect()
    listener_task = asyncio.create_task(client.start_listening())
    callback = partial(load_card, expire_time=current_app.config.get("DEFAULT_DASHBOARD_TIMEOUT"))
    await client.subscribe_events(callback, current_app.config.get("EVENT_TYPE"), )
    await listener_task
    return "Listening for events..."

