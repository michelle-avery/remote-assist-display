import configparser
import os

CONFIG_FILE = "config.ini"

def get_saved_config(config_dir):
    config_file = os.path.join(config_dir, CONFIG_FILE)
    saved_config = configparser.ConfigParser()
    saved_config.read(config_file)
    return saved_config

def save_to_config(section, key, value, config_dir):
    config = get_saved_config(config_dir)
    config_file = os.path.join(config_dir, CONFIG_FILE)
    if section not in config:
        config[section] = {}
    config[section][key] = value
    with open(config_file, "w") as configfile:
        config.write(configfile)
