#!/usr/bin/env python3

"""Run TIM calculations dependent on TBA data."""

import copy
from typing import List, Dict, Tuple, Any

from calculations import base_calculations
import tba_communicator
import utils
from server import Server
import logging
from timer import Timer
import override

log = logging.getLogger(__name__)


class TBATIMCalc(base_calculations.BaseCalculations):
    """Runs TBA Tim calculations"""

    SCHEMA = utils.unprefix_schema_dict(utils.read_schema("schema/calc_tba_tim_schema.yml"))["tba"]

    def __init__(self, server):
        """Creates an empty list to add references of calculated tims to"""
        super().__init__(server)
        self.calculated = set([tim["match_number"] for tim in self.server.local_db.find("tba_tim")])

    @staticmethod
    def calc_tba_bool(match_data: Dict, alliance: str, filters: Dict) -> bool:
        """Returns a bool representing if match_data meets all filters defined in filters."""
        for key, value in filters.items():
            if match_data["score_breakdown"][alliance][key] != value:
                return False
        return True

    @staticmethod
    def get_robot_number_and_alliance(team_num: str, match_data: Dict) -> Tuple[int, str]:
        """Gets the robot number (e.g. the `1` in initLineRobot1) and alliance color."""
        team_key = f"frc{team_num}"
        for alliance in ["red", "blue"]:
            for i, key in enumerate(match_data["alliances"][alliance]["team_keys"], start=1):
                if team_key == key:
                    return i, alliance
        raise ValueError(f'Team {team_num} not found in match {match_data["match_number"]}')

    @staticmethod
    def get_team_list_from_match(match_data: Dict) -> List[str]:
        """Extracts list of teams that played in the match with data given in match_data."""
        team_list = []
        for alliance in ["red", "blue"]:
            team_list.extend(
                # This fetches the numeric values from the string
                [team[3:] for team in match_data["alliances"][alliance]["team_keys"]]
            )
        return team_list

    # @staticmethod
    # def calculate_driver_stations(match, seperate_alliances=False) -> Dict[str, str]:
    #     "Given match data, return a list for each alliance with each teams driver position"
    #     blue_team_keys = match["alliances"]["blue"]["team_keys"]
    #     red_team_keys = match["alliances"]["red"]["team_keys"]

    #     blue_driver_positions = {}
    #     blue_driver_positions[blue_team_keys[0][3:]] = "left"
    #     blue_driver_positions[blue_team_keys[1][3:]] = "center"
    #     blue_driver_positions[blue_team_keys[2][3:]] = "right"

    #     red_driver_positions = {}
    #     red_driver_positions[red_team_keys[0][3:]] = "left"
    #     red_driver_positions[red_team_keys[1][3:]] = "center"
    #     red_driver_positions[red_team_keys[2][3:]] = "right"

    #     if seperate_alliances:
    #         driver_stations = {}
    #         driver_stations["blue"] = blue_driver_positions
    #         driver_stations["red"] = red_driver_positions
    #         return driver_stations

    #     # combines the two to make it easier to search through. One team can't play on both sides so it does not break anything
    #     blue_driver_positions.update(red_driver_positions)
    #     return blue_driver_positions

    def calculate_tim(self, team_number: str, match) -> Dict[str, Any]:
        """Given a team number and a match that it's from, calculate that tim"""
        match_number: int = match["match_number"]
        tim = {"team_number": team_number, "match_number": match_number}

        # Check if an important thing like score_breakdown is in the match data
        if match["score_breakdown"] is None:
            log.warning(f"TBA TIM Calculation on {match_number} missing match data")

        robot_number, alliance = self.get_robot_number_and_alliance(team_number, match)
        # driver_stations = self.calculate_driver_stations(match)

        for calculation, tim_requirements in self.SCHEMA.items():
            # calculation is the name of the field, like "mobility" for example
            # tim_requirements is dict of stuff including {"type": "bool"} and something like
            # {"taxiRobot": "Yes"}
            tim_requirements_copy = copy.deepcopy(tim_requirements)

            # type does not need to be in the final data, so we remove it
            # {"type": "bool", "field": "value"} -> {"field": "value"}
            del tim_requirements_copy["type"]

            # Add a number after each field that ends in Robot
            # {"field": "value"} -> {"field1": "value"}
            for field, expected_value in tim_requirements.items():
                if field.endswith("Robot"):
                    del tim_requirements_copy[field]
                    tim_requirements_copy[f"{field}{robot_number}"] = expected_value

            # # calculate driver stations
            # if calculation == "driver_station":
            #     tim[calculation] = driver_stations[team_number]
            #     continue

            # Fun calc_tba_bool for each calculation, and add it to tim
            if isinstance(tim["match_number"], int):
                # since spotlight doesn't have a tim_requirements field
                tim[calculation] = self.calc_tba_bool(
                    match,
                    alliance,
                    tim_requirements_copy,
                )

        tim["climb_level"] = match["score_breakdown"][alliance][f"endGameRobot{robot_number}"]

        return tim

    def run(self):
        """Executes the TBA TIM calculations"""
        timer = Timer()

        # Delete and re-insert if updating all data
        self.server.local_db.delete_data("tba_tim")

        new_data = []
        for match in list(
            filter(
                lambda match: match["comp_level"] == "qm",
                tba_communicator.tba_request(f"event/{Server.TBA_EVENT_KEY}/matches"),
            )
        ):
            for team_number in self.get_team_list_from_match(match):
                # Calculate the tim, getting the team and match from entry
                calculated_tim = self.calculate_tim(team_number, match)

                # Ensure we don't write results from a calculation that errorred
                if not calculated_tim:
                    continue

                new_data.append(calculated_tim)

                # Add the tim ref to calculated, right after it gets calculated
                self.calculated.add(match["match_number"])

        self.server.local_db.insert_documents("tba_tim", utils.unique_ld(new_data))

        override.apply_override("tba_tims")

        timer.end_timer(__file__)
