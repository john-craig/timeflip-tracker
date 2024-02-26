import logging
import os

timeflip_logger = None

LOG_LEVEL_LOOKUP = {"INFO": logging.INFO, "DEBUG": logging.DEBUG}


def create_logger():
    global timeflip_logger

    env_log_level = os.getenv("LOG_LEVEL")
    if env_log_level in LOG_LEVEL_LOOKUP:
        log_level = LOG_LEVEL_LOOKUP[env_log_level]
    else:
        log_level = logging.ERROR

    # Set up logging
    logging.basicConfig()
    timeflip_logger = logging.getLogger("Timeflip")
    timeflip_logger.setLevel(log_level)


def get_logger():
    global timeflip_logger
    return timeflip_logger
