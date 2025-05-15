#!/usr/bin/env python3
# Copyright (c) 2024 FRC Team 1678: Citrus Circuits
"""Holds functions used to determine auto scoring and paths in each match"""

from typing import List, Dict, Union, Any, Tuple
from calculations.base_calculations import BaseCalculations
import logging
import utils
from timer import Timer
import copy
import override

log = logging.getLogger(__name__)


class AutoPIMCalc(BaseCalculations):
    schema = utils.read_schema("schema/calc_auto_pim.yml")
    obj_tim_schema = utils.read_schema("schema/calc_obj_tim_schema.yml")

    def __init__(self, server):
        super().__init__(server)
        self.watched_collections = ["unconsolidated_obj_tim", "sim_precision"]

    def get_unconsolidated_auto_timelines(
        self, unconsolidated_obj_tims: List[Dict[str, List[dict]]]
    ) -> Tuple[List[List[dict]], Union[int, None]]:
        """Given unconsolidated_obj_tims, returns unconsolidated auto timelines
        and the index of the best scout's timeline"""

        unconsolidated_auto_timelines = []
        best_sim_precision, best_scout_index = None, 0
        # Extract auto timelines
        for i, unconsolidated_tim in enumerate(unconsolidated_obj_tims):
            sim = {
                key: unconsolidated_tim[key]
                for key in ["team_number", "match_number", "scout_name"]
            }
            unconsolidated_auto_timelines.append(
                [
                    action
                    for action in unconsolidated_tim["timeline"]
                    if action["in_teleop"] == False
                ]
            )
            sim_precision: List[Dict[str, float]] = self.server.local_db.find("sim_precision", sim)
            if len(sim_precision) == 0:
                continue
            elif "sim_precision" not in sim_precision[0]:
                continue
            else:
                if len(sim_precision) > 1:
                    log.error(f"multiple sim_precisions found for {sim}, taking first option")
                precision = abs(sim_precision[0]["sim_precision"])
                if best_sim_precision is None or precision < best_sim_precision:
                    best_sim_precision = precision
                    best_scout_index = i
        return unconsolidated_auto_timelines, best_scout_index

    def consolidate_timelines(
        self, unconsolidated_timelines: List[List[dict]], has_preload: bool
    ) -> List[dict]:
        """Given a list of unconsolidated auto timelines and the index of the best scout's timeline
        (output from the get_unconsolidated_auto_timelines function), consolidates the timelines into a single timeline.

        If two timelines are the same, use that timeline.
        Else, choose timeline from scout with highest SPR.
        """

        ut = unconsolidated_timelines  # alias
        consolidated_timeline = []
        lengths = [len(timeline) for timeline in ut]
        is_sus = False

        robot_inventory = (
            ["C"] if has_preload else []
        )  # used to detect whether an action is impossible or not
        for i in range(max(lengths)):
            actions = []
            for j in range(len(ut)):
                if len(ut[j]) > i:
                    actions.append(
                        ut[j][i]["action_type"][5:]
                        if "fail" in ut[j][i]["action_type"]
                        else ut[j][i]["action_type"]
                    )
                else:
                    actions.append("")
            actions_list = copy.deepcopy(actions)
            consolidated_action = ""
            while consolidated_action == "":
                mode_actions = BaseCalculations.modes(actions_list)
                if len(mode_actions) == 1:  # should only happen if two or more scouts agree
                    if mode_actions[0] == "":
                        break
                    consolidated_action = mode_actions[0]
                else:  # no scouts agree
                    is_sus = True
                    consolidated_action = actions_list[
                        0
                    ]  # use the first scout, but we'll check if it's a possible action
                if consolidated_action in list(
                    self.schema["--timeline_fields"]["intake_position"]["valid_actions"].keys()
                ):
                    # the robot intook something
                    piece = (
                        "C"
                        if "coral" in consolidated_action or "station" in consolidated_action
                        else "A"
                    )
                    if piece not in robot_inventory:  # check if the action is possible
                        robot_inventory.append(piece)
                        break
                elif consolidated_action in list(
                    self.schema["--timeline_fields"]["score"]["valid_actions"].keys()
                ):
                    # the robot scored something
                    piece = (
                        "C"
                        if "coral" in consolidated_action or "_F" in consolidated_action
                        else "A"
                    )
                    if piece in robot_inventory:  # check if the action is possible
                        robot_inventory.remove(piece)
                        break
                # if it makes it here, that means that the action must have been impossible.
                # so we remove the impossible action and try again
                actions_list.remove(consolidated_action)
                consolidated_action = ""
                if len(actions_list) == 0:
                    break
            if consolidated_action == "":
                break
            # add the agreed-upon action to the timeline
            consolidated_timeline.append(ut[actions.index(consolidated_action)][i])

        if len(ut) < 3:
            is_sus = True

        return consolidated_timeline, is_sus

    def get_consolidated_tim_fields(self, calculated_tim: dict) -> dict:
        "Given a calculated_tim, return tim fields directly from other collections"
        # Auto variables we collect
        tim_fields = self.schema["tim_fields"]

        tim_auto_values = {}
        for field in tim_fields:
            collection, datapoint = field.split(".")
            if collection == "obj_tim":
                tim_auto_values[datapoint] = calculated_tim[datapoint]
            else:
                # Get data from other collections, such as subj_team or tba_tim
                data: List[dict] = self.server.local_db.find(
                    collection,
                    {
                        "match_number": calculated_tim["match_number"],
                        "team_number": calculated_tim["team_number"],
                    },
                )
                try:
                    tim_auto_values[datapoint] = data[0][datapoint]
                except:
                    tim_auto_values[datapoint] = None
                    log.critical(
                        f"{field} not found for {calculated_tim['team_number']} in match {calculated_tim['match_number']}"
                    )

        return tim_auto_values

    def create_auto_fields(self, tim: dict) -> dict:
        """Creates auto fields for one tim such as score_1, intake_1, etc using the consolidated_timeline"""
        # counters to cycle through scores and intakes
        counts = {field: 0 for field in self.schema["--timeline_fields"]}
        # set all fields to None (in order to not break exports)
        update = {}
        for field, info in self.schema["--timeline_fields"].items():
            for i in range(info["max_count"]):
                update[f"{field}_{i + 1}"] = "none"

        # For each action in the consolidated timeline, add it to one of the new fields (if it applies)
        for action in tim["auto_timeline"]:
            # BUG: action_type sometimes doesn't exist for a timeline action
            if action.get("action_type") is None:
                log.warning("action_type does not exist")
                continue
            # BUG: action_type can sometimes be null, need better tests in auto_pim, more edge cases
            elif action["action_type"] is None:
                log.warning("action_type is null")
                continue
            # Iterate through each timeline_field
            for field, info in self.schema["--timeline_fields"].items():
                # Check if the action is one of the valid actions for this field
                if action["action_type"] in info["valid_actions"].keys():
                    # Iterate to the next datapoint for that field
                    counts[field] += 1
                    # Calculate the value for the field
                    update[f"{field}_{counts[field]}"] = self.calculate_action(
                        action["action_type"], info["valid_actions"]
                    )
        return update

    def calculate_action(self, action: str, action_dict):
        "Given an action type (e.g. score_speaker), return the short-form name used in auto_pims (e.g. speaker)"
        # Iterate through possible action types
        # Return the short-form name if the full name matches
        for full_name, new_name in action_dict.items():
            if action == full_name:
                return new_name

        # Log if action type is invalid
        log.error(f"{action} is not a valid action type")
        return "none"

    def score_fail_type(self, unconsolidated_tims: List[Dict]):
        """This function is required in auto_pims because the unconsolidated_obj_tim collection has timelines
        which have not had fails calculated yet, but fails need to be calculated so that successes works
        """
        for num_1, tim in enumerate(unconsolidated_tims):
            timeline = tim["timeline"]
            # Collects the data for score_fails for amp, and speaker.
            for num, action_dict in enumerate(timeline):
                if action_dict["action_type"] == "fail":
                    for score_type, new_value in self.obj_tim_schema["--fail_actions"].items():
                        if (
                            unconsolidated_tims[num_1]["timeline"][num + 1]["action_type"]
                            == score_type
                        ):
                            unconsolidated_tims[num_1]["timeline"][num + 1][
                                "action_type"
                            ] = new_value["name"]
        return unconsolidated_tims

    def calculate_auto_pims(self, tims: List[dict]) -> List[dict]:
        """Calculates auto data for the given tims, which looks like
        [{"team_number": 1678, "match_number": 42}, {"team_number": 1706, "match_number": 56}, ...]
        """
        calculated_pims = []
        for tim in tims:
            # Get data for the tim from MongoDB
            unconsolidated_obj_tims: List[dict] = self.server.local_db.find(
                "unconsolidated_obj_tim", tim
            )
            obj_tim: dict = self.server.local_db.find("obj_tim", tim)
            if len(obj_tim) > 0:
                obj_tim = obj_tim[0]
            else:
                log.critical(
                    f"no obj_tim data for {tim['team_number']} in match {tim['match_number']}"
                )
                continue

            # Run calculations on the team in match
            tim.update(self.get_consolidated_tim_fields(obj_tim))
            timeline, is_sus = self.consolidate_timelines(
                self.get_unconsolidated_auto_timelines(
                    self.score_fail_type(unconsolidated_obj_tims)
                )[0],
                obj_tim["has_preload"],
            )
            tim.update({"auto_timeline": timeline, "is_sus": is_sus})
            tim.update(self.create_auto_fields(tim))
            obj_tims = self.server.local_db.find(
                "obj_tim", {"team_number": tim["team_number"], "match_number": tim["match_number"]}
            )
            # Data that is later updated by auto_paths
            tim.update(
                {
                    "match_numbers_played": [],
                    "num_matches_ran": 0,
                    "path_number": 0,
                    "is_compatible": self.is_compatible(timeline, obj_tims),
                }
            )

            calculated_pims.append(tim)
        return calculated_pims

    def is_compatible(self, auto_data, obj_tims):
        return any([tims["start_position"] in {"2", "3", "4"} for tims in obj_tims]) and any(
            [
                any(
                    [score in path["action_type"] for score in ["score_F1", "score_F2", "score_F6"]]
                )
                for path in auto_data
            ]
        )

    def run(self):
        """Executes the auto_pim calculations"""
        timer = Timer()

        tims = []

        for document in self.server.local_db.find(self.watched_collections[0]):
            # Check that the entry is an unconsolidated_obj_tim
            if "timeline" not in document.keys() or "team_number" not in document.keys():
                continue

            # Check that the team is in the team list, ignore team if not in teams list
            team_num = document["team_number"]
            if team_num not in self.teams_list:
                log.warning(f"team number {team_num} is not in teams list")
                continue

            # Make tims list
            tims.append(
                {
                    "team_number": team_num,
                    "match_number": document["match_number"],
                }
            )

        # Filter duplicate tims
        unique_tims = utils.unique_ld(tims)

        self.server.local_db.delete_data("auto_pim")

        self.server.local_db.insert_documents("auto_pim", self.calculate_auto_pims(unique_tims))

        override.apply_override("auto_pim")

        timer.end_timer(__file__)
