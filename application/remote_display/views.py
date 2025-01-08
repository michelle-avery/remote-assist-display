from . import bp
from flask import redirect, url_for, current_app
from .auth import fetch_access_token

import requests
import socket

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
    return response