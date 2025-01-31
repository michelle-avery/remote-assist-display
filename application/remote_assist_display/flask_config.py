import os
import socket
import sys
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

def check_frozen() -> bool:
    """Check if we are running in a frozen environment."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return True
    return False

def get_local_dir(is_android: bool, is_frozen: bool) -> str:
    """Return the log directory based on the environment."""
    if is_android:
        try:
            from android.storage import app_storage_path  # type: ignore
            return str(app_storage_path())
        except ImportError:
            raise RuntimeError("android.storage module is not available")
    elif is_frozen:
        return str(os.path.dirname(os.path.abspath(sys.executable)))
    else:
        return str(os.path.dirname(__file__))
    
class Config(object):
    env = Env()
    VERSION = "0.0.1"
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
    IS_FROZEN = check_frozen()
    LOG_DIR = env.str("LOG_DIR", get_local_dir(IS_ANDROID, IS_FROZEN))
    CONFIG_DIR = env.str("CONFIG_DIR", get_local_dir(IS_ANDROID, IS_FROZEN))