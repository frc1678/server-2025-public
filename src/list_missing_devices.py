#!/usr/bin/env python3

"""Elegantly displays attached and missing devices."""

import adb_communicator

from console import console
import logging
import utils

log = logging.getLogger("list_missing_devices")


def missing_devices():
    """Loops through device serials and checks if the device is connected

    prints in color based on missing status.
    """
    utils.print("Normally Pixel 3a #1-3 and Lenovo Tab E7 #1-28 should be here.", "yellow")
    utils.print(
        "Lenovo Tab E7 #29-33 are not included in the tablet cases unless tablets have been switched out."
    )
    devices = adb_communicator.get_attached_devices()
    # Counter for all connected devices
    total_devices_connected = 0
    total_unauthorized_devices = 0
    if not devices:
        status = 0
    # Gets all devices
    for device in adb_communicator.DEVICE_SERIAL_NUMBERS:
        # Checks if device is connected and connection status
        # `connection` is a list of device serial and connection status
        for connection in devices:
            if device not in connection[0]:
                status = 0
            elif connection[1] == "unauthorized":
                status = 1
                total_devices_connected += 1
                total_unauthorized_devices += 1
                break
            else:
                status = 2
                total_devices_connected += 1
                break

        if status == 0:
            utils.print(f"{adb_communicator.DEVICE_SERIAL_NUMBERS[device]}", "red")
        elif status == 1:
            utils.print(f"{adb_communicator.DEVICE_SERIAL_NUMBERS[device]}", "yellow")
        else:
            utils.print(f"{adb_communicator.DEVICE_SERIAL_NUMBERS[device]}", "green")

    log.info(f"Total Devices Connected: {total_devices_connected}")
    log.info(f"Total Unauthorized Devices: {total_unauthorized_devices}")
    if not devices:
        utils.print(f"WARNING: No devices connected", "red")


if __name__ == "__main__":
    missing_devices()
