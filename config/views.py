from . import bp
from flask import render_template, request, redirect, url_for, current_app
import configparser
import time
import webview

CONFIG_FILE = "config.ini"


@bp.route("/", methods=["GET"])
def config():
    saved_config = configparser.ConfigParser()
    saved_config.read(CONFIG_FILE)
    if "HomeAssistant" in saved_config:
        current_app.config["assist_entity"] = saved_config.get("HomeAssistant", "assist_entity", fallback=None)
        current_app.config["default_dashboard"] = saved_config.get("HomeAssistant", "default_dashboard_path", fallback=None)
        current_app.config["url"] = saved_config.get("HomeAssistant", "url", fallback=None)
        if current_app.config["assist_entity"] and current_app.config["default_dashboard"]:
            return redirect(url_for("dashboard.dashboard"))
        else:
            return render_template("config.html")
    return redirect(url_for("config.hass_login"))

@bp.route("/save", methods=["POST"])
def save_config():
    assist_entity = request.form.get("assistEntity")
    default_dashboard = request.form.get("defaultDashboard")

    # Save configuration to a file
    saved_config = configparser.ConfigParser()
    saved_config.read(CONFIG_FILE)

    if "HomeAssistant" not in saved_config:
        saved_config["HomeAssistant"] = {}

    saved_config["HomeAssistant"]["assist_entity"] = assist_entity
    saved_config["HomeAssistant"]["default_dashboard_path"] = default_dashboard

    # Also set the values on the server object so they can be accessed later
    current_app.config["assist_entity"] = assist_entity
    current_app.config["default_dashboard"] = default_dashboard

    with open(CONFIG_FILE, "w") as configfile:
        saved_config.write(configfile)

    return redirect(url_for("config.hass_login"))

@bp.route("/hass-login", methods=["GET"])
def hass_login():
    return render_template("login.html")

@bp.route("/connect", methods=["POST"])
def  connect():
    def save_url(url):
        saved_config = configparser.ConfigParser()
        saved_config.read(CONFIG_FILE)

        if "HomeAssistant" not in saved_config:
            saved_config["HomeAssistant"] = {}

        saved_config["HomeAssistant"]["url"] = url

        # Also save the URL on the Server object
        current_app.config["url"] = url

        with open(CONFIG_FILE, "w") as configfile:
            saved_config.write(configfile)
        print(f"URL saved: {url}")

    url = request.form.get("haUrl")

    webview.windows[0].load_url(url)

    while True:
        result = webview.windows[0].evaluate_js("""
            localStorage.getItem('hassTokens')
        """)
        if result:
            save_url(url)
            return redirect(url_for("dashboard.dashboard"))

        time.sleep(1)

    return redirect(url_for("dashboard.dashboard"))
