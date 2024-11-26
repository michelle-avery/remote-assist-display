import webview
import websockets
import configparser
import json
import os
import time

CONFIG_FILE = "config.ini"

class Api:

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

        # Update or add the HomeAssistant URL
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

    home_assistant_url = config.get('HomeAssistant', 'url', fallback=None)
    default_dashboard_path = config.get('HomeAssistant', 'default_dashboard_path', fallback=None)

    if not home_assistant_url:
        # No URL configured, show the URL input screen
        window = webview.create_window("Home Assistant Login", 'screens/login.html', js_api=api, fullscreen=False)

    elif not default_dashboard_path:
        # URL configured, but no default dashboard path, show the configuration screen
        window = webview.create_window("Configure Home Assistant", 'screens/config.html', js_api=api, fullscreen=False)

    else:
        # Everything is configured, load the default dashboard
        full_dashboard_url = f"{home_assistant_url}/{default_dashboard_path}"
        window = webview.create_window("Home Assistant", full_dashboard_url, js_api=api, fullscreen=False)
    webview.start(private_mode=False)
