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
from timeflip_tracker.configuration import load_configuration
from timeflip_tracker.connection import *
from timeflip_tracker.database import *
from timeflip_tracker.logger import *
from prometheus_client import start_http_server


async def main():
    create_logger()
    timeflip_logger = get_logger()

    database_cursor = connect_database()

    timeflip_config = load_configuration()
    adapter_addr = timeflip_config["adapter"] if "adapter" in timeflip_config else None

    loop = asyncio.get_event_loop()

    # Start up the server to expose the metrics.
    metrics_server, _ = start_http_server(8000)

    def handler(signum, frame):
        timeflip_logger.warning("Got SIGINT/SIGTERM, shutting down...")
        all_tasks = asyncio.all_tasks(loop=loop)
        for task in all_tasks:
            task.cancel()

        close_database()
        metrics_server.shutdown()
        # loop.close()

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

    try:
        await asyncio.gather(*device_coroutines)
    except asyncio.exceptions.CancelledError:
        pass


def run_main():
    asyncio.run(main())

if __name__ == "__main__":
    run_main()
