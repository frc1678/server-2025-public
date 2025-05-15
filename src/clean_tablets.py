#!/usr/bin/env python3

"""Standardizes tablet font size, deletes old data, and uninstalls apps."""

import adb_communicator
import os
import utils
import shutil
import logging

log = logging.getLogger("clean_tablets")


class TabletClean:
    """Clean local data copied over from tablets"""

    def __init__(self, tablet_data_path="data/devices"):
        """Set default settings for tablet data path and default font size

        Both of the values have defaults and can be overwritten by parameters.
        This is to have the default settings run without change in this script
        but also have the ability to be run by other files with deferent
        defaults"""
        self.tablet_data_path = tablet_data_path

    def clean_local_tablet_directory(self):
        """Cleans out files in the data/devices directory on the server computer."""
        # Checks if the directory exists
        if os.path.isdir(self.tablet_data_path):
            # Deletes the directory
            shutil.rmtree(self.tablet_data_path)
            log.info(f"Deleted all files in {self.tablet_data_path}")
        # Creates the tablet directory again
        utils.create_file_path(self.tablet_data_path, True)


def clean_tablets_function():
    FILE_PATH = utils.create_file_path("data/devices")
    DEVICES = adb_communicator.get_attached_devices()
    APK_NAMES = [
        "com.frc1678.match_collection",
        "com.citruscircuits.overrate",
        "com.frc1678.driver_practice",
    ]
    num_cleaned = 0
    adb_communicator.adb_font_size_enforcer()

    clean_tablets = TabletClean()

    # Check if server operator wants to run through default process (delete everything)
    do_default = utils.input("Run default tablet clean process (deletes everything)? (y/n): ")
    if do_default.lower() == "y":
        # Clean local tablet data
        clean_tablets.clean_local_tablet_directory()

        # Delete tablet downloads
        adb_communicator.delete_tablet_downloads()

        # Uninstall match collection
        for device in DEVICES:
            adb_communicator.uninstall_app(device[0])
            log.info(
                f"Uninstalled Match Collection from {adb_communicator.DEVICE_SERIAL_NUMBERS[device[0]]}"
            )
            num_cleaned += 1
    else:
        # Checks if the server operator wants to delete tablet data
        delete_tablet_data = utils.input("Delete all local tablet data on this computer? (y/N): ")
        if delete_tablet_data.upper() == "Y":
            # Deletes tablet data from local tablet directory
            clean_tablets.clean_local_tablet_directory()

        delete_tablet_downloads = utils.input("Delete all tablet file downloads? (y/N): ")
        if delete_tablet_downloads.upper() == "Y":
            adb_communicator.delete_tablet_downloads()

        uninstall_match_collection = utils.input("Uninstall all apps from tablets? (y/N): ")
        if uninstall_match_collection.upper() == "Y":
            for device in DEVICES:
                for app in APK_NAMES:
                    adb_communicator.uninstall_app(device[0], app)
                    log.info(
                        f"Uninstalled app {app} from {adb_communicator.DEVICE_SERIAL_NUMBERS[device[0]]}"
                    )
                num_cleaned += 1
    log.info(f"{num_cleaned} devices cleaned")


if __name__ == "__main__":
    clean_tablets_function()
