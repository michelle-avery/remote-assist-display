from http import HTTPStatus
from urllib.parse import urlparse

import requests
from flask import current_app, redirect, render_template, request, url_for

from .auth import fetch_access_token
from .config_handler import get_saved_config, save_to_config

# from .websocket_manager import WebSocketManager
from .ha_websocket_manager import WebSocketManager
from .navigate import load_dashboard

CONFIG_FILE = "config.ini"


def register_routes(app):
    @app.route("/", methods=["GET"])
    async def config():
        saved_config = get_saved_config(current_app.config["CONFIG_DIR"])
        if "HomeAssistant" in saved_config:
            current_app.logger.debug("Found existing config file")
            current_app.config["url"] = saved_config.get(
                "HomeAssistant", "url", fallback=None
            )
            current_app.logger.debug(f"Found configured URL: {current_app.config['url']}")
            if current_app.config["url"]:
                # Todo: handle cases where we have a saved url, but no valid credentials
                current_app.logger.debug("Redirecting to waiting page")
                return redirect(url_for("waiting"))
        current_app.logger.debug("No existing config file found, redirecting to login")
        return redirect(url_for("hass_login"))

    @app.route("/hass-login", methods=["GET"])
    def hass_login():
        
        error_code = request.args.get('error')
        error_message = None
        
        if error_code == 'auth_incomplete':
            error_message = "Authentication was not completed. Please try logging in again."
        elif error_code == 'auth_failed':
            error_message = "Failed to authenticate with Home Assistant. Please try again."
        elif error_code == 'unexpected':
            error_message = "An unexpected error occurred. Please try again."
            
        return render_template("login.html", error_message=error_message)

    def save_url(url):
        save_to_config("HomeAssistant", "url", url, current_app.config["CONFIG_DIR"])
        current_app.logger.debug(f"Saved URL to config file: {url}")
        # Also save the URL on the Server object
        current_app.config["url"] = url

    @app.route("/connect", methods=["POST"])
    async def connect():
        url = request.form.get("haUrl")
        if not url:
            return {"error": "Please enter a Home Assistant URL"}, HTTPStatus.BAD_REQUEST
        
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return {"error": "Please enter a valid URL"}, HTTPStatus.BAD_REQUEST
        except Exception:
            return {"error": "Please enter a valid URL"}, HTTPStatus.BAD_REQUEST
        
        # Check if the URL is reachable before attempting to load it
        try:
            response = requests.get(f"{url}/auth/providers", verify=False, timeout=5)
            if response.status_code != 200:
                return {
                    "error": "Unable to connect to Home Assistant at this URL. Please verify the URL and try again."
                }, HTTPStatus.BAD_REQUEST
        except requests.exceptions.ConnectTimeout:
            return {"error": "Could not connect to Home Assistant. Please check the URL and ensure Home Assistant is running."}, HTTPStatus.BAD_REQUEST
        except requests.exceptions.ConnectionError:
            return {
                "error": "Could not connect to Home Assistant. Please check the URL and ensure Home Assistant is running."
            }, HTTPStatus.BAD_REQUEST
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Connection error: {str(e)}", exc_info=True)
            return {
                "error": "Failed to connect to Home Assistant. Please verify the URL and try again."
            }, HTTPStatus.BAD_REQUEST

        
        try:
            # Since we won't have settings from the server yet, we can't set the 
            # device name in localStorage.
            current_app.logger.debug(f"Getting credentials from Home Assistant at {url}")
            await load_dashboard(url, local_storage=False)
            
            try:
                retries = current_app.config.get(
                    "TOKEN_RETRY_LIMIT", 10
                ) 
                await fetch_access_token(
                    url=url,
                    retries=retries,
                    delay=10,
                    app=current_app,
                )
            except Exception as auth_error:
                current_app.logger.error(f"Authentication error: {str(auth_error)}", exc_info=True)
                # Navigate back to login page with error
                if "Unable to fetch token from localStorage" in str(auth_error):
                    await load_dashboard(url_for('hass_login', error='auth_incomplete'), local_storage=False)
                else:
                    await load_dashboard(url_for('hass_login', error='auth_failed'), local_storage=False)
                return "", HTTPStatus.OK  # Return OK since we handled the navigation
            # Save the URL to our config file
            save_url(url)
            current_app.logger.debug("Redirecting to waiting page")
            await load_dashboard(url_for("waiting"), local_storage=False)
            return "", HTTPStatus.OK

        except Exception as e:
            current_app.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            await load_dashboard(url_for('hass_login', error='unexpected'), local_storage=False)
            return "", HTTPStatus.OK

    @app.route("/waiting", methods=["GET"])
    def waiting():
        return render_template("waiting.html")

    @app.route("/hass-config", methods=["POST"])
    async def hassconfig():
        if "url" not in current_app.config:
            return {"error": "Missing Home Assistant URL"}, HTTPStatus.BAD_REQUEST

        try:
            manager = WebSocketManager.get_instance(current_app)
            manager.initialize(current_app.config["url"])
            return "", HTTPStatus.OK
        except Exception as e:
            current_app.logger.error(
                f"Failed to configure Home Assistant: {str(e)}", exc_info=True
            )
            await load_dashboard(url_for('hass_login', error=str(e)), local_storage=False)
            return {"error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
