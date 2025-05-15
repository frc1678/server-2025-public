#!/usr/bin/env python3
"""Calculates scout precisions to determine scout accuracy compared to TBA."""

from calculations.base_calculations import BaseCalculations
import tba_communicator
import utils
import logging
from timer import Timer
from typing import Union, Dict, List
import override

log = logging.getLogger(__name__)


class ScoutPrecisionCalc(BaseCalculations):
    def __init__(self, server):
        super().__init__(server)
        self.watched_collections = ["unconsolidated_totals"]
        self.overall_schema = utils.read_schema("schema/calc_scout_precision_schema.yml")

    def calc_scout_precision(
        self, scout_sims: List[Dict[str, Union[str, int, float]]]
    ) -> Dict[str, float]:
        """Averages all of a scout's in-match errors to get their overall error in a competition.

        `scout_sims`: list of dicts of `sim_precision` documents for one scout

        Returns a dictionary with SPR values averaged across all documents in `scout_sims`.
        """
        calculations = {}
        for calculation, schema in self.overall_schema["calculations"].items():
            required = schema["requires"]
            datapoint = required.split(".")[1]
            all_sim_errors = []
            for document in scout_sims:
                if document.get(datapoint) is not None:
                    all_sim_errors.append(abs(document[datapoint]))
            if all_sim_errors:
                calculations[calculation] = self.avg(all_sim_errors)
        return calculations

    def calc_ranks(
        self, scouts: List[Dict[str, Union[int, str]]]
    ) -> List[Dict[str, Union[int, str]]]:
        """Ranks a scout based on their overall precision.

        `scouts`: output from `calc_scout_precision()`; a list of dicts containing scout names and SPR values

        Returns the same format of list of dicts with an added key-value pair denoting each scout's rank.
        """
        for rank, schema in self.overall_schema["ranks"].items():
            for scout in scouts:
                # If there is no scout precision, set it to None
                if schema["requires"].split(".")[1] not in scout.keys():
                    scout[schema["requires"].split(".")[1]] = None

            # This is a bit complex, but works as follows. It constructs a tuple for every scout in the list, where the first value
            # is whether the scout precision is None, and the second is the value itself. Tuples are sorted item by item, so those
            # with False as the first value (if its not None) will come before those where it is true (if it is None), because False < True
            scouts = sorted(
                scouts,
                key=lambda s: (
                    s[schema["requires"].split(".")[1]] is None,
                    s[schema["requires"].split(".")[1]],
                ),
            )

            # Go through the list and assign the ranks accordingly
            for i in range(len(scouts)):
                scouts[i][rank] = i + 1

            # Delete scout_precision if it is None (So it doesn't break validation)
            for scout in scouts:
                if scout[schema["requires"].split(".")[1]] == None:
                    del scout[schema["requires"].split(".")[1]]

        return scouts

    def update_scout_precision_calcs(self, scouts: set) -> List[Dict[str, Union[int, str]]]:
        """Creates overall scout precision updates.

        `scouts`: output from `find_updated_scouts`

        Returns a list of scout precision dicts to be updated to the database.
        """
        updates = []
        for scout in scouts:
            scout_sims = self.server.local_db.find("sim_precision", {"scout_name": scout})
            update = {}
            update["scout_name"] = scout
            if scout_precision := self.calc_scout_precision(scout_sims):
                update.update(scout_precision)
            updates.append(update)
        updates = self.calc_ranks(updates)
        return updates

    def run(self):
        "Runs SPR calculations on data from MongoDB"
        timer = Timer()

        scouts = set(map(lambda doc: doc["scout_name"], self.server.local_db.find("sim_precision")))

        self.server.local_db.delete_data("scout_precision")
        self.server.local_db.insert_documents(
            "scout_precision", self.update_scout_precision_calcs(scouts)
        )

        override.apply_override("scout_precision")

        timer.end_timer(__file__)
