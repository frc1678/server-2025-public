#!/usr/bin/env python3
"""Calculate objective team data from Team in Match (TIM) data."""

import utils
from typing import List, Dict
from calculations import base_calculations
import statistics
import logging
from timer import Timer
import csv
import os
import tba_communicator as tba
import override
import time

log = logging.getLogger(__name__)


class OBJTeamCalc(base_calculations.BaseCalculations):
    """Runs OBJ Team calculations"""

    # Get the last section of each entry (so foo.bar.baz becomes baz)
    SCHEMA = utils.unprefix_schema_dict(utils.read_schema("schema/calc_obj_team_schema.yml"))
    TIM_SCHEMA = utils.read_schema("schema/calc_obj_tim_schema.yml")

    def __init__(self, server):
        """Overrides watched collections, passes server object"""
        super().__init__(server)
        self.watched_collections = ["obj_tim", "subj_tim"]

        # For Matt's robustness ratings
        self.robustness_var_map = {
            "#": "team_number",
            "\U0001f6de": "matt_drivetrain",
            "🔌": "electrical_robustness",
            "⚙️": "mechanical_robustness",
            "🦾": "robot_complexity",
            "Architecture": "architecture",
            "Notes": "matt_notes",
        }

    def get_action_counts(self, tims: List[Dict]):
        """Gets a list of times each team completed a certain action by tim for averages
        and standard deviations.
        """
        tim_action_counts = {}
        # Gathers all necessary schema fields
        tim_fields = set()
        for schema in {
            **self.SCHEMA["averages"],
            **self.SCHEMA["standard_deviations"],
            **self.SCHEMA["extrema"],
        }.values():
            tim_fields.add(schema["tim_fields"][0].split(".")[1])
        for tim_field in tim_fields:
            # Gets the total number of actions across all tims
            tim_action_counts[tim_field] = [tim[tim_field] for tim in tims]
        return tim_action_counts

    def get_action_sum(self, tims: List[Dict]):
        """Gets a list of times each team completed a certain action by tim for medians"""
        tim_action_sum = {}
        # Gathers all necessary schema fields
        tim_fields = set()
        for schema in {**self.SCHEMA["medians"]}.values():
            tim_fields.add(schema["tim_fields"][0].split(".")[1])
        for tim_field in tim_fields:
            tim_action_sum[tim_field] = [tim[tim_field] for tim in tims]
        return tim_action_sum

    def get_action_categories(self, tims: List[Dict]):
        """Gets a list of times each team completed a certain categorical action for counts and modes."""
        tim_action_categories = {}
        # Gathers all necessary schema fields
        tim_fields = set()
        for schema in {**self.SCHEMA["modes"]}.values():
            tim_fields.add(schema["tim_fields"][0].split(".")[1])
        for tim_field in tim_fields:
            # Gets the total number of actions across all tims
            tim_action_categories[tim_field] = [tim[tim_field] for tim in tims]
        return tim_action_categories

    def calculate_averages(self, tim_action_counts, lfm_tim_action_counts):
        """Creates a dictionary of calculated averages, called team_info,
        where the keys are the names of the calculations, and the values are the results
        """
        team_info = {}
        for calculation, schema in self.SCHEMA["averages"].items():
            # Average the values for the tim_fields
            average = 0
            for tim_field in schema["tim_fields"]:
                tim_field = tim_field.split(".")[1]
                if "lfm" in calculation:
                    average += (
                        0
                        if self.avg(lfm_tim_action_counts[tim_field]) == None
                        else self.avg(lfm_tim_action_counts[tim_field])
                    )
                else:
                    average += (
                        0
                        if self.avg(tim_action_counts[tim_field]) == None
                        else self.avg(tim_action_counts[tim_field])
                    )
            team_info[calculation] = average

            # 2025 SAC HOTFIX
            # Datapoint requested by Austin
            if calculation == "tele_avg_total_pieces":
                team_info["tele_avg_total_nonzero_pieces"] = self.avg(
                    list(filter(lambda val: val != 0, tim_action_counts[tim_field]))
                )
                team_info["lfm_tele_avg_total_nonzero_pieces"] = self.avg(
                    list(filter(lambda val: val != 0, lfm_tim_action_counts[tim_field]))
                )
        return team_info

    def calculate_standard_deviations(self, tim_action_counts, lfm_tim_action_counts):
        """Creates a dictionary of calculated standard deviations, called team_info,
        where the keys are the names of the calculation, and the values are the results
        """
        team_info = {}
        for calculation, schema in self.SCHEMA["standard_deviations"].items():
            # Take the standard deviation for the tim_field
            tim_field = schema["tim_fields"][0].split(".")[1]
            if "lfm" in calculation:
                standard_deviation = (
                    statistics.pstdev(lfm_tim_action_counts[tim_field])
                    if lfm_tim_action_counts[tim_field]
                    else 0
                )
            else:
                standard_deviation = (
                    statistics.pstdev(tim_action_counts[tim_field])
                    if tim_action_counts[tim_field]
                    else 0
                )
            team_info[calculation] = standard_deviation
        return team_info

    def filter_tims_for_counts(self, tims: List[Dict], schema):
        """Filters tims based on schema for count calculations"""
        tims_that_meet_filter = 0
        for field in schema["tim_fields"]:
            if type(field) == dict:
                for key, value in field.items():
                    key = key.split(".")[1]
                    # Checks that the TIMs in their given field meet the filter
                    tims_that_meet_filter += len(list(filter(lambda tim: tim[key] == value, tims)))
            else:
                for key, value in schema["tim_fields"].items():
                    if key != "not":
                        # Checks that the TIMs in their given field meet the filter
                        tims_that_meet_filter += len(
                            list(filter(lambda tim: tim[key] == value, tims))
                        )
                    else:
                        # not_field expects the output to be anything but the given filter
                        # not_value is the filter that not_field shouldn't have
                        # checks if value is a list
                        if isinstance(value, list):
                            tims_that_meet_filter += len(
                                list(
                                    # filter gets every item that meets the conditions of the lambda function in tims
                                    filter(
                                        lambda tim: False
                                        not in [
                                            tim.get(not_field.split(".")[1], not_value) != not_value
                                            for val in value
                                            for not_field, not_value in val.items()
                                        ],
                                        tims,
                                    )
                                )
                            )
                        else:
                            tims_that_meet_filter += len(
                                list(
                                    filter(
                                        lambda tim: False
                                        not in [
                                            tim.get(not_field, not_value) != not_value
                                            for not_field, not_value in value.items()
                                        ],
                                        tims,
                                    )
                                )
                            )

        return tims_that_meet_filter

    def calculate_counts(self, tims: List[Dict], lfm_tims: List[Dict]):
        """Creates a dictionary of calculated counts, called team_info,
        where the keys are the names of the calculations, and the values are the results
        """
        team_info = {}
        for calculation, schema in self.SCHEMA["counts"].items():
            if "lfm" in calculation:
                tims_that_meet_filter = self.filter_tims_for_counts(lfm_tims, schema)
            else:
                tims_that_meet_filter = self.filter_tims_for_counts(tims, schema)
            team_info[calculation] = tims_that_meet_filter
        return team_info

    """def calculate_multi_counts(self, tims: List[Dict], lfm_tims: List[Dict]):
        '''Calculates counts of datapoints that can occur more than once in a match, such as trap_successes'''
        team_info = {}
        for calculation, schema in self.SCHEMA["multi_counts"].items():
            tim_fields = [tim_field.split(".")[1] for tim_field in schema["tim_fields"]]
            team_info[calculation] = sum(
                [
                    tim[tim_field]
                    for tim_field in tim_fields
                    for tim in (lfm_tims if "lfm" in calculation else tims)
                ]
            )
        return team_info
        Not used in Reefscape"""

    """def calculate_special_counts(self, obj_tims, subj_tims, lfm_obj_tims, lfm_subj_tims):
        '''Calculates counts of datapoints collected by Objective and Subjective Scouts.'''
        team_info = {}
        for calculation, schema in self.SCHEMA["special_counts"].items():
            total = 0
            obj_tims_that_meet_filter = []
            subj_tims_that_meet_filter = []
            if "lfm" in calculation:
                for field in schema["tim_fields"]:
                    for key, value in field.items():
                        # Separates the datapoint into the obj/subj_tim part and the actual datapoint
                        key, name = key.split(".")[1], key.split(".")[0]
                        # Checks that the TIMs in their given field meet the filter
                        if name == "obj_tim":
                            # joins the two lists together
                            # filter gets every item that meets the conditions of the lambda function in tims
                            obj_tims_that_meet_filter = obj_tims_that_meet_filter + list(
                                filter(lambda tim: tim.get(key, value) == value, lfm_obj_tims)
                            )
                        else:
                            subj_tims_that_meet_filter = subj_tims_that_meet_filter + list(
                                filter(lambda tim: tim.get(key, value) == value, lfm_subj_tims)
                            )
            else:
                for field in schema["tim_fields"]:
                    for key, value in field.items():
                        # Separates the datapoint into the obj/subj_tim part and the actual datapoint
                        key, name = key.split(".")[1], key.split(".")[0]
                        # Checks that the TIMs in their given field meet the filter
                        if name == "obj_tim":
                            # joins the two lists together
                            # filter gets every item that meets the conditions of the lambda function in tims
                            obj_tims_that_meet_filter = obj_tims_that_meet_filter + list(
                                filter(lambda tim: tim.get(key, value) == value, obj_tims)
                            )
                        else:
                            subj_tims_that_meet_filter = subj_tims_that_meet_filter + list(
                                filter(lambda tim: tim.get(key, value) == value, subj_tims)
                            )
            for tim in obj_tims_that_meet_filter:
                for s_tim in subj_tims_that_meet_filter:
                    if (
                        tim["match_number"] == s_tim["match_number"]
                        and tim["team_number"] == s_tim["team_number"]
                    ):
                        total += 1
                        break
            team_info[calculation] = total
        return team_info
        Not used in Reefscape"""

    """def calculate_super_counts(self, tims, lfm_tims):
        '''Calculates counts of datapoints collected by Super Scouts.'''
        team_info = {}
        for calculation, schema in self.SCHEMA["super_counts"].items():
            total = 0
            tim_field = schema["tim_fields"][0].split(".")[1]
            if "lfm" in calculation:
                for tim in lfm_tims:
                    if tim[tim_field]:
                        total += 1
            else:
                for tim in tims:
                    if tim[tim_field]:
                        total += 1
            team_info[calculation] = total
        return team_info
        Not used in Reefscape"""

    def calculate_ss_counts(self, tims, lfm_tims):
        """Calculates counts of datapoints collected by Stand Strategists."""
        team_info = {}
        for calculation, schema in self.SCHEMA["ss_counts"].items():
            total = 0
            tim_field = schema["tim_fields"][0].split(".")[1]
            if "lfm" in calculation:
                for tim in lfm_tims:
                    if tim_field in tim.keys():
                        if tim[tim_field] == True:
                            total += 1
            else:
                for tim in tims:
                    if tim_field in tim.keys():
                        if tim[tim_field] == True:
                            total += 1
            team_info[calculation] = total
        return team_info

    def calculate_extrema(
        self,
        tim_action_counts,
        lfm_tim_action_counts,
    ):
        """Creates a dictionary of extreme values, called team_info,
        where the keys are the names of the calculations, and the values are the results
        """
        team_info = {}
        for calculation, schema in self.SCHEMA["extrema"].items():
            tim_field = schema["tim_fields"][0].split(".")[1]
            if schema["extrema_type"] == "max":
                if "lfm" in calculation:
                    team_info[calculation] = (
                        max(lfm_tim_action_counts[tim_field])
                        if lfm_tim_action_counts[tim_field]
                        else 0
                    )
                else:
                    team_info[calculation] = (
                        max(tim_action_counts[tim_field]) if tim_action_counts[tim_field] else 0
                    )
            if schema["extrema_type"] == "min":
                if "lfm" in calculation:
                    team_info[calculation] = (
                        min(lfm_tim_action_counts[tim_field])
                        if lfm_tim_action_counts[tim_field]
                        else 0
                    )
                else:
                    team_info[calculation] = (
                        min(tim_action_counts[tim_field]) if tim_action_counts[tim_field] else 0
                    )
        return team_info

    def calculate_medians(self, tim_action_sum, lfm_tim_action_sum):
        """Creates a dictionary of median actions, called team_info,
        where the keys are the names of the calculations, and the values are the results
        """
        team_info = {}
        for calculation, schema in self.SCHEMA["medians"].items():
            median = 0
            for tim_field in schema["tim_fields"]:
                tim_field = tim_field.split(".")[1]
                if "lfm" in calculation:
                    values_to_count = [
                        value
                        for value in lfm_tim_action_sum[tim_field]
                        if value != schema["ignore"]
                    ]
                    if not values_to_count:
                        continue
                    median += statistics.median(values_to_count)
                else:
                    values_to_count = [
                        value for value in tim_action_sum[tim_field] if value != schema["ignore"]
                    ]
                    if not values_to_count:
                        continue
                    median += statistics.median(values_to_count)
            team_info[calculation] = median
        return team_info

    def calculate_modes(self, tim_action_categories, lfm_tim_action_categories):
        """Creates a dictionary of mode actions, called team_info,
        where the keys are the names of the calculations, and the values are the results
        """

        team_info = {}
        for calculation, schema in self.SCHEMA["modes"].items():
            values_to_count = []
            for tim_field in schema["tim_fields"]:
                tim_field = tim_field.split(".")[1]
                if "lfm" in calculation:
                    values_to_count = values_to_count + [
                        value
                        for value in lfm_tim_action_categories[tim_field]
                        if value != schema["ignore"]
                    ]
                else:
                    values_to_count = values_to_count + [
                        value
                        for value in tim_action_categories[tim_field]
                        if value != schema["ignore"]
                    ]
            team_info[calculation] = statistics.multimode(values_to_count)
        return team_info

    def calculate_success_rates(self, team_counts: Dict):
        """Creates a dictionary of action success rates, called team_info,
        where the keys are the names of the calculations, and the values are the results
        """
        team_info = {}
        for calculation, schema in self.SCHEMA["success_rates"].items():
            num_attempts = 0
            num_successes = 0
            for attempt_datapoint in schema["team_attempts"]:
                if isinstance(attempt_datapoint, int):
                    num_attempts += attempt_datapoint
                elif attempt_datapoint[0] == "-":
                    num_attempts -= team_counts[attempt_datapoint[1:]]
                else:
                    num_attempts += team_counts[attempt_datapoint]
            for success_datapoint in schema["team_successes"]:
                num_successes += team_counts[success_datapoint]
            if num_attempts != 0:
                team_info[calculation] = num_successes / num_attempts
                if num_successes / num_attempts > 1:
                    team_info[calculation] = 1
            else:
                team_info[calculation] = None
        return team_info

    # Not used in Crescendo
    """def calculate_average_points(self, team_data):
        team_info = {}
        for calculation, schema in self.SCHEMA["average_points"].items():
            total_successes = 0
            total_points = 0
            for field, value in schema.items():
                if field == "type":
                    continue
                total_successes += team_data[field]
                total_points += team_data[field] * value
            if total_successes > 0:
                team_info[calculation] = total_points / total_successes
            else:
                team_info[calculation] = 0
        return team_info"""

    def calculate_sums(self, team_data, tims: List[Dict], lfm_tims: List[Dict]):
        """Creates a dictionary of sum of weighted data, called team_info
        where the keys are the names of the calculations, and the values are the results
        """
        team_info = {}
        for calculation, schema in self.SCHEMA["sums"].items():
            # incap_time has no point values
            if calculation == "total_incap_time":
                team_info[calculation] = sum(tim["tele_incap"] for tim in tims)
            elif calculation == "lfm_total_incap_time":
                # Use lfm_tims instead of tims, also this is the only lfm sum
                team_info[calculation] = sum([tim["tele_incap"] for tim in lfm_tims])

            else:
                total_points = 0
                for field, value in schema.items():
                    if field == "type":
                        continue
                    if isinstance(value, list):
                        weight = 1
                        for v in value:
                            weight *= v if not isinstance(v, str) else team_data[v]
                    else:
                        weight = value if not isinstance(value, str) else team_data[value]
                    total_points += (
                        team_data[field] if field in team_data else team_info[field]
                    ) * weight
                team_info[calculation] = total_points
        return team_info

    def pull_robustness_ratings(self):
        """This function is a temporary way to pull Matt's robustness ratings from a CSV file into the `obj_team` collection in the database.

        Pulls from a file called `data/{server_key}_robustness_ratings.csv` if it exists (export from Google sheet)
        """
        type_map = {
            "team_number": str,
            "matt_drivetrain": str,
            "electrical_robustness": float,
            "mechanical_robustness": float,
            "robot_complexity": float,
            "architecture": str,
            "matt_notes": str,
        }
        data = []

        if os.path.exists(f"data/{utils.server_key()}_robustness_ratings.csv"):
            with open(f"data/{utils.server_key()}_robustness_ratings.csv", "r") as file:
                csvreader = csv.reader(file)
                header = next(csvreader)
                indexes = {var: header.index(var) for var in header}

                for row in csvreader:
                    row_doc = dict()
                    for key, i in indexes.items():
                        if key not in self.robustness_var_map.keys():
                            continue
                        type_ = type_map[self.robustness_var_map[key]]
                        if row[i]:
                            row_doc[self.robustness_var_map[key]] = type_(row[i])
                        else:
                            row_doc[self.robustness_var_map[key]] = None
                    data.append(row_doc)
        else:
            for team in self.server.TEAM_LIST:
                row_doc = {"team_number": team}

                for var in list(self.robustness_var_map.values())[1:]:
                    type_ = type_map[var]
                    row_doc[var] = None

                data.append(row_doc)

        return data

    # def calculate_avg_defense_points_subtracted(self, team_number, obj_team_updates):
    #     obj_tims = self.server.local_db.find("obj_tim")
    #     ss_tims = self.server.local_db.find("ss_tim")
    #     obj_teams = self.server.local_db.find("obj_team")
    #     for team in obj_team_updates.keys():
    #         updated_team = False
    #         for i in range(len(obj_teams)):
    #             if obj_teams[i]["team_number"] == team:
    #                 obj_teams[i]["team_number"].update(obj_team_updates[team])
    #                 updated_team = True
    #                 break
    #         if not updated_team:
    #             obj_teams.append(obj_team_updates[team])

    #     """Calculates the avg amount of points a team is expected to prevent the opposing alliance from scoring when they play defense"""
    #     matches_played_defense = []
    #     total_defense_points_subtracted = 0
    #     for ss_tim in ss_tims:
    #         if (
    #             ss_tim["team_number"] == team_number
    #             and ss_tim["played_defense"]
    #             and ss_tim["match_number"] not in matches_played_defense
    #         ):
    #             matches_played_defense.append(ss_tim["match_number"])
    #             match_obj_tims = [
    #                 tim for tim in obj_tims if tim["match_number"] == ss_tim["match_number"]
    #             ]
    #             team_obj_tim = [tim for tim in match_obj_tims if tim["team_number"] == team_number][
    #                 0
    #             ]
    #             # shortened form of 'alliance_color_is_red'
    #             ac_is_red = team_obj_tim["alliance_color_is_red"]
    #             opposing_alliance_tims = [
    #                 tim for tim in match_obj_tims if tim["alliance_color_is_red"] != ac_is_red
    #             ]
    #             # find the average total points in matches where the team was not played defense against
    #             expected_opposing_alliance_total_points = sum(
    #                 [
    #                     statistics.mean(
    #                         [
    #                             tim1["total_points"]
    #                             for tim1 in obj_tims
    #                             if tim1["team_number"] == tim["team_number"]
    #                             and tim1["match_number"]
    #                             not in [
    #                                 ss["match_number"]
    #                                 for ss in ss_tims
    #                                 if ss["played_defense"] == True
    #                                 and ss["team_number"]
    #                                 not in [
    #                                     tim2["team_number"]
    #                                     for tim2 in obj_tims
    #                                     if tim2["match_number"] == ss["match_number"]
    #                                     and tim2["alliance_color_is_red"]
    #                                     == tim1["alliance_color_is_red"]
    #                                 ]
    #                             ]
    #                         ]
    #                         if len(
    #                             [
    #                                 tim1["total_points"]
    #                                 for tim1 in obj_tims
    #                                 if tim1["team_number"] == tim["team_number"]
    #                                 and tim1["match_number"]
    #                                 not in [
    #                                     ss["match_number"]
    #                                     for ss in ss_tims
    #                                     if ss["played_defense"] == True
    #                                     and ss["team_number"]
    #                                     not in [
    #                                         tim2["team_number"]
    #                                         for tim2 in obj_tims
    #                                         if tim2["match_number"] == ss["match_number"]
    #                                         and tim2["alliance_color_is_red"]
    #                                         == tim1["alliance_color_is_red"]
    #                                     ]
    #                                 ]
    #                             ]
    #                         )
    #                         != 0
    #                         else [
    #                             team["avg_total_points"]
    #                             for team in obj_teams
    #                             if team["team_number"] == tim["team_number"]
    #                         ]
    #                     )
    #                     for tim in opposing_alliance_tims
    #                 ]
    #             )  # list uncomprehen(sion)dable black magic
    #             actual_opposing_alliance_total_points = sum(
    #                 [tim["total_points"] for tim in opposing_alliance_tims]
    #             )
    #             total_defense_points_subtracted += (
    #                 expected_opposing_alliance_total_points - actual_opposing_alliance_total_points
    #             )
    #     if len(matches_played_defense) == 0:
    #         return 0.0
    #     return total_defense_points_subtracted / len(matches_played_defense)

    def update_team_calcs(self, teams: list) -> list:
        """Calculate data for given team using objective calculated TIMs"""
        obj_team_updates = {}

        robustness_ratings = self.pull_robustness_ratings()

        for team in teams:
            team_data = {}
            # Load team data from database
            obj_tims = self.server.local_db.find("obj_tim", {"team_number": team})
            ss_tims = self.server.local_db.find("ss_tim", {"team_number": team})
            auto_pims = self.server.local_db.find("auto_pim", {"team_number": team})
            # Finds if they have a compatible auto
            team_data["has_compatible_auto"] = (
                sum(list(map(lambda pim: int(pim["is_compatible"]), auto_pims))) >= 1
            )
            # Last 4 tims to calculate last 4 matches
            obj_lfm_tims = sorted(obj_tims, key=lambda tim: tim["match_number"])[-4:]
            ss_lfm_tims = sorted(ss_tims, key=lambda tim: tim["match_number"])[-4:]
            tim_action_counts = self.get_action_counts(obj_tims)
            lfm_tim_action_counts = self.get_action_counts(obj_lfm_tims)
            tim_action_categories = self.get_action_categories(obj_tims)
            lfm_tim_action_categories = self.get_action_categories(obj_lfm_tims)
            tim_action_sum = self.get_action_sum(obj_tims)
            lfm_tim_action_sum = self.get_action_sum(obj_lfm_tims)

            team_data.update(self.calculate_averages(tim_action_counts, lfm_tim_action_counts))
            team_data["team_number"] = team
            team_data.update(self.calculate_counts(obj_tims, obj_lfm_tims))
            # team_data.update(self.calculate_multi_counts(obj_tims, obj_lfm_tims))
            # team_data.update(self.calculate_super_counts(subj_tims, subj_lfm_tims))
            team_data.update(self.calculate_ss_counts(ss_tims, ss_lfm_tims))
            team_data.update(
                self.calculate_standard_deviations(tim_action_counts, lfm_tim_action_counts)
            )
            team_data.update(
                self.calculate_extrema(
                    tim_action_counts,
                    lfm_tim_action_counts,
                )
            )
            # team_data.update(
            #     self.calculate_special_counts(obj_tims, subj_tims, obj_lfm_tims, subj_lfm_tims)
            # )
            team_data.update(self.calculate_modes(tim_action_categories, lfm_tim_action_categories))
            team_data.update(self.calculate_medians(tim_action_sum, lfm_tim_action_sum))
            team_data.update(self.calculate_success_rates(team_data))
            # team_data.update(self.calculate_average_points(team_data))
            team_data.update(self.calculate_sums(team_data, obj_tims, obj_lfm_tims))

            for team_rating in robustness_ratings:
                try:
                    if team_rating["team_number"] == team:
                        team_rating.pop("team_number")
                        team_data.update(team_rating)
                        break
                except:
                    continue
            else:
                team_data.update({var: None for var in list(self.robustness_var_map.values())[1:]})

            # If obj team is too slow, it might be because TBA requests are slower than usual. This happens when the internet is bad (e.g. at Champs). To fix this, remove the TBA request here and just use the number of obj tim documents. Replace the long f-string below with `f"{len(obj_tims)}/{len(obj_tims)}"`
            team_data[
                "matches_with_data"
            ] = f"{len(obj_tims)}/{len([match for match in (tba.tba_request(f'event/{self.server.TBA_EVENT_KEY}/matches') or []) if team in (tba.get_teams_in_match(match)['red'] + tba.get_teams_in_match(match)['blue']) and match.get('score_breakdown') and (self.server.TBA_EVENT_KEY + '_qm') in match['key']])}"

            obj_team_updates[team] = team_data
        return list(obj_team_updates.values())

    def run(self):
        """Executes the OBJ Team calculations"""
        timer = Timer()

        teams = self.get_teams_list()

        self.server.local_db.delete_data("obj_team")
        self.server.local_db.insert_documents("obj_team", self.update_team_calcs(teams))

        override.apply_override("obj_team")

        timer.end_timer(__file__)
