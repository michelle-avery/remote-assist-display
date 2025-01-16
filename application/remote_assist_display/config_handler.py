import configparser

CONFIG_FILE = "config.ini"

def get_saved_config():
    saved_config = configparser.ConfigParser()
    saved_config.read(CONFIG_FILE)
    return saved_config

def save_to_config(section, key,value):
    config = get_saved_config()
    if section not in config:
        config[section] = {}
    config[section][key] = value
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)
