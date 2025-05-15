#!/usr/bin/env python3

import database
import server
import logging
import utils
import time
import json
from unittest.mock import patch
import tba_communicator

"""Uses the raw QRs in the cloud db to simulate a competition"""


log = logging.getLogger("comp_simulator")

tba_request_wrapper = tba_communicator.tba_request

if __name__ == "__main__":
    utils.confirm_comp()

    # set up stuff
    write_cloud = utils.input("Write to cloud db? (y/N): ").lower() == "y"
    use_cloud_qrs = (
        utils.input(
            f"Use cloud db raw_qr data? (otherwise, the script will attempt to read from data/{utils.TBA_EVENT_KEY}_raw_qr.json) (Y/n): "
        ).lower()
        != "n"
    )
    if use_cloud_qrs:
        cloud_db = database.BetterDatabase(utils.TBA_EVENT_KEY, write_cloud)
        real_raw_qrs = cloud_db.get_documents("raw_qr")
    else:
        real_raw_qrs = json.load(open(f"data/{utils.server_key()}_raw_qr.json"))
    current_match_number = 1
    s = server.Server(write_cloud)
    s.local_db.delete_data("raw_qr", bypass=True)
    s.calculations.pop(0)  # remove qr input :)
    while True:
        matches_to_simulate = int(utils.input("Number of matches to simulate: "))
        if matches_to_simulate == 0:
            break
        raw_qrs_to_upload = []

        with patch(
            "tba_communicator.tba_request",
            side_effect=lambda api_url: list(
                filter(
                    lambda match: "qm" in match["key"]
                    and match["match_number"] <= matches_to_simulate,
                    tba_request_wrapper(api_url),
                )
            )
            if api_url == f"event/{utils.TBA_EVENT_KEY}/matches"
            else tba_request_wrapper(api_url),
        ):
            for i in range(matches_to_simulate):
                # simulate the match data being entered
                log.info(f"Adding QRs from match {current_match_number}")

                # only add qrs if they are the correct match number
                for qr in real_raw_qrs:
                    if f"$B{current_match_number}$" in qr["data"].split("%")[0]:
                        qr.pop("_id")
                        raw_qrs_to_upload.append(qr)

                if raw_qrs_to_upload == []:
                    log.info(f"No more raw QRs (match {current_match_number})")
                    continue
                current_match_number += 1
            # add the raw qrs to the local db
            s.local_db.insert_documents("raw_qr", raw_qrs_to_upload)

            s.run_calculations()
            if s.write_cloud:
                for collection in s.VALID_COLLECTIONS:
                    curr_time = time.time()

                    data = s.local_db.find(collection)

                    if data:
                        s.cloud_db.delete_documents(collection, dict(), bypass_raw=True)

                        cleaned_data = []
                        for item in data:
                            item.pop("_id")
                            cleaned_data.append(item)

                        s.cloud_db.insert_documents(collection, cleaned_data)

                        log.info(
                            f"Inserted collection {collection} into the cloud DB. ({round(time.time() - curr_time, 1)} sec)"
                        )
                    else:
                        log.error(
                            f"No data found in collection {collection} in local DB, cannot update to the cloud DB."
                        )
