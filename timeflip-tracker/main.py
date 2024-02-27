import argparse
import asyncio
import logging
import os
import signal
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
from logger import *
from prometheus_client import start_http_server


async def main():
    create_logger()
    timeflip_logger = get_logger()

    database_cursor = connect_database()

    timeflip_config = load_configuration()
    device_config = timeflip_config["devices"][0]  # Only one supported
    adapter_addr = timeflip_config["adapter"] if "adapter" in timeflip_config else None

    loop = asyncio.get_event_loop()

    # Start up the server to expose the metrics.
    metrics_server, _ = start_http_server(8000)

    def handler(signum, frame):
        timeflip_logger.warning("Got SIGINT/SIGTERM, shutting down...")
        all_tasks = asyncio.all_tasks(loop=loop)
        for task in all_tasks:
            task.cancel()
        loop.run_until_complete(
            asyncio.gather(
                *all_tasks,
                return_exceptions=True  # means all tasks get a chance to finish
            )
        )

        close_database()
        metrics_server.shutdown()
        loop.close()

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    device_coroutines = list(
        map(
            lambda device_config: connect_and_run(
                device_config, adapter_addr=adapter_addr
            ),
            timeflip_config["devices"],
        )
    )

    await asyncio.gather(*device_coroutines)


if __name__ == "__main__":
    asyncio.run(main())
