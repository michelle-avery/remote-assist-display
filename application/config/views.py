from . import bp

from dashboard.navigate import load_dashboard
from flask import render_template, request, redirect, url_for, current_app
from .config_handler import get_saved_config, save_to_config
from remote_display.auth import fetch_access_token
from remote_display.views import register

CONFIG_FILE = "config.ini"


@bp.route("/", methods=["GET"])
async def config():
    saved_config = get_saved_config()
    if "HomeAssistant" in saved_config:
        current_app.config["url"] = saved_config.get("HomeAssistant", "url", fallback=None)
        if current_app.config["url"]:
            # Todo: handle cases where we have a saved url, but no valid credentials
            return redirect(url_for("config.waiting"))
    return redirect(url_for("config.hass_login"))



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

    try:
        await fetch_access_token(url=url, retries=current_app.config.get("TOKEN_RETRY_LIMIT"))
        # Save the URL to our config file
        save_url(url)
        # Register the device.
        response = await register()
        load_dashboard(url_for('config.waiting'))

        return response


    except Exception as e:
        return {"error": str(e)}, 500

@bp.route("/waiting", methods=["GET"])
def waiting():
    return render_template("waiting.html")