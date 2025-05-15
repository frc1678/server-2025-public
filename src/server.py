#! /usr/bin/env python3

"""Contains the server class."""
import console  # DON'T DELETE THIS LINE. This initializes the logging system
import importlib
from typing import List, Type

import yaml
import json

from calculations import base_calculations
import database
import utils
import console
import logging
import os
import time
import doozernet_communicator

log = logging.getLogger("server")


class Server:
    """Contains the logic that runs calculations in proper order.

    Calculation classes should contain a `run` method that accepts one argument, an instance of this
    class. They should use the `db` attribute of this server class to communicate with the local
    database.
    """

    CALCULATIONS_FILE = utils.create_file_path("src/calculations.yml")
    TBA_EVENT_KEY = utils.load_tba_event_key_file(utils._TBA_EVENT_KEY_FILE)
    VALID_COLLECTIONS = [
        "auto_paths",
        "auto_pim",
        "obj_team",
        "obj_tim",
        "subj_team",
        "subj_tim",
        "tba_team",
        "tba_tim",
        "predicted_aim",
        "predicted_alliances",
        "predicted_team",
        # "predicted_elims",
        "pickability",
        # "raw_obj_pit",
        "raw_qr",
        "ss_tim",
        "ss_team",
        "scout_precision",
        "sim_precision",
        # "unconsolidated_totals",
        "unconsolidated_obj_tim",
        # "unconsolidated_ss_team",
        "data_accuracy",
        "scout_disagreements",
        "flagged_data",
    ]

    def __init__(self, write_cloud=False, has_internet=True):
        self.has_internet = has_internet
        if has_internet:
            self.dn_model = doozernet_communicator.check_model_availability()
        else:
            self.dn_model = None

        self.local_db = database.Database()
        if write_cloud:
            self.cloud_db = database.BetterDatabase(utils.server_key(), True)
        else:
            self.cloud_db = None
        self.write_cloud = write_cloud
        self.MATCH_SCHEDULE = utils.get_match_schedule()
        self.TEAM_LIST = utils.get_team_list()

        self.calculations = self.load_calculations()

    # TODO: optimize this function, this takes a really long time (especially on the old server computer)
    def load_calculations(self) -> List["base_calculations.BaseCalculations"]:
        """Imports calculation modules and creates instances of calculation classes."""

        # Prepare terminal
        print()

        with open(self.CALCULATIONS_FILE) as f:
            calculation_load_list = yaml.load(f, Loader=yaml.Loader)

        num_calcs = len(calculation_load_list)
        loaded_calcs = []

        count = 1
        # `calculations.yml` is a list of dictionaries, each with an "import_path" and "class_name"
        # key. We need to import the module and then get the class from the imported module.
        for calc in calculation_load_list:
            # If there is no internet, don't load modules that require internet
            if calc["needs_internet"] and not self.has_internet:
                utils.progress_bar(count, num_calcs)
                count += 1
                continue
            # Import the module
            try:
                module = importlib.import_module(calc["import_path"])
            except Exception as e:
                log.error(f'{e.__class__.__name__} importing {calc["import_path"]}: {e}')
                continue
            # Get calculation class from module
            try:
                cls: Type["base_calculations.BaseCalculations"] = getattr(
                    module, calc["class_name"]
                )
                # Append an instance of calculation class to the calculations list
                # We pass `self` as the only argument to the `__init__` method of the calculation
                # class so the calculations can get access to server instance variables such as the
                # oplog or the database
                loaded_calcs.append(cls(self))

                # Display progress bar
                utils.progress_bar(count, num_calcs)
                count += 1
            except Exception as e:
                log.error(
                    f'{e.__class__.__name__} instantiating {calc["import_path"]}.{calc["class_name"]}: {e}'
                )

        utils.print()
        return loaded_calcs

    def run_calculations(self):
        """Run each calculation in `self.calculations` in order"""
        for calc in self.calculations:
            calc.run()

    def run(self):
        """Starts server cycles, runs in infinite loop"""
        while True:
            self.run_calculations()
            if self.write_cloud:
                for collection in self.VALID_COLLECTIONS:
                    curr_time = time.time()

                    data = self.local_db.find(collection)

                    if data:
                        self.cloud_db.delete_documents(collection, dict(), bypass_raw=True)

                        cleaned_data = []
                        for item in data:
                            item.pop("_id")
                            cleaned_data.append(item)

                        self.cloud_db.insert_documents(collection, cleaned_data)

                        log.info(
                            f"Inserted collection {collection} into the cloud DB. ({round(time.time() - curr_time, 1)} sec)"
                        )
                    else:
                        log.error(
                            f"No data found in collection {collection} in local DB, cannot update to the cloud DB."
                        )


if __name__ == "__main__":
    utils.confirm_comp()

    has_internet = utils.has_internet()
    if not has_internet:
        write_cloud = False
        log.critical(
            "You are not connected to internet! In no-internet mode, only core calculations will run and updates will only show on the local DB."
        )
        while not os.path.isfile(f"data/{utils.TBA_EVENT_KEY}_match_schedule.json"):
            log.critical(f"No match schedule file found for {utils.TBA_EVENT_KEY}")
            utils.input("Press ENTER when you have created the match schedule file:")
        log.info(f"Match schedule found at {utils.TBA_EVENT_KEY}_match_schedule.json")
    else:
        write_cloud_question = utils.input("Write changes to cloud DB? (y/N): ").lower()
        if write_cloud_question in ["y", "yes"]:
            write_cloud = True
        else:
            write_cloud = False

        if write_cloud and not utils.in_production():
            utils.confirm_comp(
                "You're writing to the cloud DB, but you're NOT in production mode. Is this right?"
            )
    server = Server(write_cloud, has_internet)
    server.run()
