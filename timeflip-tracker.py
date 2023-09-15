import argparse
from datetime import datetime, timedelta
from typing import Callable, Any, List, Tuple, Coroutine
import pytimefliplib
from pytimefliplib.async_client import AsyncClient, DEFAULT_PASSWORD, CHARACTERISTICS, TimeFlipRuntimeError
from bleak import BleakScanner, BleakClient, BleakError
from bleak.backends.device import BLEDevice
import requests
import asyncio
import os
import configparser

DEFAULT_CONFIG_PATH = "/etc/timeflip-tracker/config.toml"
global CURRENT_DAY

class RuntimeClientError(Exception):
    pass

facet_mapping = [
    "",
    "studying", #1
    "chores", #2
    "writing", #3
    "development", #4
    "reading", #5
    "streaming", #6
    "exercise", #7
    "administrivia", #8
    "television", #9
    "break", #10
    "music", #11
    "meeting"  #12
]

weekday_colors = [
    (77,166,255),
    (255,153,102),
    (0,153,0), 
    (204,34,0),
    (25,255,255),
    (42,0,128),
    (255,221,51)
]

# Callbacks

async def event_callback(arg1, event_data):
    requests.post(
        webhook_url,
        headers={
            "Authorization": "Token {}".format(webhook_token),
            "Content-Type": "application/json"
        },
        json={
            "side": event_data[0],
            "activity": facet_mapping[event_data[0]]
        }
    )

def disconnected_callback(client):
    requests.post(
        webhook_url,
        headers={
            "Authorization": "Token {}".format(webhook_token),
            "Content-Type": "application/json"
        },
        json={
            "side": -1,
            "activity": "disconnected"
        }
    )

async def find_timeflip():
    """Adapted from Bleak documentation (https://pypi.org/project/bleak/) for the discovery of new devices.
    """

    devices_map: Dict[str, List[BLEDevice]] = {
        'connection_issue': [],
        'not_timeflip': [],
        'timeflip': []
    }

    devices = await BleakScanner.discover()
    for d in devices:
        try:
            async with BleakClient(d) as client:
                try:  # Check if the device have a TimeFlip characteristic (here, the facet value)
                    _ = await client.read_gatt_char(CHARACTERISTICS['facet'])
                    devices_map['timeflip'].append(d)
                except BleakError:
                    devices_map['not_timeflip'].append(d)

        except (BleakError, asyncio.TimeoutError):
            devices_map['connection_issue'].append(d)
    
    return devices_map['timeflip']

async def connect_and_run(actions_on_client: Callable[[AsyncClient], Coroutine]):
    # Note: option to manually pass in the address would go here
    timeflip_addresses = await find_timeflip()

    if len(timeflip_addresses) == 0:
        raise TimeFlipRuntimeError('Could not find TimeFlip device')

    timeflip_address = timeflip_addresses[0]
    timeflip_password = DEFAULT_PASSWORD

    try:
        async with AsyncClient(timeflip_address, disconnected_callback=disconnected_callback) as client:
            # setup
            print('! Connected to {}'.format(timeflip_address))

            await client.setup(password=timeflip_password)
            print('! Password communicated')

            await actions_on_client(client)

    except (BleakError, TimeFlipRuntimeError, RuntimeClientError) as e:
        print('communication error: {}'.format(e), file=sys.stderr)

def get_current_day_of_week():
    # Get the current date
    current_date = datetime.now()

    # Get the day of the week as an integer (Monday is 0, Sunday is 6)
    day_of_week = current_date.weekday()

    return day_of_week

async def set_facet_colors(client: AsyncClient, color):
    for i in range(0,12):
        await client.set_color(i, color)

async def actions_on_client(client: AsyncClient):
    await client.register_notify_facet_v3(event_callback)

    CURRENT_DAY = get_current_day_of_week()

    await set_facet_colors(client, weekday_colors[CURRENT_DAY])

    while True:
        await asyncio.sleep(60)

        if get_current_day_of_week() != CURRENT_DAY:
            CURRENT_DAY = get_current_day_of_week()

            await set_facet_colors(client, weekday_colors[CURRENT_DAY])


def load_configuration():
    # Order of precedence:
    #   1) actual environment variable
    #   2) variable contained in .env file
    #   3) configuration value
    webhook_token = os.getenv("WEBHOOK_TOKEN")
    webhook_url = os.getenv("WEBHOOK_URL")
    config_path = os.getenv("CONFIG_PATH")

    # Finally load from config file
    if not config_path:
        config_path = DEFAULT_CONFIG_PATH
    
    config = configparser.ConfigParser()
    config.read_file(open(config_path))

    if not webhook_token:
        webhook_token = config['WEBHOOK']['TOKEN']
    
    if not webhook_url:
        webhook_url = config['WEBHOOK']['URL']

    return (webhook_token, webhook_url)


def main():
    webhook_token, webhook_url = load_configuration()

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(connect_and_run(actions_on_client))
    except BaseException:
        all_tasks = asyncio.all_tasks(loop=loop)
        for task in all_tasks:
            task.cancel()
        loop.run_until_complete(
            asyncio.gather(
                *all_tasks,
                return_exceptions=True # means all tasks get a chance to finish
            )
        )
        raise
    finally:
        loop.close()


if __name__ == '__main__':
    main()
