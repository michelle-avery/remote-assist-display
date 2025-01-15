from flask import current_app

from .state import DisplayState

def event_router(event, expire_time=None):
    """Route events to the appropriate function."""
    current_app.logger.info(f"Received event: {event}")
    display_state = DisplayState.get_instance()
    # Make sure any async operations here are properly handled
    try:
        settings =event.get("event", {}).get("result", {}).get("displays",{}).get(current_app.config["UNIQUE_ID"], {}).get("settings",None)
        if settings:
            # The event contains new settings for this display, update them
            update_settings(settings, display_state)
        elif event.get("event", {}).get("command") == "remote_assist_display/navigate_url":
            # The event is a request to navigate to a URL
            display_state.load_url(event.get("event", {}).get("url"))

    except Exception as e:
        current_app.logger.error(f"Error in load_card: {e}")


def update_settings(settings, display_state):
    if settings.get("default_dashboard", None):
        current_app.config["default_dashboard"] = settings["default_dashboard"]
        dashboard_url = f'{current_app.config["url"]}/{current_app.config["default_dashboard"]}'
        display_state.load_url(dashboard_url)
