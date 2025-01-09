from . import bp
from flask import redirect, url_for, current_app
from http import HTTPStatus
from .auth import fetch_access_token

import asyncio
import requests
import socket

from dashboard.navigate import load_dashboard


@bp.route("/")
def index():
    return redirect(url_for("config.config"))

@bp.route("/register", methods=["POST"])
async def register():
    url = current_app.config["url"]
    id = current_app.config["UNIQUE_ID"]
    hostname = socket.gethostname()
    token = await fetch_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    data = {"hostname": hostname, "id": id}
    response = requests.post(f"{url}/api/remote_assist_display/register", json=data, headers=headers)
    return response.json(), response.status_code

@bp.route("/hass-config", methods=["POST"])
async def hassconfig():
    url = current_app.config["url"]
    id = current_app.config["UNIQUE_ID"]
    token = await fetch_access_token(url=url)
    headers = {"Authorization": f"Bearer {token}"}
    # Poll the config endpoint every minute until a default dashboard is configured
    while True:
        response = requests.get(f"{url}/api/remote_assist_display/config/{id}", headers=headers)
        if response.json().get("default_dashboard", None):
            current_app.config["default_dashboard"] = response.json()["default_dashboard"]
            break
        await asyncio.sleep(60)
    load_dashboard(url_for("dashboard.dashboard"))
    return "", HTTPStatus.OK