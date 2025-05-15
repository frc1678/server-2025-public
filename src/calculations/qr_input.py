"""This file houses a calculation class that allows the server to input data"""

import adb_communicator
import calculations.base_calculations
import utils
from ulid import ULID
import logging
import time
import sys
from timer import Timer

log = logging.getLogger(__name__)


class QRInput(calculations.base_calculations.BaseCalculations):
    def __init__(self, server):
        super().__init__(server)
        self.schema = utils.read_schema("schema/match_collection_qr_schema.yml")

    def upload_qr_codes(self, qr_codes):
        # Acquires current qr data
        qr_data = [qr_code["data"] for qr_code in self.server.local_db.find("raw_qr")]
        qr = set()
        duplicate_count = 0

        for qr_code in qr_codes:
            # Check for duplicate QR codes
            if qr_code in qr_data:
                duplicate_count += 1
                continue
            # Checks to make sure the qr is valid by checking its starting character
            elif qr_code.startswith(
                self.schema["subjective_aim"]["_start_character"]
            ) or qr_code.startswith(self.schema["objective_tim"]["_start_character"]):
                qr.add(qr_code)
            else:
                log.warning(f'Invalid QR code not uploaded: "{qr_code}"')
        if duplicate_count > 0:
            log.warning(f"{duplicate_count} duplicate QR codes not uploaded.")

        if qr != set():
            qr = [
                {
                    "data": qr_code,
                    "blocklisted": False,
                    "override": {},
                    "ulid": str(ULID()),
                    "readable_time": str(ULID().datetime),
                }
                for qr_code in qr
            ]
            self.server.local_db.insert_documents("raw_qr", qr)
        return qr

    def run(self, test_input=None):
        """Grabs QR codes from user using stdin.read(), each qr is separated by a newline"""
        timer = Timer()
        cleaned_qr_codes = False

        # If test_input is assigned to a value (in tests), set qr_codes to test_input.
        # Otherwise, get input from user.
        # Used because there is no good way to test stdin.read()
        if test_input:
            qr_codes = test_input
            uploaded_qrs = self.upload_qr_codes(qr_codes)
        else:
            cleaned_qr_codes = []
            utils.print("ENTER DATA: ")
            qr_codes = (
                sys.stdin.read()
            )  # stdin.read() is used so that pressing enter does not end the input; use CTRL+D instead
            for qr in qr_codes.strip().split("\n"):
                if not qr:
                    continue
                qr = qr.upper()
                if qr[0] == "Q":
                    qr = qr[1:]
                cleaned_qr_codes.append(qr)

            # THIS CODE IS HERE IN CASE CTRL+D BREAKS
            # qr_codes = []
            # while True:
            #     line = sys.stdin.readline().strip().upper()
            #     if line:
            #         if line[0] == "Q":
            #             line = line[1:]
            #     if line == "STOP":
            #         break
            #     qr_codes.append(line)

        # Upload qr codes as list
        if cleaned_qr_codes:
            uploaded_qrs = self.upload_qr_codes(cleaned_qr_codes)
        else:
            uploaded_qrs = []
        # Let the server operator know that it's safe to clear the QR scanners
        utils.print(f"Uploaded {len(uploaded_qrs)} new raw QRs to the local DB", justify="center")
        time.sleep(1)

        adb_communicator.pull_qrs()
        adb_communicator.pull_pit_data()
        adb_communicator.pull_ss_data(self.server.local_db)

        timer.end_timer(__file__)
