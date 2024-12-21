import threading

import webview
from flask import current_app

load_card_timer = None

def load_card(event, expire_time=None):
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
        load_dashboard(new_url)
        # Cancel the timer if it's already running
        if load_card_timer:
            load_card_timer.cancel()
        # Start a new timer
        if expire_time:
            load_card_timer = threading.Timer(expire_time, load_dashboard, args=[default_dashboard_url])
            load_card_timer.start()


def load_dashboard(url):
    webview.windows[0].load_url(url)

def set_local_storage():
    key = current_app.config["DEVICE_NAME_KEY"]
    value = current_app.config["device_name"]
    webview.windows[0].evaluate_js(f"""
        localStorage.setItem("{key}", "{value}")
    """)
