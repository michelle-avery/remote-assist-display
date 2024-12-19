from . import bp
from flask import current_app, render_template
import webview
import asyncio
import json
import threading
from hass_client import HomeAssistantClient

load_card_timer = None

@bp.route("/", methods=["GET"])
def dashboard():
    return render_template("dashboard.html")

@bp.route("/listen", methods=["POST"])
async def listen():
    url = current_app.config["url"]
    dashboard = current_app.config["default_dashboard"]
    webview.windows[0].load_url(f"{url}/{dashboard}")
    retry_limit = 10
    for _ in range(retry_limit):
        token = webview.windows[0].evaluate_js("""
                    localStorage.getItem('hassTokens')
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
    await client.subscribe_events(load_card, "custom_conversation_conversation_ended")
    await listener_task
    return "Listening for events..."

def load_card(event):
    global load_card_timer
    card_url = event.get("data", {}).get("result", {}).get("response", {}).get("card", {}).get("dashboard", {}).get("title")
    device_id = event.get("data", {}).get("device_id")
    entity_id = current_app.config["assist_entity"]
    hass_url = current_app.config["url"]

    if device_id != entity_id:
        return
    if card_url:
        new_url = f"{hass_url}/{card_url}"
        default_dashboard_url = f"{hass_url}/{current_app.config.get('default_dashboard')}"
        webview.windows[0].load_url(new_url)
        # Cancel the timer if it's already running
        if load_card_timer:
            load_card_timer.cancel()
        # Start a new timer
        load_card_timer = threading.Timer(30, load_dashboard, args=[default_dashboard_url])
        load_card_timer.start()

def load_dashboard(url):
    print(f"Loading dashboard: {url}")
    webview.windows[0].load_url(url)
