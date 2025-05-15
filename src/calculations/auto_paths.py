#!/usr/bin/env python3

"""
Holds functions used to determine auto scoring and paths

1. Collect all existing pims
2. Group by team, start position, and scoring
3. Calculate success and score info for each unique auto
4. Add unique paths to database
"""

from typing import List
from calculations.base_calculations import BaseCalculations
import logging
import console
import utils
from timer import Timer
import override

log = logging.getLogger(__name__)


class AutoPathCalc(BaseCalculations):
    schema = utils.read_schema("schema/calc_auto_paths.yml")

    def __init__(self, server):
        super().__init__(server)
        self.watched_collections = ["auto_pim"]

    def group_auto_paths(self, pim: dict, calculated_paths: List[dict]) -> dict:
        """
        Creates an auto path given a pim and a list of existing paths.
        Checks if the new pim already has an existing path or if it's a new path.
        """
        # Find all current auto paths with this team number and start position
        current_documents: List[dict] = self.server.local_db.find(
            "auto_paths",
            {"team_number": pim["team_number"]},
        )
        # Add the current calculated_tims into current documents (because these tims aren't in server yet)
        current_documents.extend(
            [
                calculated_path
                for calculated_path in calculated_paths
                if (calculated_path["team_number"] == pim["team_number"])
            ]
        )

        path = {"team_number": pim["team_number"]}

        # Finy any matching paths
        for document in current_documents:
            # Checks to see if it's the same path
            if self.is_same_path(pim, document):
                # Set path values to pim
                for field in self.schema["--path_groups"]["exact_match"]:
                    # Don't update if failed score unless old path doesn't have any info there
                    if "fail" not in str(pim[field]) or document[field] == "none":
                        path[field] = pim[field]
                    else:
                        path[field] = document[field]

                # Add number of score successes
                for new_datapoint, count_datapoint in self.schema["path_increment"].items():
                    # Must have scored to increment
                    for name, values in count_datapoint.items():
                        if name != "type":
                            if pim[name] in values:
                                path[new_datapoint] = document[new_datapoint] + 1
                            else:
                                path[new_datapoint] = document[new_datapoint]

                # Increment all information
                path["num_matches_ran"] = document["num_matches_ran"] + 1
                path["match_numbers_played"] = [pim["match_number"]]
                path["match_numbers_played"].extend(document["match_numbers_played"])
                path["path_number"] = document["path_number"]
                path["timeline"] = document["timeline"]
                path["is_sus"] = pim["is_sus"] if document["is_sus"] else False
                break
        else:
            # If there are no matching documents, that means this is a new auto path
            path["num_matches_ran"] = 1
            path["path_number"] = len(current_documents) + 1
            path["match_numbers_played"] = [pim["match_number"]]
            path["is_sus"] = pim["is_sus"]
            for field in self.schema["--path_groups"]["exact_match"]:
                path[field] = pim[field]

            timeline = []
            intake_count = 1
            score_count = 1
            for action in pim["auto_timeline"]:
                try:
                    if "intake" in action["action_type"]:
                        timeline.append(path[f"intake_position_{intake_count}"])
                        intake_count += 1
                    else:
                        timeline.append(path[f"score_{score_count}"])
                        score_count += 1
                except:
                    continue
            path["timeline"] = str(timeline)

            # Start at 1 for each incremented datapoint if it a success, else a 0
            for new_datapoint, count_datapoint in self.schema["path_increment"].items():
                # All conditions must be true to increment
                for name, values in count_datapoint.items():
                    if name != "type":
                        if pim[name] in values:
                            path[new_datapoint] = 1
                        else:
                            path[new_datapoint] = 0
        return path

    def is_same_path(self, pim: dict, document: dict) -> bool:
        """Finds if the tim path is the same as the document path"""
        # All exact path_groups in schema must have the same value
        for datapoint in self.schema["--path_groups"]["exact_match"]:
            # If score was fail, count it as the same
            if (
                pim[datapoint]
                if not isinstance(pim[datapoint], str) or "fail" not in pim[datapoint]
                else pim[datapoint][5:]
            ) != (
                document[datapoint]
                if not isinstance(pim[datapoint], str) or "fail" not in document[datapoint]
                else document[datapoint][5:]
            ):
                return False
        return True

    def update_auto_pims(self, path: dict) -> None:
        """Updates existing auto pims with incremented path number and num matches ran"""
        update = {"path_number": path["path_number"], "num_matches_ran": path["num_matches_ran"]}
        query = {
            "match_number": {"$in": path["match_numbers_played"]},
            "team_number": path["team_number"],
            "start_position": path["start_position"],
        }
        self.server.local_db.update_many("auto_pim", update, query)

    def is_updated_path(self, new_path, old_path):
        "Checks if new_path is an updated version of old_path. Used in calculate_auto_paths() below."
        # Check if old path is a subset of new path
        if new_path["team_number"] == old_path["team_number"]:
            if set(old_path["match_numbers_played"]).issubset(
                set(new_path["match_numbers_played"])
            ):
                return True
        return False

    def calculate_auto_paths(self, empty_pims: List[dict]) -> List[dict]:
        """Calculates auto data for the given empty pims, which looks like
        [{"team_number": "1678", "match_number": 42}, {"team_number": "1706", "match_number": 56}, ...]
        """
        calculated_paths = []
        for pim in empty_pims:
            auto_pims: List[dict] = self.server.local_db.find("auto_pim", pim)
            if len(auto_pims) != 1:
                log.error(f"Multiple pims found for {pim}")

            path = self.group_auto_paths(auto_pims[0], calculated_paths)
            # Check to see if an outdated version of the path is in calculated_paths and remove it
            for calculated_path in calculated_paths:
                if self.is_updated_path(path, calculated_path):
                    calculated_paths.remove(calculated_path)
            calculated_paths.append(path)

        for path in calculated_paths:
            self.update_auto_pims(path)
        return calculated_paths

    def run(self):
        """Executes the auto_path calculations"""
        timer = Timer()

        # Get oplog entries
        empty_pims = []

        for document in self.server.local_db.find(self.watched_collections[0]):
            if "team_number" not in document.keys():
                continue
            # Check that the team is in the team list, ignore team if not in teams list
            team_num = document["team_number"]
            if team_num not in self.teams_list:
                log.warning(f"auto_paths: team number {team_num} is not in teams list")
                continue

            # Make pims list
            empty_pims.append(
                {
                    "team_number": team_num,
                    "match_number": document["match_number"],
                }
            )

        # Filter duplicate pims
        unique_empty_pims = utils.unique_ld(empty_pims)

        self.server.local_db.delete_data("auto_paths")

        # Upload data to MongoDB
        self.server.local_db.insert_documents(
            "auto_paths", self.calculate_auto_paths(unique_empty_pims)
        )

        override.apply_override("auto_paths")

        timer.end_timer(__file__)
