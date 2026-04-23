import asyncio
import sys
from typing import Any, Callable, Coroutine, List, Tuple

from bleak import BleakClient, BleakError, BleakScanner
from bleak.backends.device import BLEDevice
from bluetooth_adapters import get_adapters
from timeflip_tracker.colors import color_to_tuple, random_color_tuple
from timeflip_tracker.database import insert_event
from timeflip_tracker.logger import get_logger
from timeflip_tracker.actions import invoke_hook
from timeflip_tracker.metrics import cut_timeflip_connection_info, cut_timeflip_status_info
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

async def connect_and_run(
    device_config,
    adapter_addr=None,
):
    timeflip_logger = get_logger()
    mac_addr = device_config["mac_address"]


    def disconnect_callback(client: AsyncClient):
        timeflip_logger = get_logger()
        timeflip_logger.warning(f"Disconnected from {client.address}")
        cut_timeflip_connection_info("disconnected", client.address)

        if 'actions' in device_config and 'on_disconnect' in device_config['actions']:
            invoke_hook(device_config['actions']['on_disconnect'], [device_config['name'], device_config["mac_address"]])


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

                if 'actions' in device_config and 'on_connect' in device_config['actions']:
                    invoke_hook(device_config['actions']['on_connect'], [device_config['name'], device_config["mac_address"]])

                await actions_on_client(
                    device_config,
                    client,
                    password=device_config["password"],
                )

        except (BleakError, TimeFlipRuntimeError, RuntimeClientError, TimeoutError) as e:
            timeflip_logger.error(f"Communication error connecting to {mac_addr}. {e}")

        await asyncio.sleep(15)


async def actions_on_client(device_config, client: AsyncClient, password=None):
    mac_addr = device_config["mac_address"]
    timeflip_logger = get_logger()
    timeflip_logger.info(f"Connected to device {mac_addr}")
    last_reported_facet = None

    def handle_facet_event(facet_num):
        nonlocal last_reported_facet

        device_name = device_config["name"]
        device_address = device_config["mac_address"]
        facet_index = facet_num - 1
        configured_facets = device_config["facets"]

        if 0 <= facet_index < len(configured_facets):
            facet = configured_facets[facet_index]
            facet_value = facet["value"]
            facet_color = facet.get("color_tuple", color_to_tuple("white"))
        else:
            facet_value = "unassigned"
            facet_color = color_to_tuple("white")

        if facet_num != last_reported_facet:
            timeflip_logger.info(
                f"Device {device_name} ({device_address}) changed to facet {facet_num}: {facet_value}"
            )
            last_reported_facet = facet_num

        insert_event(
            device_name,
            device_address,
            facet_num,
            facet_value,
            facet_color)

        if 'actions' in device_config and 'on_facet_change' in device_config['actions']:
            invoke_hook(device_config['actions']['on_facet_change'], [device_name, device_address, facet_num, facet_value, facet_color])

    def setup_facet_callback(facet_num):
        handle_facet_event(facet_num)

    if password is not None:
        await client.setup(facet_callback=setup_facet_callback, password=password)
        timeflip_logger.info(f"Password communicated to {mac_addr}")

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

    # Post the current facet on connect
    current_facet = await client.current_facet()
    handle_facet_event(current_facet)

    while True:
        await asyncio.sleep(600)
        await timeflip_status(client)
