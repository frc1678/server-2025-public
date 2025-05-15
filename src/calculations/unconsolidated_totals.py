# Copyright (c) 2024 FRC Team 1678: Citrus Circuits


import copy
import utils
from calculations.base_calculations import BaseCalculations
from typing import List, Union, Dict
import logging
import tba_communicator
import json
from timer import Timer
import statistics
import calculations.obj_tims as obj_tims
import statistics
import database
import override

log = logging.getLogger(__name__)


class UnconsolidatedTotals(BaseCalculations):
    schema = utils.read_schema("schema/calc_obj_tim_schema.yml")
    type_check_dict = {"float": float, "int": int, "str": str, "bool": bool}

    def __init__(self, server):
        super().__init__(server)
        self.watched_collections = ["unconsolidated_obj_tim"]

    def pull_spr(event_key: str, scout: str, cloud: bool = True) -> dict:
        "Pulls a scout's SPR from the database, used for SPR consolidation"
        db = database.BetterDatabase(event_key, cloud)
        return db.get_documents("scout_precision", {"scout_name": scout})

    def merge_timeline_actions(self, tims: List[Dict]) -> list:
        """Combines actions such as auto_score_FX_LY into auto_coral_LY actions"""
        # loop through every tim
        for i in range(len(tims)):
            # loop through every timeline action
            for j in range(len(tims[i]["timeline"])):
                for action, eq_actions in self.schema["--merge_actions"].items():
                    # check if the timeline action can be changed to this action
                    if tims[i]["timeline"][j]["action_type"] in eq_actions["names"]:
                        tims[i]["timeline"][j]["action_type"] = action
                        break
        return tims

    def filter_timeline_actions(self, tim: dict, **filters) -> list:
        """Removes timeline actions that don't meet the filters and returns all the actions that do"""
        actions = tim["timeline"]
        for field, required_value in filters.items():
            if field == "time":
                # Times are given as closed intervals: either [0,134] or [135,150]
                actions = filter(
                    lambda action: required_value[0] <= action["time"] <= required_value[1],
                    actions,
                )
            else:
                # Removes actions for which action[field] != required_value
                actions = filter(lambda action: action[field] == required_value, actions)
            # filter returns an iterable object
            actions = list(actions)
        return actions

    def count_timeline_actions(self, tim: dict, **filters) -> int:
        """Returns the number of actions in one TIM timeline that meets the required filters"""
        return len(self.filter_timeline_actions(tim, **filters))

    def total_time_between_actions(
        self, tim: dict, start_action: str, end_action: str, min_time: int
    ) -> int:
        """Returns total number of seconds spent between two types of actions for a given TIM


        start_action and end_action are the names (types) of those two actions,
        such as start_incap and end_climb.
        min_time is the minimum number of seconds between the two types of actions that we want to count
        """
        # Separate calculation for scoring cycle times
        if start_action == "score":
            scoring_actions = self.filter_timeline_actions(tim, action_type=start_action)
            cycle_times = []

            # Calculates time difference between every pair of scoring actions
            for i in range(1, len(scoring_actions)):
                cycle_times.append(scoring_actions[i - 1]["time"] - scoring_actions[i]["time"])

            # Calculate median cycle time (if cycle times is not an empty list)
            if cycle_times:
                median_cycle_time = statistics.median(cycle_times)
            else:
                median_cycle_time = 0

            # Cycle time has to be an integer
            return round(median_cycle_time)

        # Intake related cycle times
        elif "intake" in start_action:
            start_end_pairs = []
            cycle_times = []

            # Creates pairs of [<start action>, <end action>]
            for action in tim["timeline"]:
                # Adds each start action to a new pair
                if action["action_type"] == start_action:
                    start_end_pairs.append([action])
                # If there is an incomplete pair, adds the end action
                elif (
                    len(start_end_pairs) >= 1
                    and action["action_type"] in end_action
                    and len(start_end_pairs[-1]) == 1
                ):
                    start_end_pairs[-1].append(action)
                # If something happens inbetween the start action and the end action, removes the incomplete pair
                elif (
                    len(start_end_pairs) >= 1
                    and action["action_type"] not in ["start_incap", "end_incap", "fail"]
                    and len(start_end_pairs[-1]) == 1
                ):
                    start_end_pairs.pop(-1)

            # Finds time between each pair of start action + end action
            c_pairs = copy.deepcopy(start_end_pairs)
            for index, pair in enumerate(start_end_pairs):
                if len(pair) != 2:
                    c_pairs.pop(index)
                    continue

                start = pair[0]
                end = pair[1]
                time_difference = start["time"] - end["time"]
                if time_difference >= min_time:
                    cycle_times.append(time_difference)

            start_end_pairs = c_pairs
            # Calculate median cycle time (if cycle times is not an empty list)
            if cycle_times:
                median_cycle_time = statistics.median(cycle_times)
            else:
                median_cycle_time = 0

            # Cycle time has to be an integer
            return round(median_cycle_time)

        # Other time calculations (incap)
        else:
            start_actions = self.filter_timeline_actions(tim, action_type=start_action)
            end_actions = []
            # Takes multiple end actions
            if isinstance(end_action, list):
                for action in end_action:
                    end_actions = end_actions + self.filter_timeline_actions(
                        tim, action_type=action
                    )
            else:
                end_actions = self.filter_timeline_actions(tim, action_type=end_action)
            # Match scout app should automatically add an end action at the end of the match,
            # if there isn't already an end action after the last start action. That way there are the
            # same number of start actions and end actions.
            total_time = 0
            for start, end in zip(start_actions, end_actions):
                if start["time"] - end["time"] >= min_time:
                    total_time += start["time"] - end["time"]
            return total_time

    def calculate_tim_counts(self, unconsolidated_tims: dict) -> dict:
        """Given a list of unconsolidated TIMs, returns the calculated count based data fields"""
        calculated_tim = {}
        self.score_fail_type(unconsolidated_tims)
        for calculation, filters in self.schema["timeline_counts"].items():
            unconsolidated_counts = []
            # Variable type of a calculation is in the schema, but it's not a filter
            filters_ = copy.deepcopy(filters)
            expected_type = filters_.pop("type")
            for tim in unconsolidated_tims:
                # Override timeline counts at consolidation
                new_count = 0
                if calculation not in tim["override"]:  # If no overrides
                    new_count = self.count_timeline_actions(tim, **filters_)
                else:
                    for key in list(tim["override"].keys()):
                        if (
                            key == calculation
                        ):  # If datapoint in overrides matches calculation being counted
                            # if override begins with += or -=, add or subtract respectively instead of just setting
                            if isinstance(tim["override"][calculation], str):
                                # removing "+=" and setting override[edited_datapoint] to the right type
                                if tim["override"][calculation][0:2] == "+=":
                                    tim["override"][calculation] = tim["override"][calculation][2:]
                                    if tim["override"][calculation].isdecimal():
                                        tim["override"][calculation] = int(
                                            tim["override"][calculation]
                                        )
                                    elif (
                                        "." in tim["override"][calculation]
                                        and tim["override"][calculation]
                                        .replace(".", "0", 1)
                                        .isdecimal()
                                    ):
                                        tim["override"][calculation] = float(
                                            tim["override"][calculation]
                                        )
                                    # "adding" to the original value
                                    tim["override"][calculation] += self.count_timeline_actions(
                                        tim, **filters_
                                    )
                                elif tim["override"][calculation][0:2] == "-=":
                                    # removing "-=" and setting override[edited_datapoint] to the right type
                                    tim["override"][calculation] = tim["override"][calculation][2:]
                                    if tim["override"][calculation].isdecimal():
                                        tim["override"][calculation] = int(
                                            tim["override"][calculation]
                                        )
                                    elif (
                                        "." in tim["override"][calculation]
                                        and tim["override"][calculation]
                                        .replace(".", "0", 1)
                                        .isdecimal()
                                    ):
                                        tim["override"][calculation] = float(
                                            tim["override"][calculation]
                                        )
                                    # "subtracting" to the original value
                                    tim["override"][calculation] *= -1
                                    tim["override"][calculation] += self.count_timeline_actions(
                                        tim, **filters_
                                    )
                            new_count = tim["override"][calculation]
                if not isinstance(new_count, self.type_check_dict[expected_type]):
                    raise TypeError(f"Expected {new_count} calculation to be a {expected_type}")
                unconsolidated_counts.append(new_count)
            calculated_tim[calculation] = obj_tims.ObjTIMCalcs.consolidate_nums(
                unconsolidated_counts
            )
        return calculated_tim

    def calculate_tim_times(self, unconsolidated_tim: dict) -> dict:
        """Given a list of unconsolidated TIMs, returns the calculated time data fields"""
        times = {}
        for calculation, action_types in self.schema["timeline_cycle_time"].items():
            # Variable type of a calculation is in the schema, but it's not a filter
            filters_ = copy.deepcopy(action_types)
            expected_type = filters_.pop("type")
            # action_types is a list of dictionaries, where each dictionary is
            # "action_type" to the name of either the start or end action
            new_cycle_time = self.total_time_between_actions(
                unconsolidated_tim,
                action_types["start_action"],
                action_types["end_action"],
                action_types["minimum_time"],
            )
            if not isinstance(new_cycle_time, self.type_check_dict[expected_type]):
                raise TypeError(f"Expected {new_cycle_time} calculation to be a {expected_type}")
            times[calculation] = new_cycle_time
        return times

    def calculate_expected_fields(self, tim, tim_totals):
        """Currently calculates the expected cycle times as well as the number of cycles. Both these calculations weight the different intake to score cycles."""
        # HOTFIX FOR 2025 REEFSCAPE
        # THIS YEAR, PRETTY MUCH ALL CYCLES ARE WORTH THE SAME SO EXPECTED CYCLES LOGIC IS MUCH SIMPLER
        score_actions = [
            "tele_net",
            "tele_processor",
            "tele_coral_L1",
            "tele_coral_L2",
            "tele_coral_L3",
            "tele_coral_L4",
            "tele_fail_net",
            "tele_fail_processor",
            "tele_fail_coral_L1",
            "tele_fail_coral_L2",
            "tele_fail_coral_L3",
            "tele_fail_coral_L4",
            "tele_drop_coral",
            "tele_drop_algae",
        ]
        cycles = {}
        num_cycles = 0
        for score_action in score_actions:
            if "drop" in score_action:
                num_cycles += 0.25 * tim_totals[score_action]
            else:
                num_cycles += tim_totals[score_action]
        cycles["expected_cycles"] = num_cycles

        times = [
            action["time"] for action in tim["timeline"] if action["action_type"] in score_actions
        ]
        if len(times) >= 2:
            cycles["expected_cycle_time"] = (
                abs(times[-1] - times[0]) / num_cycles if num_cycles != 0 else 150
            )
        else:
            cycles["expected_cycle_time"] = 135 / num_cycles if num_cycles != 0 else 150

        # intake_weights = self.schema["intake_weights"]
        # for field, value in self.schema["calculate_expected_fields"].items():
        #     if len(tim["timeline"]) == 0:
        #         cycles[field] = 0
        #         continue
        #     score_actions = value["score_actions"]
        #     # Make start time and end time equal to when teleop and endgame started
        #     try:
        #         start_time = self.filter_timeline_actions(tim, action_type="to_teleop")[0]["time"]
        #         end_time = self.filter_timeline_actions(tim, action_type="to_endgame")[-1]["time"]
        #     except:
        #         start_time = 135
        #         end_time = 0
        #     # Make total time equal to amount of time passed between teleop and endgame
        #     # tim_totals has the consolidated incap, we subtract incap from total_time to exclude its effect
        #     total_time = start_time - end_time - tim_totals["tele_incap"]
        #     # Tele actions are all the actions that occured in the time between the start time and end time
        #     tele_actions = self.filter_timeline_actions(tim, **{"time": [end_time, start_time]})
        #     num_cycles = 0
        #     # Filter for all intake actions in teleop then check the next action to see if it is a score
        #     # If the score is failed, the timeline appears as "fail", then the location
        #     length = len(tele_actions) - 1
        #     for count in range(length):
        #         # Last action will always be to endgame, so we can ignore the last and 2nd to last actions
        #         # Otherwise, there will be an index error
        #         if length - count > 1:
        #             if tele_actions[count + 1]["action_type"] in score_actions or (
        #                 tele_actions[count + 1]["action_type"] == "fail"
        #                 and tele_actions[count + 2]["action_type"] in score_actions
        #             ):
        #                 # If it is fail, the cycle must already be counted, also prevents crashing if it is the first action
        #                 if tele_actions[count]["action_type"] in list(intake_weights.keys()):
        #                     # Add intake weight type in schema
        #                     num_cycles += intake_weights[tele_actions[count]["action_type"]][
        #                         "normal"
        #                     ]
        #             # Add special case for incap b/c someone can intake, go incap, then score
        #             elif tele_actions[count + 1]["action_type"] == "start_incap":
        #                 if length - count > 3:
        #                     if tele_actions[count + 3]["action_type"] in score_actions or (
        #                         tele_actions[count + 3]["action_type"] == "fail"
        #                         and tele_actions[count + 4]["action_type"] in score_actions
        #                     ):
        #                         try:
        #                             num_cycles += intake_weights[
        #                                 tele_actions[count]["action_type"]
        #                             ]["normal"]
        #                         except:
        #                             pass
        #                 elif length - count == 3:
        #                     if tele_actions[count + 3]["action_type"] in score_actions:
        #                         num_cycles += intake_weights[tele_actions[count]["action_type"]][
        #                             "normal"
        #                         ]
        #             # If a robot has a piece out of a auto and scores it check to see if we should include it, if so add 1
        #             # to_teleop is the first timeline field, so check when count == 1
        #             if (
        #                 count == 1
        #                 and not value["ignore_shot_out_of_auto"]
        #                 and tele_actions[count]["action_type"] in score_actions
        #             ):
        #                 num_cycles += 1
        #     # Use the calc field to determine if we are calculating cycle time or number of cycles
        #     if value["calc"] == "time":
        #         # If there are no cycles, then set the cycle time to 135
        #         cycles[field] = (total_time / num_cycles) if num_cycles != 0 else 135.0
        #     elif value["calc"] == "num":
        #         cycles[field] = num_cycles

        return cycles

    def score_fail_type(self, unconsolidated_tims: List[Dict]):
        for num_1, tim in enumerate(unconsolidated_tims):
            timeline = tim["timeline"]
            # Collects the data for score_fails
            for num, action_dict in enumerate(timeline):
                if action_dict["action_type"] == "fail":
                    for score_type, new_value in self.schema["--fail_actions"].items():
                        if (
                            unconsolidated_tims[num_1]["timeline"][num + 1]["action_type"]
                            == score_type
                        ):
                            unconsolidated_tims[num_1]["timeline"][num + 1][
                                "action_type"
                            ] = new_value["name"]
        return unconsolidated_tims

    def calculate_unconsolidated_tims(self, unconsolidated_tims: List[Dict]):
        """Given a list of unconsolidated TIMS, returns the unconsolidated calculated TIMs"""
        if len(unconsolidated_tims) == 0:
            log.warning("calculate_tim: zero TIMs given")
            return {}
        unconsolidated_tims = self.merge_timeline_actions(unconsolidated_tims)
        unconsolidated_tims = self.score_fail_type(unconsolidated_tims)
        unconsolidated_totals = []
        # Calculates unconsolidated tim counts
        for tim in unconsolidated_tims:
            if not tim["timeline"]:
                log.critical(
                    f"No timeline for team {tim['team_number']} in match {tim['match_number']}"
                )
                continue
            tim_totals = {}
            tim_totals["scout_name"] = tim["scout_name"]
            tim_totals["match_number"] = tim["match_number"]
            tim_totals["team_number"] = tim["team_number"]
            tim_totals["alliance_color_is_red"] = tim["alliance_color_is_red"]
            tim_totals["scored_preload"] = (
                tim["has_preload"] and tim["timeline"][0]["action_type"][:10] == "auto_coral"
            )
            # Calculate unconsolidated tim counts
            for aggregate, filters in self.schema["aggregates"].items():
                total_count = 0
                aggregate_counts = filters["counts"]
                for calculation, filters in self.schema["timeline_counts"].items():
                    filters_ = copy.deepcopy(filters)
                    expected_type = filters_.pop("type")
                    new_count = self.count_timeline_actions(tim, **filters_)
                    if not isinstance(new_count, self.type_check_dict[expected_type]):
                        raise TypeError(f"Expected {new_count} calculation to be a {expected_type}")
                    tim_totals[calculation] = new_count
                    # Calculate unconsolidated aggregates
                    for count in aggregate_counts:
                        if calculation == count:
                            total_count += new_count
                    tim_totals[aggregate] = total_count
            # New section for obj_tim, unconsolidated_totals needs to iterate through these datapoints as well
            for aggregate, filters in self.schema["pre_consolidated_aggregates"].items():
                total_count = 0
                aggregate_counts = filters["counts"]
                for calculation, filters in self.schema["timeline_counts"].items():
                    filters_ = copy.deepcopy(filters)
                    expected_type = filters_.pop("type")
                    new_count = self.count_timeline_actions(tim, **filters_)
                    if not isinstance(new_count, self.type_check_dict[expected_type]):
                        raise TypeError(f"Expected {new_count} calculation to be a {expected_type}")
                    tim_totals[calculation] = new_count
                    # Calculate unconsolidated aggregates
                    for count in aggregate_counts:
                        if calculation == count:
                            total_count += new_count
                    tim_totals[aggregate] = total_count
            # Calculate unconsolidated categorical actions
            for category in self.schema["categorical_actions"]:
                tim_totals[category] = tim[category]

            tim_totals.update(self.calculate_tim_times(tim))
            tim_totals.update(self.calculate_expected_fields(tim, tim_totals))
            unconsolidated_totals.append(tim_totals)
        return unconsolidated_totals

    def update_calcs(self, tims: List[Dict[str, Union[str, int]]]) -> List[dict]:
        """Calculate data for each of the given TIMs. Those TIMs are represented as dictionaries:
        {'team_number': '1678', 'match_number': 69}"""
        unconsolidated_totals = []
        for tim in tims:
            unconsolidated_obj_tims = self.server.local_db.find("unconsolidated_obj_tim", tim)
            # check for overrides
            override = {}
            for t in unconsolidated_obj_tims:
                if "override" in t:
                    override.update(t.pop("override"))
            calculated_unconsolidated_tim = self.calculate_unconsolidated_tims(
                unconsolidated_obj_tims
            )
            # implement overrides
            if override:
                for edited_datapoint in override:
                    if edited_datapoint in calculated_unconsolidated_tim[0]:
                        # if override begins with += or -=, add or subtract respectively instead of just setting
                        if isinstance(override[edited_datapoint], str):
                            if override[edited_datapoint][0:2] == "+=":
                                # removing "+=" and setting override[edited_datapoint] to the right type
                                override[edited_datapoint] = override[edited_datapoint][2:]
                                if override[edited_datapoint].isdecimal():
                                    override[edited_datapoint] = int(override[edited_datapoint])
                                elif (
                                    "." in override[edited_datapoint]
                                    and override[edited_datapoint].replace(".", "0", 1).isdecimal()
                                ):
                                    override[edited_datapoint] = float(override[edited_datapoint])
                                # "adding" to the original value
                                override[edited_datapoint] += calculated_unconsolidated_tim[0][
                                    edited_datapoint
                                ]
                            elif override[edited_datapoint][0:2] == "-=":
                                # removing "-=" and setting override[edited_datapoint] to the right type
                                override[edited_datapoint] = override[edited_datapoint][2:]
                                if override[edited_datapoint].isdecimal():
                                    override[edited_datapoint] = int(override[edited_datapoint])
                                elif (
                                    "." in override[edited_datapoint]
                                    and override[edited_datapoint].replace(".", "0", 1).isdecimal()
                                ):
                                    override[edited_datapoint] = float(override[edited_datapoint])
                                # "subtracting" from the original value
                                override[edited_datapoint] *= -1
                                override[edited_datapoint] += calculated_unconsolidated_tim[0][
                                    edited_datapoint
                                ]
                        # overriding old value
                        calculated_unconsolidated_tim[0][edited_datapoint] = override[
                            edited_datapoint
                        ]
            unconsolidated_totals.extend(calculated_unconsolidated_tim)
        return unconsolidated_totals

    def run(self):
        """Executes the OBJ TIM calculations"""
        timer = Timer()

        if self.server.has_internet:
            tba_match_data: List[dict] = tba_communicator.tba_request(
                f"event/{utils.TBA_EVENT_KEY}/matches"
            )
        else:
            with open(f"data/{utils.TBA_EVENT_KEY}_match_schedule.json", "r") as f:
                match_schedule = dict(json.load(f))

        tims = []
        for document in self.server.local_db.find(self.watched_collections[0]):
            team_num = document["team_number"]
            if team_num not in self.teams_list:
                log.warning(f"team number {team_num} is not in teams list")
                continue
            tims.append(
                {
                    "team_number": team_num,
                    "match_number": document["match_number"],
                }
            )
        unique_tims = []
        for tim in tims:
            if tim not in unique_tims:
                unique_tims.append(tim)

        # Delete and re-insert
        self.server.local_db.delete_data("unconsolidated_totals")

        updates = self.update_calcs(unique_tims)
        filtered = []
        if len(updates) > 1:
            for document in updates:
                if document["team_number"] in list(
                    map(
                        lambda doc: doc["number"],
                        self.server.MATCH_SCHEDULE[str(document["match_number"])]["teams"],
                    )
                ):
                    filtered.append(document)
                else:
                    log.error(
                        f"{document['team_number']} not found in match {document['match_number']}"
                    )
        self.server.local_db.insert_documents("unconsolidated_totals", filtered)

        override.apply_override("unconsolidated_totals")

        timer.end_timer(__file__)
