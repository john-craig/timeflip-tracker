import os

from ruamel.yaml import YAML

yaml = YAML(typ="rt")


def validate_configuration(configuration):
    # Main thing is that a device only has 12
    # sides, so... gotta check for that
    for device in configuration["devices"]:
        if "facets" in device:
            if len(device["facets"]) > 12:
                raise ValueError(f"Too many facets defined for device {device['name']}")


def load_configuration():
    # Order of precedence:
    #   1) actual environment variable
    #   2) configuration value
    config_path = os.getenv("CONFIG_PATH")

    # Finally load from config file
    if not config_path:
        config_path = DEFAULT_CONFIG_PATH

    with open(config_path, "r") as file:
        configuration = yaml.load(file)

    validate_configuration(configuration)

    return configuration
