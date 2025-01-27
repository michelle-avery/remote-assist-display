import socket
import uuid

from environs import Env


def get_hostname() -> str:
    """Return the device hostname."""
    return socket.gethostname()

def get_mac_address() -> str:
    """Return MAC address formatted as hex with no colons."""
    return "".join(
        ["{:02x}".format((uuid.getnode() >> ele) & 0xFF) for ele in range(0, 8 * 6, 8)][
            ::-1
        ]
    )

def check_android(env: Env) -> bool:
    """Check if we are running on an Android device."""
    if bool(env.int("P4A_MINSDK", 0)):
        return True
    return False

class Config(object):
    env = Env()

    # Logging and debug settings
    LOG_LEVEL = env.str("LOG_LEVEL", "INFO").upper()
    FLASK_DEBUG = env.bool("FLASK_DEBUG", False)
    FULLSCREEN = env.bool("FULLSCREEN", True)
    WEBVIEW_DEBUG = env.bool("WEBVIEW_DEBUG", False)

    SEND_FILE_MAX_AGE_DEFAULT = env.int("SEND_FILE_MAX_AGE_DEFAULT", 1)
    # Default timeout of dashboard in seconds
    DEFAULT_DASHBOARD_TIMEOUT =  env.int("DEFAULT_DASHBOARD_TIMEOUT", 30)
    # Number of times to retry fetching token
    TOKEN_RETRY_LIMIT = env.int("TOKEN_RETRY_LIMIT", 10)
    # Event type to listen for
    EVENT_TYPE = env.str("EVENT_TYPE", "remote_assist_display_navigate")
    # The device's MAC address
    MAC_ADDRESS = env.str("MAC_ADDRESS", get_mac_address())
    # The device's hostname
    HOSTNAME = env.str("HOSTNAME", get_hostname())
    # The unique ID to use for this device
    UNIQUE_ID = env.str("UNIQUE_ID", f"remote-assist-display-{MAC_ADDRESS}-{HOSTNAME}")
    # Are we running on android?
    IS_ANDROID = check_android(env)