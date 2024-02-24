import asyncio
import logging
import sys
from typing import Any, Callable, Coroutine, List, Tuple

from bleak import BleakClient, BleakError, BleakGATTCharacteristic, BleakScanner
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


class RuntimeClientError(Exception):
    pass


async def find_timeflip():
    """Adapted from Bleak documentation (https://pypi.org/project/bleak/) for the discovery of new devices."""

    devices_map: Dict[str, List[BLEDevice]] = {
        "connection_issue": [],
        "not_timeflip": [],
        "timeflip": [],
    }

    devices = await BleakScanner.discover()
    for d in devices:
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


async def facet_notify_callback(sender: BleakGATTCharacteristic, event_data):
    facet_num = event_data[0]
    insert_event(
        device_conf["name"],
        device_conf["mac_address"],
        facet_num,
        device_conf["facets"][facet_num]["value"],
    )


def disconnect_callback(client: AsyncClient):
    logger.warning(f"Disconnected from {client.address}")


async def connect_and_run(
    device_config,
    actions_on_client: Callable[[AsyncClient], Coroutine],
    disconnect_callback,
):
    global device_conf
    device_conf = device_config
    mac_addr = device_config["mac_address"]

    # for now just always try to reconnect until we're killed
    while True:
        try:
            async with AsyncClient(
                device_config["mac_address"], disconnected_callback=disconnect_callback
            ) as client:
                # setup
                debug.info(f"Connected to {mac_addr}")

                await client.setup(password=device_config["password"])
                debug.info(f"Password communicated to {mac_addr}")

                await actions_on_client(device_config, client)

        except (BleakError, TimeFlipRuntimeError, RuntimeClientError) as e:
            logging.error(f"Communication error connecting to {mac_addr}: {e}")

            # TODO: handle this

        await asyncio.sleep(300)


async def actions_on_client(device_config, client: AsyncClient):
    await client.register_notify_facet_v3(facet_notify_callback)

    mac_addr = device_config["mac_address"]
    logger.info(f"Connected to device {mac_addr}")

    firmware_revision = await client.firmware_revision()
    battery_level = await client.battery_level()
    internal_device_name = await client.device_name()
    logger.debug(
        f"Device {mac_addr} firmware revision {firmware_revision}, battery level {battery_level}, device_name {internal_device_name}"
    )

    color_tuple_white = color_to_tuple("white")
    for i in range(0, 12):
        color_tuple = None

        if i < len(device_config["facets"]):
            facet = device_config["facets"][i]

            if "color" in facet:
                color_tuple = color_to_tuple(facet["color"])
            else:
                color_tuple = color_tuple_white
        else:
            color_tuple = color_tuple_white

        await client.set_color(i, color_tuple)
        logging.debug(f"Device {mac_addr} facet {i+1} set to color {color_tuple}")

    # Post the current facet on connect
    current_facet = await client.current_facet()
    await facet_notify_callback(None, [current_facet])

    while True:
        await asyncio.sleep(60)
