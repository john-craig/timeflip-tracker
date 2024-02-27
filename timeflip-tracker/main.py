import argparse
import asyncio
import logging
import os
import sys
import threading
from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine, List, Tuple

import pytimefliplib
import requests
from bleak import BleakClient, BleakError, BleakScanner
from bleak.backends.device import BLEDevice
from configuration import load_configuration
from connection import *
from database import *

LOG_LEVEL_LOOKUP = {"INFO": logging.INFO, "DEBUG": logging.DEBUG}


def main():
    env_log_level = os.getenv("LOG_LEVEL")
    if env_log_level in LOG_LEVEL_LOOKUP:
        log_level = LOG_LEVEL_LOOKUP[env_log_level]
    else:
        log_level = logging.ERROR

    logging.basicConfig()
    logging.getLogger().setLevel(log_level)

    database_cursor = connect_database()

    timeflip_config = load_configuration()
    device_config = timeflip_config["devices"][0]  # Only one supported

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(
            connect_and_run(device_config, actions_on_client, disconnect_callback)
        )
    except (BaseException, KeyboardInterrupt):
        all_tasks = asyncio.all_tasks(loop=loop)
        for task in all_tasks:
            task.cancel()
        loop.run_until_complete(
            asyncio.gather(
                *all_tasks,
                return_exceptions=True  # means all tasks get a chance to finish
            )
        )

        raise
    finally:
        loop.close()


if __name__ == "__main__":
    main()
