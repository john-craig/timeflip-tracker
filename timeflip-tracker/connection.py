import asyncio
import sys
from typing import Any, Callable, Coroutine, List, Tuple

from bleak import BleakClient, BleakError, BleakGATTCharacteristic, BleakScanner
from bleak.backends.device import BLEDevice
from bluetooth_adapters import get_adapters
from colors import color_to_tuple, random_color_tuple
from database import insert_event
from logger import get_logger
from metrics import cut_timeflip_connection_info, cut_timeflip_status_info
from pytimefliplib.async_client import (
    CHARACTERISTICS,
    DEFAULT_PASSWORD,
    AsyncClient,
    TimeFlipRuntimeError,
)


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


async def timeflip_status(client):
    mac_addr = client.address
    firmware_revision = await client.firmware_revision()
    battery_level = await client.battery_level()
    internal_device_name = await client.device_name()

    timeflip_logger = get_logger()
    timeflip_logger.debug(
        f"Device {mac_addr} firmware revision {firmware_revision}, battery level {battery_level}, device_name {internal_device_name}"
    )

    cut_timeflip_status_info(
        mac_addr, firmware_revision, battery_level, internal_device_name
    )


def disconnect_callback(client: AsyncClient):
    timeflip_logger = get_logger()
    timeflip_logger.warning(f"Disconnected from {client.address}")
    cut_timeflip_connection_info("disconnected", client.address)


async def connect_and_run(
    device_config,
    adapter_addr=None,
):
    mac_addr = device_config["mac_address"]

    timeflip_logger = get_logger()

    adapter_path = None
    if adapter_addr:
        timeflip_logger.debug(f"Attempting to find path for adapter {adapter_addr}")
        bluetooth_adapters = get_adapters()
        await bluetooth_adapters.refresh()

        timeflip_logger.debug(f"Found adapters:\n{bluetooth_adapters.adapters}")

        for adapter_key in bluetooth_adapters.adapters:
            adapter_obj = bluetooth_adapters.adapters[adapter_key]

            if "address" in adapter_obj and adapter_obj["address"] == adapter_addr:
                adapter_path = adapter_key
                timeflip_logger.debug(
                    f"Matched path {adapter_path} for adapter {adapter_addr}"
                )

    # for now just always try to reconnect until we're killed
    while True:
        try:
            async with AsyncClient(
                device_config["mac_address"],
                disconnected_callback=disconnect_callback,
                adapter=adapter_path,
            ) as client:
                # setup
                timeflip_logger.info(f"Connected to {mac_addr}")
                cut_timeflip_connection_info("connected", client.address)

                await client.setup(password=device_config["password"])
                timeflip_logger.info(f"Password communicated to {mac_addr}")

                await actions_on_client(device_config, client)

        except (BleakError, TimeFlipRuntimeError, RuntimeClientError) as e:
            timeflip_logger.error(f"Communication error connecting to {mac_addr}. {e}")

        await asyncio.sleep(30)


async def actions_on_client(device_config, client: AsyncClient):
    mac_addr = device_config["mac_address"]
    timeflip_logger = get_logger()
    timeflip_logger.info(f"Connected to device {mac_addr}")

    await timeflip_status(client)

    disco_colors = (
        "default_color" in device_config and device_config["default_color"] == "disco"
    )
    timeflip_logger.debug(f"Disco colors for device {mac_addr}: {disco_colors}")
    default_color_tuple = (
        color_to_tuple("white")
        if "default_color" not in device_config or disco_colors
        else color_to_tuple(device_config["default_color"])
    )

    for i in range(0, 12):
        color_tuple = default_color_tuple if not disco_colors else random_color_tuple()

        if i < len(device_config["facets"]):
            facet = device_config["facets"][i]

            if "color" in facet:
                color_tuple = color_to_tuple(facet["color"])

            facet["color_tuple"] = color_tuple
            device_config["facets"][i] = facet

        await client.set_color(i, color_tuple)
        timeflip_logger.debug(
            f"Device {mac_addr} facet {i+1} set to color {color_tuple}"
        )

    async def facet_notify_callback(sender: BleakGATTCharacteristic, event_data):
        facet_num = event_data[0]

        if facet_num >= len(device_config["facets"]):
            # Set to a value that was not defined
            insert_event(
                device_config["name"],
                device_config["mac_address"],
                facet_num,
                "unassigned",
                color_to_tuple("white"),
            )
        else:
            insert_event(
                device_config["name"],
                device_config["mac_address"],
                facet_num,
                device_config["facets"][facet_num - 1]["value"],
                device_config["facets"][facet_num - 1]["color_tuple"],
            )

    await client.register_notify_facet_v3(facet_notify_callback)

    # Post the current facet on connect
    current_facet = await client.current_facet()
    await facet_notify_callback(None, [current_facet])

    while True:
        await asyncio.sleep(600)
        await timeflip_status(client)
