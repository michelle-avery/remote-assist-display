import configparser
import os
import json
import time
import threading
from functools import wraps

from flask import Flask, request, render_template, redirect, url_for

import  webview

from home_assistant import HomeAssistantClient

CONFIG_FILE = "config.ini"

gui_dir = os.path.join(os.path.dirname(__file__), 'templates')  # development path

if not os.path.exists(gui_dir):  # frozen executable path
    gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gui')

server = Flask(__name__, static_folder=gui_dir, template_folder=gui_dir)
server.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1  # disable caching

def verify_token(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        data = json.loads(request.data)
        token = data.get('token')
        if token == webview.token:
            return function(*args, **kwargs)
        else:
            raise Exception('Authentication error')

    return wrapper

@server.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

@server.route('/')
def landing():
    # Check the config and redirect appropriately
    saved_config = configparser.ConfigParser()
    saved_config.read(CONFIG_FILE)
    if 'HomeAssistant' in saved_config:
        server.config['assist_entity'] = saved_config.get('HomeAssistant', 'assist_entity', fallback=None)
        server.config['default_dashboard'] = saved_config.get('HomeAssistant', 'default_dashboard_path', fallback=None)
        if server.config['assist_entity'] and server.config['default_dashboard']:
            # Everything's configured, so redirect to the dashboard
            return redirect(url_for('dashboard'))
        else:
            # Configuration is incomplete, so redirect to the config page
            return render_template('config.html', token=webview.token)
    # We don't have a saved url, so redirect to the login page
    return redirect(url_for('hass_login'))

@server.route('/save-config', methods=['POST'])
def save_config():
    assist_entity = request.form.get('assistEntity')
    default_dashboard = request.form.get('defaultDashboard')

    # Save configuration to a file
    saved_config = configparser.ConfigParser()
    saved_config.read(CONFIG_FILE)

    if 'HomeAssistant' not in saved_config:
        saved_config['HomeAssistant'] = {}

    saved_config['HomeAssistant']['assist_entity'] = assist_entity
    saved_config['HomeAssistant']['default_dashboard_path'] = default_dashboard

   # Also set the values on the server object so they can be accessed later
    server.config['assist_entity'] = assist_entity
    server.config['default_dashboard'] = default_dashboard

    with open(CONFIG_FILE, 'w') as configfile:
        saved_config.write(configfile)

    return redirect(url_for('hass_login'))

@server.route('/hass-login', methods=['GET'])
def hass_login():
    return render_template('login.html', token=webview.token)

@server.route('/connect', methods=['POST'])
def connect():
    def save_url(url):
        saved_config = configparser.ConfigParser()
        saved_config.read(CONFIG_FILE)

        if 'HomeAssistant' not in saved_config:
            saved_config['HomeAssistant'] = {}

        saved_config['HomeAssistant']['url'] = url

        # Also save the URL on the Server object
        server.config['url'] = url

        with open(CONFIG_FILE, 'w') as configfile:
            saved_config.write(configfile)
        print(f"URL saved: {url}")

    url = request.form.get('haUrl')
    webview.windows[0].load_url(url)

    while True:
        result = webview.windows[0].evaluate_js("""
                    localStorage.getItem('hassTokens')
                """)
        if result:
            save_url(url)
            return redirect(url_for('dashboard'))

        time.sleep(1)

@server.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template('dashboard.html')

@server.route('/listen', methods=['POST'])
def listen():
    url = server.config['url']
    dashboard = server.config['default_dashboard']
    webview.windows[0].load_url(f'{url}/{dashboard}')
    token = webview.windows[0].evaluate_js("""
                localStorage.getItem('hassTokens')
            """)
    access_token = json.loads(token)['access_token']
    ws_url = url.replace("http", "ws")
    ws_url = f"{ws_url}/api/websocket"
    client = HomeAssistantClient(ws_url, access_token)
    client.set_event_callback(load_card)
    threading.Thread(target=client.start).start()
    return "Listening for events..."

def load_card(event):
    data = json.loads(event)
    card_url = data.get('event', {}).get('data', {}).get('result', {}).get('response', {}).get('card', {}).get('dashboard', {}).get('title')
    device_id = data.get('event', {}).get('data', {}).get('device_id')
    entity_id = server.config['assist_entity']
    hass_url = server.config['url']

    if device_id != entity_id:
        return
    if card_url:
        new_url = f"{hass_url}/{card_url}"
        webview.windows[0].load_url(new_url)
    else:
        print("Card URL not found in event data.")
