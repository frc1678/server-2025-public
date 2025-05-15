#!/usr/bin/env python3
"""Calculate subjective team data"""

import utils
import logging
from calculations import base_calculations
from typing import Dict, List
from timer import Timer
import override

log = logging.getLogger(__name__)


class SubjTeamCalcs(base_calculations.BaseCalculations):
    """Runs subjective team calculations"""

    SCHEMA = utils.read_schema("schema/calc_subj_team_schema.yml")

    def __init__(self, server):
        """Overrides watched collections, passes server object"""
        super().__init__(server)
        self.watched_collections = ["subj_tim"]
        self.teams_that_have_competed = set()

    def teams_played_with(self, team: str) -> List[str]:
        """Returns a list of teams that the given team has played with so far, including themselves
        and including repeats"""
        partners = []
        # matches_played is a dictionary where keys are match numbers and values represent alliance color
        matches_played = {}
        for tim in self.server.local_db.find("subj_tim", {"team_number": team}):
            matches_played.update({tim["match_number"]: tim["alliance_color_is_red"]})
        for match_num, alliance_color in matches_played.items():
            # Find subj_tim data for robots in the same match and alliance as the team
            alliance_data = self.server.local_db.find(
                "subj_tim", {"match_number": match_num, "alliance_color_is_red": alliance_color}
            )
            partners.extend([tim["team_number"] for tim in alliance_data])
        return partners

    def unadjusted_ability_calcs(self, team: str) -> Dict[str, float]:
        """Retrieves subjective AIM info for the given team and returns a dictionary with
        calculations for that team"""
        calculations = {}
        # self.SCHEMA['data'] tells us which fields we need to put in the database that don't
        # require calculations
        subj_tims = self.server.local_db.find("subj_tim", {"team_number": team})

        for data_field in self.SCHEMA["data"].keys():
            vals = []
            if data_field == "team_number":
                calculations[data_field] = team
                continue

            for st in subj_tims:
                try:
                    vals.append(st[data_field])
                except:
                    continue

            if not vals:
                calculations[data_field] = None
            else:
                calculations[data_field] = self.modes(vals)[0]
        # Counts are simply incremented if the variable happened in a match
        for team_var, tim_var in self.SCHEMA["--counts"].items():
            calculations[team_var] = sum(map(lambda t: t[tim_var], subj_tims))
        # Next, actually run the calculations
        for calc_name, calc_info in self.SCHEMA["unadjusted_calculations"].items():
            collection_name, _, ranking_name = calc_info["requires"][0].partition(".")
            # For calculations such as driver_field_awareness and driver_agility,
            # we just pull the rankings from the database and average them
            # Lists average each index, ex: [0, 3], [2, 1] -> [1, 2]
            # If there is "ignore" in calc_info, ignore those values
            team_rankings = []
            ignore_filter = lambda data: not ("ignore" in calc_info and data in calc_info["ignore"])
            is_list = calc_info["type"] == "List"
            for tim in self.server.local_db.find(collection_name, {"team_number": team}):
                # If robot died in match, excludes their field awareness and agility scores from that match
                if tim["died"]:
                    continue
                tim_value = tim[ranking_name]
                if is_list:
                    team_rankings.append(tim_value)
                elif ignore_filter(tim_value):
                    team_rankings.append(tim_value)
            # HARD-CODED 2025 PINNACLES HOTFIX
            if calc_name != "avg_time_left_to_climb":
                average_team_rankings = (
                    self.avg(team_rankings)
                    if not is_list
                    else [  # Average each index
                        self.avg(
                            [value[index] for value in team_rankings if ignore_filter(value[index])]
                        )
                        for index in range(len(team_rankings[0]))
                    ]
                )
            else:
                average_team_rankings = self.avg([val for val in team_rankings if val != 0])
            calculations[calc_name] = average_team_rankings

        return calculations

    def adjusted_ability_calcs(self) -> Dict[str, Dict[int, float]]:
        """Retrieves subjective AIM data for all teams and recalculates adjusted ability scores
        for each team. Recalculating all of them is necessary because ability scores compensate for
        luck of match schedule, so a team's ability score will depend on the unadjusted
        scores for all of their alliance partners"""
        # If no teams have competed yet, there is no point in running the calculation
        if len(self.teams_that_have_competed) == 0:
            return {}

        calculations = {}
        for calc_name, calc_info in self.SCHEMA["component_calculations"].items():
            collection_name, _, unadjusted_calc = calc_info["requires"][0].partition(".")
            # scores is a dictionary of team numbers to rank score
            scores = {}
            for team in self.teams_that_have_competed:
                tim = self.server.local_db.find(collection_name, {"team_number": team})
                if tim:
                    scores[team] = tim[0][unadjusted_calc]
            # Now scale the scores so they range from 0 to 1, and use those scaled scores to
            # compensate for alliance partners
            # That way, teams that are always paired with good/bad teams won't have unfair rankings
            if calc_info["type"] == "List":
                # Calculate for each index, ex: [0, 1], [2, 3] calculates 0 & 2 together and 1 & 3 together
                for index in range(len(list(scores.values())[0])):
                    self.scale_scores(
                        {
                            team: score[index] for team, score in scores.items()
                        },  # Only the scores at the index
                        calculations,
                        calc_name,
                        index,
                    )
            else:
                self.scale_scores(scores, calculations, calc_name)
        return calculations

    def scale_scores(
        self,
        scores: Dict[str, float],
        calculations: Dict[str, Dict[str, float]],
        calc_name: str,
        index: int = None,
    ) -> None:
        """Calculates scores adjusted for teammate score and scaled from 0 to 1"""
        if not scores:
            return
        filtered_scores = dict()
        for team_, s in scores.items():
            if s is not None:
                filtered_scores[team_] = s
            else:
                log.critical(f"No score for team {team_=}")
                filtered_scores[team_] = 0
        worst = min(filtered_scores.values())
        best = max(filtered_scores.values())

        scaled_scores = {
            team: (((score - worst) / (best - worst)) if best - worst != 0 else 0)
            for team, score in filtered_scores.items()
        }
        for team, score in filtered_scores.items():
            teammate_scaled_scores = [
                scaled_scores[partner] for partner in self.teams_played_with(team)
            ]
            calculations[team] = calculations.get(team, {})
            # If teammates tend to rank low, the team's score is lowered more than if teammates tend to rank high
            if index is None:
                calculations[team][calc_name] = score * self.avg(teammate_scaled_scores)
            elif index == 0:
                calculations[team][calc_name] = [score * self.avg(teammate_scaled_scores)]
            else:
                calculations[team][calc_name].append(score * self.avg(teammate_scaled_scores))

    def calculate_driver_ability(self):
        """Takes a weighted average of all the adjusted component scores to calculate overall driver ability."""
        calculations = {}
        for calc_name, calc_info in self.SCHEMA["averaged_calculations"].items():
            # ability_dict is a dictionary where keys are team numbers
            # and values are driver_ability scores
            ability_dict = {}
            for team in self.teams_that_have_competed:
                # scores is a list of the normalized, adjusted subjective ability scores for the team
                # For example, if they have good agility and average
                # field awareness, scores might look like [.8, -.3]
                scores = []
                for requirement in calc_info["requires"]:
                    collection_name, _, score_name = requirement.partition(".")
                    scores.append(
                        self.server.local_db.find(collection_name, {"team_number": team})[0][
                            score_name
                        ]
                    )
                # driver_ability is a weighted average of its component scores
                ability_dict[team] = self.avg(scores, calc_info["weights"])
            # Put the driver abilities of all teams in a list
            driver_ability_list = list(ability_dict.values())
            normalized_abilities = dict(
                zip(ability_dict.keys(), self.get_z_scores(driver_ability_list))
            )
            for team, driver_ability in normalized_abilities.items():
                calculations[team] = calculations.get(team, {})
                if calc_name == "defensive_driver_ability":
                    calculations[team][calc_name] = driver_ability + 2
                elif calc_name == "proxy_driver_ability":
                    calculations[team][calc_name] = (driver_ability + 3) ** 2
                else:
                    calculations[team][calc_name] = driver_ability
        return calculations

    def run(self):
        timer = Timer()

        # Adjusted calcs have to be re-run on all teams that have competed
        # because team data changing for one team affects all teams that played with that team
        self.teams_that_have_competed = set()
        for tim in self.server.local_db.find("subj_tim"):
            self.teams_that_have_competed.add(tim["team_number"])
        self.server.local_db.delete_data("subj_team")

        updated_teams = self.get_teams_list()
        for team in updated_teams:
            new_calc = self.unadjusted_ability_calcs(team)
            self.server.local_db.insert_documents("subj_team", new_calc)
        if len(self.teams_that_have_competed) != 0:
            # Now use the new info to recalculate adjusted ability scores
            adjusted_calcs = self.adjusted_ability_calcs()
            for team in self.teams_that_have_competed:
                self.server.local_db.update_document(
                    "subj_team", adjusted_calcs[team], {"team_number": team}
                )

            # Use the adjusted ability scores to calculate driver ability
            driver_ability_calcs = self.calculate_driver_ability()
            for team in self.teams_that_have_competed:
                self.server.local_db.update_document(
                    "subj_team", driver_ability_calcs[team], {"team_number": team}
                )

        override.apply_override("subj_team")

        timer.end_timer(__file__)
