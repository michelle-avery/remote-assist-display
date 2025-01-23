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

class Config(object):
    env = Env()

    SEND_FILE_MAX_AGE_DEFAULT = env.int("SEND_FILE_MAX_AGE_DEFAULT", 1)
    # Default timeout of dashboard in seconds
    DEFAULT_DASHBOARD_TIMEOUT =  env.int("DEFAULT_DASHBOARD_TIMEOUT", 30)
    # Number of times to retry fetching token
    TOKEN_RETRY_LIMIT = env.int("TOKEN_RETRY_LIMIT", 10)
    # Event type to listen for
    EVENT_TYPE = env.str("EVENT_TYPE", "remote_assist_display_navigate")
    # The local storage key to use for the device name. By default, this is the
    # key used by browser_mod, to  maintain ViewAssist compatibility
    DEVICE_NAME_KEY = env.str("DEVICE_NAME_KEY", "browser_mod-browser-id")
    # The device's MAC address
    MAC_ADDRESS = env.str("MAC_ADDRESS", get_mac_address())
    # The device's hostname
    HOSTNAME = env.str("HOSTNAME", get_hostname())
    # The unique ID to use for this device
    UNIQUE_ID = env.str("UNIQUE_ID", f"remote-assist-display-{MAC_ADDRESS}-{HOSTNAME}")
