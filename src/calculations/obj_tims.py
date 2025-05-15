#!/usr/bin/env python3

"""Defines class methods to consolidate and calculate Team In Match (TIM) data."""

import copy
import statistics
import utils
from calculations.base_calculations import BaseCalculations
from typing import List, Union, Dict
import logging
import tba_communicator
import json
from timer import Timer
import override

log = logging.getLogger(__name__)


class ObjTIMCalcs(BaseCalculations):
    schema = utils.read_schema("schema/calc_obj_tim_schema.yml")
    type_check_dict = {"float": float, "int": int, "str": str, "bool": bool}

    def __init__(self, server):
        super().__init__(server)
        self.watched_collections = ["unconsolidated_totals"]

    def consolidate_nums(self, nums: List[Union[int, float]], decimal=False) -> int:
        """Given numbers reported by multiple scouts, estimates actual number
        nums is a list of numbers, representing action counts or times, reported by each scout
        Currently tries to consolidate using only the reports from scouts on one robot,
        but future improvements might change the algorithm to account for other alliance members,
        since TBA can give us the total action counts for the alliance
        """
        if not nums:
            return 0
        if len(mode := self.modes(nums)) == 1:
            return mode[0]
        mean = self.avg(nums)
        if len(nums) == 0 or mean in nums:
            # Avoid getting a divide by zero error when calculating standard deviation
            if decimal:
                return round(mean, 2)
            else:
                return round(mean)
        # If two or more scouts agree, automatically go with what they say
        if len(nums) > len(set(nums)):
            # Still need to consolidate, in case there are multiple modes
            return self.consolidate_nums(self.modes(nums), decimal)
        # Population standard deviation:
        std_dev = statistics.pstdev(nums)
        # Calculate weighted average, where the weight for each num is its reciprocal square z-score
        # That way, we account less for data farther from the mean
        z_scores = [(num - mean) / std_dev for num in nums]
        weights = [1 / z**2 for z in z_scores]
        float_nums = self.avg(nums, weights)
        if decimal:
            return round(float_nums, 2)
        return round(float_nums)

    def consolidate_bools(self, bools: list) -> bool:
        """Given a list of booleans reported by multiple scouts, returns the actual value"""
        bools = self.modes(bools)
        if len(bools) == 1:
            # Go with the majority
            return bools[0]
        # Scouts are evenly split, so just go with False
        return False

    def calculate_aggregates(self, calculated_tim: List[Dict]):
        """Given a list of consolidated tims by calculate_tim_counts, return consolidated aggregates"""
        final_aggregates = {}
        # Get each aggregate and its associated counts
        for aggregate, filters in self.schema["aggregates"].items():
            total_count = 0
            aggregate_counts = filters["counts"]
            # Add up all the counts for each aggregate and add them to the final dictionary
            for count in aggregate_counts:
                total_count += (
                    calculated_tim[count]
                    if count in calculated_tim
                    else final_aggregates[count]
                    if count in final_aggregates
                    else 0
                )
                final_aggregates[aggregate] = total_count
        return final_aggregates

    def calculate_point_values(self, calculated_tim: List[Dict]):
        """Given a list of consolidated tims by calculate_tim_counts, return consolidated point values"""
        final_points = {}
        # Get each point data point
        for point_datapoint_section, filters in self.schema["point_calculations"].items():
            total_points = 0
            point_aggregates = filters["counts"]
            point_counts = list(point_aggregates.keys())
            # Add up all the counts for each aggregate, multiplies them by their value, then adds them to the final dictionary
            for point in point_counts:
                count = calculated_tim[point] if point in calculated_tim else 0
                if isinstance(count, bool):
                    total_points += point_aggregates[point] if count else 0
                elif isinstance(count, str):
                    total_points += point_aggregates[point] if count not in ["N", "F"] else 0
                else:
                    total_points += count * point_aggregates[point]
            final_points[point_datapoint_section] = total_points
        return final_points

    def consolidate_totals(self, unconsolidated_totals) -> dict:
        """Given a list of unconsolidated totals dictionaries, consolidate them into one tim"""
        consolidated_tim = {}
        for category in self.schema["categorical_actions"]:
            scout_categorical_actions = [scout[category] for scout in unconsolidated_totals]
            # Enums for associated category actions and shortened representation
            actions = self.schema["categorical_actions"][category]["list"]
            # Turn the shortened categorical actions from the scout into full strings
            categorical_actions = []
            for action in scout_categorical_actions:
                for value in actions:
                    if value == action:
                        categorical_actions.append(value)
                        break
            # If at least 2 scouts agree, take their answer
            if len(self.modes(categorical_actions)) == 1:
                consolidated_tim[category] = self.modes(categorical_actions)[0]
                continue

            # Add up the indexes of the scout responses
            category_avg = self.avg([list(actions).index(value) for value in categorical_actions])
            # Round the average and append the correct action to the final dict
            if category_avg == None:
                category_avg = 0
            consolidated_tim[category] = list(actions)[round(category_avg)]
        # Consolidate numbers & bools
        for schema_category in self.schema.keys():
            if schema_category not in [
                "intake_weights",
                "categorical_actions",
                "fail_actions",
                "point_calculations",
                "schema_file",
                "merge_actions",
            ]:
                for datapoint in self.schema[schema_category]:
                    if schema_category == "data" and datapoint != "scored_preload":
                        continue
                    if self.schema[schema_category][datapoint]["type"] == "int":
                        consolidated_tim[datapoint] = self.consolidate_nums(
                            [scout[datapoint] for scout in unconsolidated_totals]
                        )
                    elif self.schema[schema_category][datapoint]["type"] == "float":
                        consolidated_tim[datapoint] = self.consolidate_nums(
                            [scout[datapoint] for scout in unconsolidated_totals], True
                        )
                    elif self.schema[schema_category][datapoint]["type"] == "bool":
                        consolidated_tim[datapoint] = self.consolidate_bools(
                            [scout[datapoint] for scout in unconsolidated_totals]
                        )
        return consolidated_tim

    def calculate_tim(self, unconsolidated_totals) -> dict:
        """Given a list of unconsolidated TIMs, returns a calculated TIM"""
        if len(unconsolidated_totals) == 0:
            log.warning("zero unconsolidated_totals docs given")
            return {}
        calculated_tim = {}

        team_number = unconsolidated_totals[0]["team_number"]
        match_number = unconsolidated_totals[0]["match_number"]

        calculated_tim.update(self.consolidate_totals(unconsolidated_totals))
        calculated_tim.update(self.calculate_aggregates(calculated_tim))

        # TODO Add flag when all scouts disagree with TBA

        tim = self.server.local_db.find(
            "tba_tim", {"team_number": team_number, "match_number": match_number}
        )

        tba_to_db = {"DeepCage": "D", "None": "N", "ShallowCage": "S"}
        if len(tim) != 0:
            if tim[0]["climb_level"] == "Parked":
                calculated_tim["parked"] = True
                calculated_tim["cage_level"] = "N"
            else:
                calculated_tim["parked"] = False
                calculated_tim["cage_level"] = tba_to_db[tim[0]["climb_level"]]
        if calculated_tim["cage_level"] == "D" or calculated_tim["cage_level"] == "S":
            calculated_tim["cage_fail"] = False
        else:
            if any(total["cage_fail"] for total in unconsolidated_totals):
                calculated_tim["cage_fail"] = True
            else:
                calculated_tim["cage_fail"] = False

        calculated_tim["deep"] = (
            calculated_tim["cage_level"] == "D" and not calculated_tim["cage_fail"]
        )
        calculated_tim["shallow"] = (
            calculated_tim["cage_level"] == "S" and not calculated_tim["cage_fail"]
        )
        calculated_tim.update(self.calculate_point_values(calculated_tim))

        # #olidated TIMs to get the team and match number,
        # since that should be the same for each unconsolidated TIM
        calculated_tim["match_number"] = unconsolidated_totals[0]["match_number"]
        calculated_tim["team_number"] = unconsolidated_totals[0]["team_number"]
        calculated_tim["alliance_color_is_red"] = unconsolidated_totals[0]["alliance_color_is_red"]
        # confidence_rating is the number of scouts that scouted one robot
        calculated_tim["confidence_rating"] = len(unconsolidated_totals)

        return calculated_tim

    def update_calcs(self, tims: List[Dict[str, Union[str, int]]]) -> List[dict]:
        """Calculate data for each of the given TIMs. Those TIMs are represented as dictionaries:
        {'team_number': '1678', 'match_number': 69}"""
        calculated_tims = []

        for tim in tims:
            unconsolidated_totals = self.server.local_db.find("unconsolidated_totals", tim)
            calculated_tim = self.calculate_tim(unconsolidated_totals)
            calculated_tim["flagged"] = False
            calculated_tims.append(calculated_tim)
        return calculated_tims

    def run(self):
        """Executes the OBJ TIM calculations"""
        timer = Timer()

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

        self.server.local_db.delete_data("obj_tim")

        updates = self.update_calcs(unique_tims)
        filtered = []
        if updates == None:
            pass
        else:
            for update in updates:
                if update:
                    if update["team_number"] in self.server.TEAM_LIST:
                        if tba_tim := self.server.local_db.find(
                            "tba_tim",
                            {"team_number": team_num, "match_number": document["match_number"]},
                        ):
                            update["leave"] = tba_tim[0]["leave"]
                        filtered.append(update)
                    else:
                        log.warning(
                            f"{update['team_number']} not found in match {update['match_number']}"
                        )

        self.server.local_db.insert_documents("obj_tim", filtered)

        override.apply_override("obj_tim")

        timer.end_timer(__file__)
