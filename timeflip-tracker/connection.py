import asyncio
import sys
from typing import Any, Callable, Coroutine, List, Tuple

from bleak import BleakClient, BleakError, BleakScanner
from bleak.backends.device import BLEDevice
from colors import color_to_tuple
from database import insert_event
from pytimefliplib.async_client import (
    CHARACTERISTICS,
    DEFAULT_PASSWORD,
    AsyncClient,
    TimeFlipRuntimeError,
)

device_conf = None

facet_mapping = [
    "",
    "studying",  # 1
    "chores",  # 2
    "writing",  # 3
    "development",  # 4
    "reading",  # 5
    "streaming",  # 6
    "exercise",  # 7
    "administrivia",  # 8
    "television",  # 9
    "break",  # 10
    "music",  # 11
    "meeting",  # 12
]

weekday_colors = [
    (77, 166, 255),
    (255, 153, 102),
    (0, 153, 0),
    (204, 34, 0),
    (25, 255, 255),
    (42, 0, 128),
    (255, 221, 51),
]


class RuntimeClientError(Exception):
    pass


# async def set_facet_colors(client: AsyncClient, color):
#     for i in range(0, 12):
#         await client.set_color(i, color)


async def find_timeflip():
    """Adapted from Bleak documentation (https://pypi.org/project/bleak/) for the discovery of new devices."""

    devices_map: Dict[str, List[BLEDevice]] = {
        "connection_issue": [],
        "not_timeflip": [],
        "timeflip": [],
    }

    devices = await BleakScanner.discover()
    for d in devices:
        print(d)
        try:
            async with BleakClient(d) as client:
                try:  # Check if the device have a TimeFlip characteristic (here, the facet value)
                    _ = await client.read_gatt_char(CHARACTERISTICS["facet"])
                    devices_map["timeflip"].append(d)
                except BleakError:
                    devices_map["not_timeflip"].append(d)

        except (BleakError, asyncio.TimeoutError):
            devices_map["connection_issue"].append(d)

    return devices_map["timeflip"]


async def facet_notify_callback(arg1, event_data):
    facet_num = event_data[0]
    insert_event(
        device_conf["name"],
        device_conf["mac_address"],
        facet_num,
        device_conf["facets"][facet_num]["value"],
    )


def disconnect_callback(client: AsyncClient):
    print("NEFAS!")


async def connect_and_run(
    device_config,
    actions_on_client: Callable[[AsyncClient], Coroutine],
    disconnect_callback,
):
    global device_conf
    device_conf = device_config

    # for now just always try to reconnect until we're killed
    while True:
        try:
            async with AsyncClient(
                device_config["mac_address"], disconnected_callback=disconnect_callback
            ) as client:
                # setup
                print("! Connected to {}".format(device_config["mac_address"]))

                await client.setup(password=device_config["password"])
                print("! Password communicated")

                await actions_on_client(device_config, client)

        except (BleakError, TimeFlipRuntimeError, RuntimeClientError) as e:
            print("communication error: {}".format(e), file=sys.stderr)

            # TODO: handle this

        await asyncio.sleep(300)


async def actions_on_client(device_config, client: AsyncClient):
    await client.register_notify_facet_v3(facet_notify_callback)

    # battery_level = await client.battery_level()
    # Post the current facet on connect
    # current_facet = await client.current_facet()
    # post_facet(current_facet)

    color_tuple_white = color_to_tuple("white")
    for i in range(0, 12):
        if i < len(device_config["facets"]):
            facet = device_config["facets"][i]

            if "color" in facet:
                color_tuple = color_to_tuple(facet["color"])
                await client.set_color(i, color_tuple)
            else:
                await client.set_color(i, color_tuple_white)
        else:
            await client.set_color(i, color_tuple_white)

    while True:
        await asyncio.sleep(60)
