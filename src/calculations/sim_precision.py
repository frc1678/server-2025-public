from datetime import datetime

from calculations.base_calculations import BaseCalculations
import tba_communicator
import utils
import logging
from typing import List, Dict, Union
import numpy as np
from timer import Timer
import override

log = logging.getLogger(__name__)


class SimPrecisionCalc(BaseCalculations):
    def __init__(self, server):
        super().__init__(server)
        self.watched_collections = ["unconsolidated_totals"]
        self.sim_schema = utils.read_schema("schema/calc_sim_precision_schema.yml")

    def get_scout_tim_score(
        self, scout: str, match_number: int, required: Dict[str, Dict[str, Union[int, List[str]]]]
    ) -> Union[int, None]:
        """Gets the score for a team in a match reported by a scout.

        `scout`: the scout's name

        `match_number`: match number to calculate

        `required`: dictionary of required datapoints `{weight: value, calculation: [calculations]}` from schema

        Returns the sum of the scout's reported scoring actions in that match.
        """
        scout_data = {"unconsolidated_totals": [], "auto_pim": []}
        scout_data["unconsolidated_totals"] = self.server.local_db.find(
            "unconsolidated_totals", {"match_number": match_number, "scout_name": scout}
        )
        if not scout_data["unconsolidated_totals"]:
            log.warning(f"No data from Scout {scout} in Match {match_number}")
            return
        scout_data["unconsolidated_totals"] = scout_data["unconsolidated_totals"][0]
        team_num = scout_data["unconsolidated_totals"]["team_number"]
        scout_data["auto_pim"] = self.server.local_db.find(
            "auto_pim", {"match_number": match_number, "team_number": team_num}
        )[0]

        total_score = 0
        for datapoint, weight in required.items():
            # split using . to get rid of collection name
            collection, datapoint = datapoint.split(".")
            total_score += scout_data[collection][datapoint] * weight
        return total_score

    def get_aim_scout_scores(
        self,
        match_number: int,
        alliance_color_is_red: bool,
        required: Dict[str, Dict[str, Union[int, List[str]]]],
    ) -> Dict[str, Dict[str, int]]:
        """Gets the individual TIM scores reported by each scout for an alliance in a match. Basically, combines the output from `get_scout_tim_score`, compiling all scouts in one alliance.

        `match_number`: match to calculate

        `alliance_color_is_red`: which alliance in the match to calculate

        `required`: dictionary of required datapoints `{weight: value, calculation: [calculations]}` from schema.

        Returns a dictionary where keys are team numbers and values are dictionaries of {<scout name>: <tim score>}.
        """
        scores_per_team = {}
        scout_data = self.server.local_db.find(
            "unconsolidated_totals",
            {
                "match_number": match_number,
                "alliance_color_is_red": alliance_color_is_red,
            },
        )
        teams = set([document["team_number"] for document in scout_data])
        # Populate dictionary with teams in alliance
        for team in teams:
            scores_per_team[team] = {}
        for document in scout_data:
            scout_tim_score = self.get_scout_tim_score(
                document["scout_name"], match_number, required
            )
            scores_per_team[document["team_number"]].update(
                {document["scout_name"]: scout_tim_score}
            )

        return scores_per_team

    def get_aim_scout_avg_errors(
        self,
        aim_scout_scores: Dict[str, Dict[str, int]],
        tba_aim_score: int,
        match_number: int,
        alliance_color_is_red: bool,
    ) -> Dict[str, float]:
        """Gets the average error of each scout ("SPR") in a match by comparing the sums of reported scores against the official TBA score for all combinations of scouts.

        `aim_scout_scores`: output from `get_aim_scout_scores()`

        `tba_aim_score`: output from `get_tba_value()`

        `match_number`: match to calculate SPRs

        `alliance_color_is_red`: alliance to calculate

        Returns a dict with keys as scout names and values as their SPRs.
        """
        if len(aim_scout_scores) != 3:
            log.warning(
                f"Missing {'red' if alliance_color_is_red else 'blue'} alliance scout data for Match {match_number}"
            )
            return {}

        # Get the reported values for each scout
        team1_scouts, team2_scouts, team3_scouts = aim_scout_scores.values()

        # Iterate through all possible combinations
        all_scout_errors = {}
        for scout1, score1 in team1_scouts.items():
            scout1_errors = all_scout_errors.get(scout1, [])
            for scout2, score2 in team2_scouts.items():
                scout2_errors = all_scout_errors.get(scout2, [])
                for scout3, score3 in team3_scouts.items():
                    scout3_errors = all_scout_errors.get(scout3, [])
                    # Calculate error
                    error = abs((score1 + score2 + score3 - tba_aim_score) / 3)
                    scout1_errors.append(error)
                    scout2_errors.append(error)
                    scout3_errors.append(error)
                    all_scout_errors[scout3] = scout3_errors
                all_scout_errors[scout2] = scout2_errors
            all_scout_errors[scout1] = scout1_errors
        scout_avg_errors = {scout: np.mean(errors) for scout, errors in all_scout_errors.items()}
        return scout_avg_errors

    def get_tba_value(
        self,
        tba_match_data: List[dict],
        tba_points: List,
        match_number: int,
        alliance_color_is_red: bool,
        tba_weight: int,
    ) -> int:
        """Get the official value from TBA for the required datapoints.

        `tba_match_data`: output from `tba_communicator.tba_request(f"event/{utils.TBA_EVENT_KEY}/matches")`

        `tba_points`: tba_datapoints field in schema calculations

        `match_number`: match to calculate

        `alliance_color_is_red`: alliance to calculate

        Returns the official score value of the datapoint from TBA.
        """
        alliance_color = ["blue", "red"][int(alliance_color_is_red)]

        for match in tba_match_data:
            if match["match_number"] == match_number and match["comp_level"] == "qm":
                tba_match_data = match["score_breakdown"][alliance_color]
        total = 0
        for datapoint in tba_points:
            split_datapoint = datapoint.split(".")
            if len(split_datapoint) == 1:
                total += tba_match_data[datapoint]
            elif len(split_datapoint) == 2:
                total += tba_match_data[split_datapoint[0]][split_datapoint[1]]
            elif len(split_datapoint) == 3:
                total += (
                    1
                    if tba_match_data[split_datapoint[0]][split_datapoint[1]][split_datapoint[2]]
                    else 0
                )
        total *= tba_weight
        return total

    def update_sim_precision_calcs(self, unconsolidated_sims):
        """Creates scout-in-match precision updates; uses all prior functions to calculate SPR for all available matches

        `sims`: list of dicts containing scout name and match number for all available scouts and matches

        Returns a list of dicts with the initial documents in `sims` plus the calculated SPRs."""
        tba_match_data: List[dict] = tba_communicator.tba_request(
            f"event/{utils.TBA_EVENT_KEY}/matches"
        )
        # When we're running server at competition, we have to wait until TBA updates match data, so we get the latest TBA match and our latest match
        latest_match = max([s["match_number"] for s in unconsolidated_sims] + [0])
        latest_tba_match = max(
            [
                t["match_number"]
                for t in tba_match_data
                if t["score_breakdown"] is not None and t["comp_level"] == "qm"
            ]
            + [0]
        )
        updates = []

        # Create dicts for shared data between scouts
        aim_match_errors = {}

        # Iterate up to either the latest tba match or match where we have data (To avoid crashing)
        for match_number in range(1, min(latest_match, latest_tba_match) + 1):
            # Create match_number keys
            aim_match_errors[match_number] = {}

            # Calculate data for each calculation
            for calculation, schema in self.sim_schema["calculations"].items():
                required = schema["requires"]
                tba_points = schema["tba_datapoints"]
                if "tba_weight" in schema.keys():
                    weight = schema["tba_weight"]
                else:
                    weight = 1
                # Get the scores from TBA
                red_tba_aim_score = self.get_tba_value(
                    tba_match_data, tba_points, match_number, True, tba_weight=weight
                )
                blue_tba_aim_score = self.get_tba_value(
                    tba_match_data, tba_points, match_number, False, tba_weight=weight
                )

                # Get the scores of all scouts in a match
                red_aim_scouts_reported_values = self.get_aim_scout_scores(
                    match_number, True, required
                )
                blue_aim_scouts_reported_values = self.get_aim_scout_scores(
                    match_number, False, required
                )

                # Get the average errors of all scouts in a match
                red_aim_scout_errors = self.get_aim_scout_avg_errors(
                    red_aim_scouts_reported_values,
                    red_tba_aim_score,
                    match_number,
                    True,
                )
                blue_aim_scout_errors = self.get_aim_scout_avg_errors(
                    blue_aim_scouts_reported_values,
                    blue_tba_aim_score,
                    match_number,
                    False,
                )

                # Update to one dictionary
                # True is for red alliance and False is for blue alliance
                aim_match_errors[match_number][calculation] = {
                    True: red_aim_scout_errors,
                    False: blue_aim_scout_errors,
                }

        for sim in unconsolidated_sims:
            sim_data = self.server.local_db.find("unconsolidated_totals", sim)[0]
            if sim_data["match_number"] > latest_tba_match:
                continue
            update = {
                "scout_name": sim_data["scout_name"],
                "match_number": sim_data["match_number"],
                "team_number": sim_data["team_number"],
                "alliance_color_is_red": sim_data["alliance_color_is_red"],
            }
            for match in tba_match_data:
                if (
                    match["match_number"] == sim_data["match_number"]
                    and match["comp_level"] == "qm"
                ):
                    # Convert match timestamp from Unix time (on TBA) to human-readable
                    if match["actual_time"] is not None:
                        update["timestamp"] = datetime.fromtimestamp(match["actual_time"])
                    else:
                        update["timestamp"] = datetime.fromtimestamp(match["time"])
                    break
            else:
                continue

            calculations = dict()
            for calculation, schema in self.sim_schema["calculations"].items():
                for name, error in aim_match_errors[sim["match_number"]][calculation][
                    sim_data["alliance_color_is_red"]
                ].items():
                    if name == sim["scout_name"]:
                        calculations[calculation] = error
                if calculation not in calculations:
                    calculations[calculation] = None

            update.update(calculations)

            # TODO this is a hotfix for 2025 Reefscape
            # Since human player net scoring messes up overal point precision, we calculate it manually in `sim_precision.py`
            overall_spr = 0
            for var, val in update.items():
                if var in self.sim_schema["calculations"].keys():
                    if val != None:
                        overall_spr += val
            update["sim_precision"] = overall_spr

            if [update["team_number"], update["match_number"], update["scout_name"]] not in [
                [u["team_number"], u["match_number"], u["scout_name"]] for u in updates
            ]:
                updates.append(update)
        return updates

    def run(self):
        "Run the SIM precision calculations and update them to the database."
        timer = Timer()

        sims = []
        for document in self.server.local_db.find(self.watched_collections[0]):
            sims.append(
                {
                    "scout_name": document["scout_name"],
                    "match_number": document["match_number"],
                }
            )

        self.server.local_db.delete_data("sim_precision")
        self.server.local_db.insert_documents(
            "sim_precision", self.update_sim_precision_calcs(sims)
        )

        override.apply_override("sim_precision")

        timer.end_timer(__file__)
