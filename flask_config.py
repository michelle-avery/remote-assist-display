from environs import Env

class Config(object):
    env = Env()
    env.read_env()

    SEND_FILE_MAX_AGE_DEFAULT = env.int("SEND_FILE_MAX_AGE_DEFAULT", 1)
    # Default timeout of dashboard in seconds
    DEFAULT_DASHBOARD_TIMEOUT =  env.int("DEFAULT_DASHBOARD_TIMEOUT", 30)
    # Number of times to retry fetching token
    TOKEN_RETRY_LIMIT = env.int("TOKEN_RETRY_LIMIT", 10)
    # Event type to listen for
    EVENT_TYPE = env.str("EVENT_TYPE", "custom_conversation_conversation_ended")
    # The local storage key to use for the device name. By default, this is the
    # key used by browser_mod, to  maintain ViewAssist compatibility
    DEVICE_NAME_KEY = env.str("DEVICE_NAME_KEY", "browser_mod-browser-id")
