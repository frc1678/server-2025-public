#!/usr/bin/env python3

import sys
import time
import logging
import utils

log = logging.getLogger("upload_to_tablets")

import adb_communicator


def send_file():
    if len(sys.argv) == 2:
        # Extract LOCAL_FILE_PATH from second argument
        # LOCAL_FILE_PATH is a string
        LOCAL_FILE_PATH = sys.argv[1]
    else:
        log.error(
            "Local APK file path is not being passed as an argument. Exiting...",
            file=sys.stderr,
        )
        sys.exit(1)

    DEVICES = adb_communicator.get_attached_devices()
    for serial in DEVICES:
        adb_communicator.send_file(serial[0], LOCAL_FILE_PATH)


if __name__ == "__main__":
    send_file()
