import webview
import websockets
import configparser
import json
import os
import time
import asyncio
from hass_client import HomeAssistantClient
import threading

CONFIG_FILE = "config.ini"

class HomeAssistantClient:
    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.event_callback = None

    async def connect(self):
        async with websockets.connect(self.url) as websocket:
            await websocket.send(json.dumps({"type": "auth", "access_token": self.token}))
            response = await websocket.recv()
            print(response)

            await websocket.send(json.dumps({"id": 1, "type": "subscribe_events", "event_type": "assistant_card_requested"}))
            response = await websocket.recv()
            print(response)

            while True:
                event = await websocket.recv()
                if self.event_callback:
                    self.event_callback(event)
    def set_event_callback(self, callback):
        self.event_callback = callback

    def start(self):
        asyncio.run(self.connect())


class Api:
    def __init__(self):
        url = None
        default_dashboard_path = None

    def listen(self):
        if not self.url or not self.default_dashboard_path:
            print("URL or default dashboard path is missing.")
            return

        window.load_url(f'{self.url}/{self.default_dashboard_path}')

        token = window.evaluate_js("""
                   localStorage.getItem('hassTokens')
               """)
        try:
            access_token = json.loads(token)['access_token']
            ws_url = self.url.replace("http", "ws")
            ws_url = f"{ws_url}/api/websocket"
            client = HomeAssistantClient(ws_url, access_token)
            client.set_event_callback(self.load_card)
            threading.Thread(target=client.start).start()
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error getting access token: {e}")

    def load_card(self, event):
        print(event)

        try:
            data = json.loads(event)
            card_url = data.get('event', {}).get('data', {}).get('card', {}).get('dashboard', {}).get('title')

            if card_url:
                new_url = f"{self.url}/{card_url}"
                window.load_url(new_url)
            else:
                print("Card URL  not found in event data.")
        except json.JSONDecodeError as e:
            print(f"Error decoding event data: {e}")

    def connect(self, url):
        print(f"Connecting to Home Assistant at: {url}")
        window.load_url(url)

        while True:
            result = window.evaluate_js("""
                        localStorage.getItem('hassTokens')
                    """)
            if result:
                self.save_url(url)
                break
            time.sleep(1)

    def save_url(self, url):
        saved_config = configparser.ConfigParser()
        saved_config.read(CONFIG_FILE)

        if 'HomeAssistant' not in saved_config:
            saved_config['HomeAssistant'] = {}

        saved_config['HomeAssistant']['url'] = url

        with open(CONFIG_FILE, 'w') as configfile:
            saved_config.write(configfile)
        print(f"URL saved: {url}")

    def save_config(self, form):
        saved_config = configparser.ConfigParser()
        saved_config.read(CONFIG_FILE)

        # Update or add the HomeAssistant URL
        if 'HomeAssistant' not in saved_config:
            saved_config['HomeAssistant'] = {}

        saved_config['HomeAssistant']['assist_entity'] = form['assistEntity']
        saved_config['HomeAssistant']['default_dashboard_path'] = form['defaultDashboard']

        with open(CONFIG_FILE, 'w') as configfile:
            saved_config.write(configfile)


def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    return config


if __name__ == "__main__":
    api = Api()
    config = load_config()

    api.url = config.get('HomeAssistant', 'url', fallback=None)
    api.default_dashboard_path = config.get('HomeAssistant', 'default_dashboard_path', fallback=None)

    if not api.url:
        # No URL configured, show the URL input screen
        window = webview.create_window("Home Assistant Login", 'screens/login.html', js_api=api, fullscreen=False)

    elif not api.default_dashboard_path:
        # URL configured, but no default dashboard path, show the configuration screen
        window = webview.create_window("Configure Home Assistant", 'screens/config.html', js_api=api, fullscreen=False)

    else:
        # Everything is configured, load the default dashboard
        full_dashboard_url = f"{api.url}/{api.default_dashboard_path}"
        window = webview.create_window("Home Assistant", 'screens/dashboard.html', js_api=api, fullscreen=False)
    webview.start(private_mode=False)
