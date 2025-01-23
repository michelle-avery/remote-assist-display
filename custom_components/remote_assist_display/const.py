"""Constants for the Remote Assist Display integration"""

import logging

DOMAIN = "remote_assist_display"
WS_ROOT = DOMAIN
LOGGER = logging.getLogger(__package__)
NAVIGATE_SERVICE = "navigate"
NAVIGATE_URL_SERVICE = "navigate_url"
NAVIGATE_WS_COMMAND = f"{WS_ROOT}/navigate"
NAVIGATE_URL_WS_COMMAND = f"{WS_ROOT}/navigate_url"
REGISTER_WS_COMMAND = f"{WS_ROOT}/register"
SETTINGS_WS_COMMAND = f"{WS_ROOT}/settings"
CONNECT_WS_COMMAND = f"{WS_ROOT}/connect"
PING_WS_COMMAND = f"{WS_ROOT}/ping"
UPDATE_WS_COMMAND = f"{WS_ROOT}/update"
DATA_DISPLAYS = "displays"
DATA_ADDERS = "adders"
DEFAULT_DISPLAY_OPTIONS = "default_display_options"
DEFAULT_HOME_ASSISTANT_DASHBOARD = "lovelace"
