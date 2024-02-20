import argparse
import asyncio
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

disconnect_sent = False

current_day = None
webhook_token = None
webhook_url = None


# Callbacks


# def post_facet(facet):
#     activity = "unknown"
#     if facet == -1:
#         activity = "disconnect"
#     else:
#         activity = facet_mapping[facet]

#     requests.post(
#         webhook_url,
#         headers={
#             "Authorization": "Token {}".format(webhook_token),
#             "Content-Type": "application/json",
#         },
#         json={"side": facet, "activity": activity},
#     )


# async def event_callback(arg1, event_data):
#     post_facet(event_data[0])


# def get_current_day_of_week():
#     # Get the current date
#     current_date = datetime.now()

#     # Get the day of the week as an integer (Monday is 0, Sunday is 6)
#     day_of_week = current_date.weekday()

#     return day_of_week


def main():
    timeflip_config = load_configuration()
    device_config = timeflip_config["devices"][0]  # Only one supported

    print(device_config)
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
