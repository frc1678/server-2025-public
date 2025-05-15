#!/usr/bin/env python3

"""Create match schedule and team list files and send them to devices.
Retrieve match schedule from TBA,
Create team list from match schedule,
send match schedule file to scout tablets over ADB,
and verify that the file is successfully transferred.
ADB stands for Android Debug Bridge.
"""

import hashlib
import json
import time
import sys
import adb_communicator
import tba_communicator
import utils
import logging
import os

log = logging.getLogger("send_device_jsons")


class SendDeviceJSONS:
    def __init__(self):
        self.LOCAL_MATCH_SCHEDULE_HASH = ""
        self.MATCH_SCHEDULE_LOCAL_PATH = utils.create_file_path(
            f"data/{utils.TBA_EVENT_KEY}_match_schedule.json"
        )
        self.MATCH_SCHEDULE_TABLET_PATH = "/storage/emulated/0/Download/match_schedule.json"
        self.TEAM_LIST_LOCAL_PATH = ""
        self.DEVICES_WITH_SCHEDULE = ""

    def validate_file(self, device_id, local_file_path, tablet_file_path):
        """Validates that `local_file_path` file was successfully transferred.
        Compares the `tablet_file_path` on the tablet to the locally stored
        version of the same file.
        Parameter 'device_id' is the serial number of the device
        """
        with open(self.MATCH_SCHEDULE_LOCAL_PATH, "rb") as match_schedule_file:
            # Store sha256 sum of match schedule
            self.LOCAL_MATCH_SCHEDULE_HASH = hashlib.sha256(match_schedule_file.read()).hexdigest()
        # Find the hash of `tablet_file_path`
        tablet_data = adb_communicator.get_tablet_file_path_hash(device_id, tablet_file_path)
        if local_file_path == self.MATCH_SCHEDULE_LOCAL_PATH:
            return tablet_data == self.LOCAL_MATCH_SCHEDULE_HASH
        raise ValueError(f"File path {local_file_path} not recognized.")

    def send_device_jsons_function(self):
        self.DEVICES_WITH_SCHEDULE = set()
        get_devices = adb_communicator.get_attached_devices()
        new_get_devices = []
        for device in get_devices:
            new_get_devices.append(device[0])
        self.DEVICES = set(new_get_devices)

        while True:
            # Wait for USB connection to initialize
            time.sleep(0.1)
            for device in self.DEVICES:
                device_name = adb_communicator.DEVICE_SERIAL_NUMBERS[device]
                if device not in self.DEVICES_WITH_SCHEDULE:
                    log.info(f"\nLoading {self.MATCH_SCHEDULE_LOCAL_PATH} onto {device_name}...")
                    if adb_communicator.push_file(
                        device,
                        self.MATCH_SCHEDULE_LOCAL_PATH,
                        self.MATCH_SCHEDULE_TABLET_PATH,
                        self.validate_file,
                    ):
                        self.DEVICES_WITH_SCHEDULE.add(device)
                        log.info(
                            f"Loaded match schedule to {self.MATCH_SCHEDULE_TABLET_PATH} on {device_name}"
                        )
                    else:
                        # Give both serial number and device name in warning
                        log.error(
                            f"FAILED sending {self.MATCH_SCHEDULE_LOCAL_PATH} to {device_name} ({device})"
                        )

            # Update connected devices before checking if program should exit
            get_devices = adb_communicator.get_attached_devices()
            new_get_devices = []
            for device in get_devices:
                new_get_devices.append(device[0])
            self.DEVICES = set(new_get_devices)
            if self.DEVICES == self.DEVICES_WITH_SCHEDULE:
                # Schedule has been loaded onto all connected devices
                if len(self.DEVICES_WITH_SCHEDULE) != 1:
                    log.info(
                        f"Match schedule loaded onto {len(self.DEVICES_WITH_SCHEDULE)} devices."
                    )
                else:
                    log.info("Match schedule loaded onto 1 device.")
            break


# Only upload schedules if file is ran, not imported
if __name__ == "__main__":
    # Prompt user
    utils.confirm_comp()

    send_jsons = SendDeviceJSONS()
    send_jsons.send_device_jsons_function()
