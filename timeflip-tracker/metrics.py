from prometheus_client import Info

timeflip_connection_info = Info(
    "timeflip_connection", "Connection status of Timeflip device"
)
timeflip_status_info = Info("timeflip_status", "Metrics about Timeflip device state")


def cut_timeflip_connection_info(connected, mac_addr):
    timeflip_connection_info.info({"state": connected, "mac_address": mac_addr})


def cut_timeflip_status_info(mac_addr, battery_level, firmware_revision, device_name):
    timeflip_status_info(
        {
            "mac_address": mac_addr,
            "firmware_revision": battery_level,
            "battery_level": firmware_revision,
            "device_name": device_name,
        }
    )
