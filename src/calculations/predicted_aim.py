#!/usr/bin/env python3
"""Makes predictive calculations for alliances in matches in a competition."""

import utils
import numpy as np
from statistics import NormalDist as Norm
from calculations.base_calculations import BaseCalculations
import tba_communicator
import logging
import pandas as pd
import statsmodels.api as sm
from timer import Timer
import doozernet_communicator
from typing import List
import copy
import override

log = logging.getLogger(__name__)


class PredictedAimCalc(BaseCalculations):
    schema = utils.read_schema("schema/calc_predicted_aim_schema.yml")

    POINT_VALUES = {
        "auto_net": 4,
        "auto_processor": 2.68,  # assume HP scores in the net 83% of the time
        "auto_coral_L1": 3,
        "auto_coral_L2": 4,
        "auto_coral_L3": 6,
        "auto_coral_L4": 7,
        "auto_leave": 3,
        "tele_net": 4,
        "tele_processor": 2.68,  # assume HP scores in the net 83% of the time
        "tele_coral_L1": 2,
        "tele_coral_L2": 3,
        "tele_coral_L3": 4,
        "tele_coral_L4": 5,
        "endgame_park": 2,
        "endgame_shallow": 6,
        "endgame_deep": 12,
    }
    PREDICTED_VALUES = {
        "auto_net": 0,
        "auto_processor": 0,
        "auto_coral_L1": 0,
        "auto_coral_L2": 0,
        "auto_coral_L3": 0,
        "auto_coral_L4": 0,
        "auto_leave": 0,
        "tele_net": 0,
        "tele_processor": 0,
        "tele_coral_L1": 0,
        "tele_coral_L2": 0,
        "tele_coral_L3": 0,
        "tele_coral_L4": 0,
        "endgame_park": 0,
        "endgame_shallow": 0,
        "endgame_deep": 0,
    }

    def __init__(self, server):
        super().__init__(server)
        self.watched_collections = ["obj_team", "tba_team"]
        self.played_teams = []

    def calc_predicted_values(self, obj_team_data, tba_team_data, team_numbers):
        """Calculates the predicted_values dataclass for an alliance.

        predicted_values is a dict which stores the predicted number of pieces and success rates.

        obj_team is a list of dictionaries of objective team data.

        tba_team is a list of dictionaries of tba team data.

        team_numbers is a list of team numbers (strings) on the alliance.

        other_team_numbers is a list of team numbers on the opposing alliance
        """
        predicted_values = copy.deepcopy(self.PREDICTED_VALUES)

        # Gets obj_team data for teams in team_numbers
        obj_team = [
            team_data for team_data in obj_team_data if team_data["team_number"] in team_numbers
        ]

        if len(obj_team) > 3:
            log.critical(f"More than 3 obj_team documents for teams {team_numbers}")

        # Updates predicted_values using obj_team and tba_team data
        for team in obj_team:
            tba_team = [
                team_data
                for team_data in tba_team_data
                if team_data["team_number"] == team["team_number"]
            ]
            if tba_team:
                tba_team = tba_team[0]
            else:
                if team["team_number"] in self.played_teams:
                    log.warning(f"tba_team data not found for team {team['team_number']}")
                tba_team = {"leave_success_rate": 0}

            # Update predicted values
            predicted_values["auto_net"] += team["auto_avg_net"]
            predicted_values["auto_processor"] += team["auto_avg_processor"]
            predicted_values["auto_coral_L1"] += team["auto_avg_coral_L1"]
            predicted_values["auto_coral_L2"] += team["auto_avg_coral_L2"]
            predicted_values["auto_coral_L3"] += team["auto_avg_coral_L3"]
            predicted_values["auto_coral_L4"] += team["auto_avg_coral_L4"]
            predicted_values["tele_net"] += team["tele_avg_net"]
            predicted_values["tele_processor"] += team["tele_avg_processor"]
            predicted_values["tele_coral_L1"] += team["tele_avg_coral_L1"]
            predicted_values["tele_coral_L2"] += team["tele_avg_coral_L2"]
            predicted_values["tele_coral_L3"] += team["tele_avg_coral_L3"]
            predicted_values["tele_coral_L4"] += team["tele_avg_coral_L4"]
            predicted_values["endgame_park"] += (
                team["park_percent"] if team["park_percent"] != None else 0
            )
            predicted_values["endgame_deep"] += (
                team["cage_percent_success_deep"]
                if team["cage_percent_success_deep"] != None
                else 0
            )
            predicted_values["endgame_shallow"] += (
                team["cage_percent_success_shallow"]
                if team["cage_percent_success_shallow"] != None
                else 0
            )
            predicted_values["auto_leave"] += (
                tba_team["leave_success_rate"] if tba_team["leave_success_rate"] != None else 0
            )

        return predicted_values

    def predict_value(self, predicted_values: dict, variables: List[str] = None) -> float:
        value = 0

        if not variables:
            variables = self.PREDICTED_VALUES.keys()

        for var, val in predicted_values.items():
            if var in variables:
                value += self.POINT_VALUES[var] * val

        return value

    def get_playoffs_alliances(self):
        """
        Gets playoff alliances from TBA.

        obj_team is all the obj_team data in the database.

        tba_team is all the tba_team data in the database.
        """
        if self.server.has_internet:
            tba_playoffs_data = tba_communicator.tba_request(
                f"event/{self.server.TBA_EVENT_KEY}/alliances"
            )
        else:
            return []
        playoffs_alliances = []

        # Hasn't reached playoffs yet
        if tba_playoffs_data == None:
            return playoffs_alliances

        for alliance in tba_playoffs_data:
            playoffs_alliances.append(
                {
                    "alliance_num": int(alliance["name"].split()[-1]),
                    "picks": [team[3:] for team in alliance["picks"]],
                }
            )
        return playoffs_alliances

    def calc_barge_rp(self, predicted_values):
        """Calculates the expected barge RP for an alliance

        obj_team_data: obj_team data from the database

        team_numbers: teams in the alliance"""
        return int(
            12 * predicted_values["endgame_deep"]
            + 6 * predicted_values["endgame_shallow"]
            + 2 * predicted_values["endgame_park"]
            >= 14
        )

    def calc_coral_rp(self, predicted_values):  # , obj_team, team_list, match_number):
        """Calculates predicted coral RP for an alliance.

        `predicted_values`: (non-empty) dataclass storing score data for the whole alliance
        """
        return int(
            sum([val for datapoint, val in predicted_values.items() if "coral" in datapoint]) >= 25
        )

    def calc_auto_rp(self, predicted_values):
        """Calculates predicted auto RP for an alliance"""
        if (
            predicted_values["auto_leave"] >= 2.5
            and sum(
                [
                    predicted_values["auto_coral_L1"],
                    predicted_values["auto_coral_L2"],
                    predicted_values["auto_coral_L3"],
                    predicted_values["auto_coral_L4"],
                ]
            )
            >= 1
        ):
            return 1.0
        else:
            return 0.0

    def get_actual_values(self, aim, tba_match_data):
        """Pulls actual AIM data from TBA if it exists.
        Otherwise, returns dictionary with all values of 0 and has_tba_data of False.

        aim is the alliance in match to pull actual data for."""
        actual_match_dict = {
            "actual_score": 0,
            "actual_barge_rp": 0.0,
            "actual_coral_rp": 0.0,
            "actual_auto_rp": 0.0,
            "won_match": False,
        }
        match_number = aim["match_number"]

        for match in tba_match_data:
            # Checks the value of winning_alliance to determine if the match has data.
            # If there is no data for the match, winning_alliance is an empty string.
            if (
                match["match_number"] == match_number
                and match["comp_level"] == "qm"
                and match["score_breakdown"] is not None
            ):
                actual_aim = match["score_breakdown"]
                if aim["alliance_color"] == "R":
                    alliance_color = "red"
                else:
                    alliance_color = "blue"
                actual_match_dict["actual_score"] = actual_aim[alliance_color]["totalPoints"]
                # TBA stores RPs as booleans. If the RP is true, they get 1 RP, otherwise they get 0.
                # these are placeholder names since we don't actually know what these datapoints will be called
                if actual_aim[alliance_color]["bargeBonusAchieved"]:
                    actual_match_dict["actual_barge_rp"] = 1.0
                if actual_aim[alliance_color]["coralBonusAchieved"]:
                    actual_match_dict["actual_coral_rp"] = 1.0
                if actual_aim[alliance_color]["autoBonusAchieved"]:
                    actual_match_dict["actual_auto_rp"] = 1.0
                # Gets whether the alliance won the match by checking the winning alliance against the alliance color/
                actual_match_dict["won_match"] = match["winning_alliance"] == alliance_color
                # Actual values to compare predictions
                actual_match_dict["actual_score_auto"] = actual_aim[alliance_color]["autoPoints"]
                actual_match_dict["actual_score_endgame"] = actual_aim[alliance_color][
                    "endGameBargePoints"
                ]
                actual_match_dict["actual_score_tele"] = (
                    actual_aim[alliance_color]["teleopPoints"]
                    - actual_match_dict["actual_score_endgame"]
                )
                actual_match_dict["actual_foul_points"] = actual_aim[alliance_color]["foulPoints"]
                actual_match_dict["cooperated"] = actual_aim[alliance_color][
                    "coopertitionCriteriaMet"
                ]
                # Sets actual_match_data to true once the actual data has been pulled
                break
        # Implementing overrides
        if "override" in aim.keys() and aim["override"]:
            for key, value in aim["override"].items():
                actual_match_dict[key] = value
            actual_match_dict["override"] = aim["override"]

        return actual_match_dict

    def filter_aims_list(self, obj_team, tba_team, aims_list):
        """Filters the aims list to only contain aims where all teams have existing data.
        Prevents predictions from crashing due to being run on teams with no data.

        obj_team is all the obj_team data in the database.

        tba_team is all the tba_team data in the database.

        aims_list is all the aims before filtering."""
        filtered_aims_list = []

        # List of all teams that have existing documents in obj_team and tba_team
        obj_team_numbers = [team_data["team_number"] for team_data in obj_team]
        tba_team_numbers = [team_data["team_number"] for team_data in tba_team]

        # Check each aim for data
        for aim in aims_list:
            has_data = True
            for team in aim["team_list"]:
                if team not in tba_team_numbers and team in self.played_teams:
                    log.warning(
                        f'no tba_team data for team {team} (Alliance {aim["alliance_color"]} in Match {aim["match_number"]})'
                    )
                if team not in obj_team_numbers:
                    has_data = False
                    if team in self.played_teams:
                        log.critical(
                            f'no obj_team data for team {team} (Alliance {aim["alliance_color"]} in Match {aim["match_number"]})'
                        )
                    break
            if has_data == True:
                filtered_aims_list.append(aim)

        return filtered_aims_list

    def calc_win_chance(self, obj_team, team_list, match_number=None):
        """Calculates predicted win probabilities for a RED alliance

        `obj_team`: list of all existing obj_team dicts

        `team_list`: dict containing team numbers in the alliance
                    looks like {"R": ["1678", "254", "4414"], "B": ["125", "6800", "1323"]}

        `match_number`: match to calculate win chance (used for logs)
        """
        # Sets up data needed to calculate win chance
        schema_fields = self.schema["--win_chance"]
        data = {"R": {"mean": 0, "var": 0}, "B": {"mean": 0, "var": 0}}

        # Gets mean and variance for alliance score distribution
        for color in ["R", "B"]:
            for team in team_list[color]:
                obj_data = list(
                    filter(lambda team_data: team_data["team_number"] == team, obj_team)
                )
                if obj_data:
                    obj_data = obj_data[0]
                else:
                    if team in self.played_teams:
                        log.critical(
                            f"no obj_team data for team {team}, cannot calculate win chance"
                        )
                    continue
                team_mean = 0
                team_var = 0
                # Add mean and variance for every score datapoint
                for name, attrs in schema_fields.items():
                    team_mean += obj_data[name] * attrs["weight"]
                    team_var += (obj_data[attrs["sd"]] * attrs["weight"]) ** 2
                data[color]["mean"] += team_mean
                data[color]["var"] += team_var

        # Calculate win chance
        # Find probability of red normal distrubution being greater than blue normal distribution
        dist = {
            "mean": data["R"]["mean"] - data["B"]["mean"],
            "var": data["R"]["var"] + data["B"]["var"],
        }
        # Calculates win chance for red, P(R - B) > 0 => 1 - phi(0)
        if dist["var"] > 0:
            prob_red_wins = round(1 - Norm(dist["mean"], dist["var"] ** 0.5).cdf(0), 3)
        else:
            return 1 if dist["mean"] > 0 else 0

        # Return win chance
        return prob_red_wins

    def update_predicted_aim(self, aims_list):
        "Updates predicted and actual data with new obj_team and tba_team data"
        updates = []
        obj_team = self.server.local_db.find("obj_team")
        tba_team = self.server.local_db.find("tba_team")
        tba_match_data = tba_communicator.tba_request(f"event/{self.server.TBA_EVENT_KEY}/matches")
        dn_predictions = []
        if self.server.has_internet:
            dn_matches = []

            if self.server.dn_model == None:
                log.info(
                    "No suitably trained DoozerNet model available, using win chance calculations"
                )
            elif self.server.dn_model == "specific":
                log.info("Found a suitably trained DoozerNet model for this competition")
            elif self.server.dn_model == "super":
                log.info(
                    "Could not find a suitably trained DoozerNet model for this competition, using SuperProphet model instead."
                )
            # do DoozerNet predictions in batch
            try:
                if self.server.dn_model != None:
                    if self.server.dn_model == "specific":
                        dn_predictions = doozernet_communicator.predict_matches(
                            list(range(1, int(len(self.get_aim_list()) / 2 + 1)))
                        )
                    else:
                        dn_predictions = doozernet_communicator.predict_matches(
                            list(range(1, int(len(self.get_aim_list()) / 2 + 1))), use_super=True
                        )
            except Exception as err:
                log.error(f"Failed to run DoozerNet model: {err}")
        else:
            tba_match_data = []
            self.server.dn_model = None
        filtered_aims_list = self.filter_aims_list(obj_team, tba_team, aims_list)

        finished_matches = []
        # Update every aim
        for aim in filtered_aims_list:
            if aim["match_number"] not in finished_matches:
                # Find opposing alliance
                other_aim = list(
                    filter(
                        lambda some_aim: some_aim["match_number"] == aim["match_number"]
                        and some_aim != aim,
                        filtered_aims_list,
                    )
                )
                if other_aim:
                    other_aim = other_aim[0]
                else:
                    log.critical(
                        f"predicted_aim: alliance {aim['team_list']} has no opposing alliance in match {aim['match_number']}"
                    )
                    continue

                # Create updates
                update = {
                    "match_number": aim["match_number"],
                    "alliance_color_is_red": aim["alliance_color"] == "R",
                }
                other_update = {
                    "match_number": other_aim["match_number"],
                    "alliance_color_is_red": other_aim["alliance_color"] == "R",
                }

                # Add variables that indicate if data exists for the match
                num_tim_docs = len(
                    list(
                        filter(
                            lambda doc: doc["team_number"] in aim["team_list"]
                            and doc["match_number"] == aim["match_number"],
                            self.server.local_db.find("obj_tim"),
                        )
                    )
                )
                update["has_tim_data"] = num_tim_docs >= 1
                update["full_tim_data"] = num_tim_docs == 3
                update["has_tba_data"] = (
                    len(
                        list(
                            filter(
                                lambda tba_doc: "qm" in tba_doc["key"]
                                and tba_doc["match_number"] == aim["match_number"],
                                tba_match_data,
                            )
                        )
                    )
                    == 1
                )

                num_tim_docs = len(
                    list(filter(lambda doc: doc["team_number"] in other_aim["team_list"], obj_team))
                )
                other_update["has_tim_data"] = num_tim_docs >= 1
                other_update["full_tim_data"] = num_tim_docs == 3
                other_update["has_tba_data"] = (
                    len(
                        list(
                            filter(
                                lambda tba_doc: "qm" in tba_doc["key"]
                                and tba_doc["match_number"] == other_aim["match_number"],
                                tba_match_data,
                            )
                        )
                    )
                    == 1
                )

                # Calculate predicted values data classes
                aim_predicted_values = self.calc_predicted_values(
                    obj_team, tba_team, aim["team_list"]
                )
                other_aim_predicted_values = self.calc_predicted_values(
                    obj_team, tba_team, other_aim["team_list"]
                )

                # Add gamepieces
                for action, value in aim_predicted_values.items():
                    update[f"_{action}"] = value
                for action, value in other_aim_predicted_values.items():
                    other_update[f"_{action}"] = value

                # Calculate predicted scores
                update["predicted_score"] = self.predict_value(aim_predicted_values)
                update["predicted_auto_score"] = self.predict_value(
                    aim_predicted_values,
                    list(filter(lambda key: "auto" in key, self.PREDICTED_VALUES.keys())),
                )
                update["predicted_tele_score"] = self.predict_value(
                    aim_predicted_values,
                    list(filter(lambda key: "tele" in key, self.PREDICTED_VALUES.keys())),
                )
                update["predicted_endgame_score"] = self.predict_value(
                    aim_predicted_values,
                    list(filter(lambda key: "endgame" in key, self.PREDICTED_VALUES.keys())),
                )

                # Other alliance
                other_update["predicted_score"] = self.predict_value(other_aim_predicted_values)
                other_update["predicted_auto_score"] = self.predict_value(
                    other_aim_predicted_values,
                    list(filter(lambda key: "auto" in key, self.PREDICTED_VALUES.keys())),
                )
                other_update["predicted_tele_score"] = self.predict_value(
                    other_aim_predicted_values,
                    list(filter(lambda key: "tele" in key, self.PREDICTED_VALUES.keys())),
                )
                other_update["predicted_endgame_score"] = self.predict_value(
                    other_aim_predicted_values,
                    list(filter(lambda key: "endgame" in key, self.PREDICTED_VALUES.keys())),
                )

                # Calculate RPs
                update["predicted_barge_rp"] = self.calc_barge_rp(aim_predicted_values)
                update["predicted_coral_rp"] = self.calc_coral_rp(aim_predicted_values)
                update["predicted_auto_rp"] = self.calc_auto_rp(aim_predicted_values)
                other_update["predicted_barge_rp"] = self.calc_barge_rp(aim_predicted_values)
                other_update["predicted_coral_rp"] = self.calc_coral_rp(other_aim_predicted_values)
                other_update["predicted_auto_rp"] = self.calc_auto_rp(other_aim_predicted_values)

                # Calculate win chance
                if aim["alliance_color"] == "R":
                    update["win_chance"] = self.calc_win_chance(
                        obj_team,
                        {
                            aim["alliance_color"]: aim["team_list"],
                            other_aim["alliance_color"]: other_aim["team_list"],
                        },
                        aim["match_number"],
                    )
                    other_update["win_chance"] = 1 - update["win_chance"]
                else:
                    other_update["win_chance"] = self.calc_win_chance(
                        obj_team,
                        {
                            other_aim["alliance_color"]: other_aim["team_list"],
                            aim["alliance_color"]: aim["team_list"],
                        },
                        other_aim["match_number"],
                    )
                    update["win_chance"] = 1 - other_update["win_chance"]
                if dn_predictions:
                    try:
                        if aim["alliance_color"] == "R":
                            update["win_chance"] = 1 - dn_predictions[aim["match_number"] - 1]
                            other_update["win_chance"] = 1 - update["win_chance"]
                        else:
                            other_update["win_chance"] = (
                                1 - dn_predictions[other_aim["match_number"] - 1]
                            )
                            update["win_chance"] = 1 - other_update["win_chance"]
                    except Exception as e:
                        log.error(f"Failed to get DoozerNet prediction: {e}")
                        dn_predictions = []

                # Calculate actual values
                update.update(self.get_actual_values(aim, tba_match_data))
                other_update.update(self.get_actual_values(other_aim, tba_match_data))

                # Add aim team list
                update["team_numbers"] = aim["team_list"]
                other_update["team_numbers"] = other_aim["team_list"]

                updates.extend([update, other_update])
                finished_matches.append(aim["match_number"])
                if self.server.dn_model != None:
                    dn_matches.extend(
                        [
                            update["team_numbers"] + other_update["team_numbers"],
                            other_update["team_numbers"] + update["team_numbers"],
                        ]
                    )
        return updates

    def update_playoffs_alliances(self):
        """Runs the calculations for predicted values in playoffs matches

        obj_team is all the obj_team data in the database.

        tba_team is all the tba_team data in the database.

        playoffs_alliances is a list of alliances with team numbers
        """
        # updates = []
        # obj_team = self.server.local_db.find("obj_team")
        # tba_team = self.server.local_db.find("tba_team")
        playoffs_alliances = self.get_playoffs_alliances()

        return playoffs_alliances

        # # Check if empty
        # if playoffs_alliances == updates:
        #     return updates

        # for alliance in playoffs_alliances:
        #     predicted_values = self.calc_predicted_values(obj_team, tba_team, alliance["picks"])
        #     update = alliance

        #     # Calculate predicted scores
        #     update["predicted_score"] = self.predict_value(predicted_values)

        #     updates.append(update)
        # return updates

    def run(self):
        timer = Timer()

        # Check which teams have played matches, used for filtering 'no data' logs
        if self.server.has_internet:
            team_statuses = tba_communicator.tba_request(
                f"event/{utils.TBA_EVENT_KEY}/teams/statuses"
            )
            self.played_teams = []
            for team, data in team_statuses.items():
                try:
                    if data["qual"]["ranking"]["matches_played"] > 0:
                        self.played_teams.append(team[3:])
                except:
                    continue

        match_schedule = self.get_aim_list()
        teams = self.get_teams_list()
        aims = []
        # Finds all overrides for actual scores
        overrides = {
            f"{aim['match_number']}{aim['alliance_color_is_red']}": aim["override"]
            for aim in self.server.local_db.find("predicted_aim")
            if "override" in aim.keys()
        }
        for alliance in match_schedule:
            for team in alliance["team_list"]:
                if team in teams:
                    alliance["override"] = (
                        overrides[f"{alliance['match_number']}{alliance['alliance_color']=='R'}"]
                        if f"{alliance['match_number']}{alliance['alliance_color']=='R'}"
                        in overrides.keys()
                        else {}
                    )
                    aims.append(alliance)
                    break

        self.server.local_db.delete_data("predicted_aim")
        self.server.local_db.delete_data("predicted_alliances")
        self.server.local_db.insert_documents("predicted_aim", self.update_predicted_aim(aims))
        self.server.local_db.insert_documents(
            "predicted_alliances", self.update_playoffs_alliances()
        )

        override.apply_override("predicted_aim")

        timer.end_timer(__file__)
