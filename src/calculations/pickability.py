from calculations import base_calculations
import utils
import logging
from timer import Timer
import tba_communicator
import statistics
from calculations import predicted_aim
import override

log = logging.getLogger(__name__)


class PickabilityCalc(base_calculations.BaseCalculations):
    """This class calculates pickability"""

    def __init__(self, server):
        super().__init__(server)
        self.pickability_schema = utils.read_schema("schema/calc_pickability_schema.yml")
        self.watched_collections = ["obj_team"]
        self.played_teams = []
        self.predicted_aim = predicted_aim.PredictedAimCalc(server)

    def calculate_pickability(self, calc_name: str, team_data: dict) -> float:
        """Calculates first and second pickability

        calc_name is which pickability to calculate (e.g. first or second)
        team_data is the data required to perform the weighted sum
        returns the weighted sum
        """
        weighted_sum = 0
        for var, weight in self.pickability_schema["calculations"][calc_name].items():
            if var != "type":
                try:
                    weighted_sum += team_data[var] * weight
                except:
                    pass

        return weighted_sum

    def calc_offensive_2nd_pickability(
        self, team_number, team_data: dict, tba_data: dict, auto_data: dict
    ) -> float:
        one_team_data = list(filter(lambda t: t["team_number"] == team_number, team_data))
        one_tba_data = list(filter(lambda t: t["team_number"] == team_number, tba_data))
        auto_data = list(filter(lambda t: t["team_number"] == team_number, auto_data))
        if one_team_data:
            one_team_data = one_team_data[0]
            if one_team_data["cage_percent_success_deep"] == None:
                one_team_data["cage_percent_success_deep"] = 0
            if one_team_data["cage_percent_success_shallow"] == None:
                one_team_data["cage_percent_success_shallow"] = 0
        else:
            one_team_data = {"cage_percent_success_deep": 0, "cage_percent_success_shallow": 0}
            log.error(f"No obj team data for team {team_number}.")
        if one_tba_data:
            one_tba_data = one_tba_data[0]
        else:
            one_tba_data = {"leave_success_rate": 0}
            log.error(f"No TBA team data for team {team_number}.")

        has_compatible_auto = int(
            sum(
                [
                    path["start_position"] == "3"
                    or path["start_position"] == "4"
                    or path["start_position"] == "2"
                    for path in auto_data
                ]
            )
            >= 1
            and sum(
                [
                    "F1" in path["score_1"] or "F2" in path["score_1"] or "F6" in path["score_1"]
                    for path in auto_data
                ]
            )
            >= 1
        )

        # Auto calculation
        score_values = {
            "reef_F1_L1": 3,
            "reef_F2_L1": 4,
            "reef_F3_L1": 6,
            "reef_F4_L1": 7,
            "reef_F5_L1": 6,
            "reef_F6_L1": 7,
            "reef_F1_L2": 3,
            "reef_F2_L2": 4,
            "reef_F3_L2": 6,
            "reef_F4_L2": 7,
            "reef_F5_L2": 6,
            "reef_F6_L2": 7,
            "reef_F1_L3": 3,
            "reef_F2_L3": 4,
            "reef_F3_L3": 6,
            "reef_F4_L3": 7,
            "reef_F5_L3": 6,
            "reef_F6_L3": 7,
            "reef_F1_L4": 3,
            "reef_F2_L4": 4,
            "reef_F3_L4": 6,
            "reef_F4_L4": 7,
            "reef_F5_L4": 6,
            "reef_F6_L4": 7,
            "net": 4,
            "processor": 6,
        }
        score_1_raw = [
            path["score_1"]
            for path in auto_data
            if path["score_1"] != "none" and "drop" not in path["score_1"]
        ]
        score_1_key = [score[5:] if "fail" in score else score for score in score_1_raw]
        mode_score = statistics.mode(score_1_key) if score_1_key else None

        if mode_score:
            mode_scores = [score for score in score_1_raw if statistics.mode(score_1_key) in score]
            mode_score_success_rate = len(
                [score for score in mode_scores if not "fail" in score]
            ) / len(mode_scores)

        can_intake_reef = False
        can_score_net = True
        for path in auto_data:
            if can_intake_reef and can_score_net:
                break
            for action in path.values():
                if "intake_reef" in str(action):
                    can_intake_reef = True
                elif "net" in str(action):
                    can_score_net = True

        # Tele calculation
        # reef & net worth 3.5
        # all expected cycles goes into whatever they score the most
        tele_weights = {"net": 3.5, "reef": 2.5, "processor": 2}
        predicted_values = self.predicted_aim.calc_predicted_values(
            team_data, tba_data, [team_number]
        )
        scoring = {
            "net": predicted_values["tele_net"],
            "reef": predicted_values["tele_coral_L1"]
            + predicted_values["tele_coral_L2"]
            + predicted_values["tele_coral_L3"]
            + predicted_values["tele_coral_L4"],
            "processor": predicted_values["tele_processor"],
        }
        optimal_element = max(scoring, key=scoring.get)
        tele = tele_weights[optimal_element] * one_team_data["avg_expected_cycles"]

        if mode_score:
            auto = (
                2 * one_tba_data["leave_success_rate"]
                + has_compatible_auto
                * (
                    mode_score_success_rate * score_values[mode_score]
                    + 2.5 * int(can_intake_reef and can_score_net)
                )
                if one_tba_data["leave_success_rate"]
                else has_compatible_auto
                * (
                    mode_score_success_rate * score_values[mode_score]
                    + 2.5 * int(can_intake_reef and can_score_net)
                )
            )
        else:
            auto = (
                2 * one_tba_data["leave_success_rate"]
                + has_compatible_auto * (2.5 * int(can_intake_reef and can_score_net))
                if one_tba_data["leave_success_rate"]
                else has_compatible_auto * (2.5 * int(can_intake_reef and can_score_net))
            )
        endgame = max(
            12 * one_team_data["cage_percent_success_deep"] - 2,
            6 * one_team_data["cage_percent_success_shallow"],
            0,
        )

        return [auto + tele + endgame, [auto, tele, endgame]]

    def update_pickability(self, obj_team, tba_team, auto_paths, subj_team):
        """Creates updated pickability documents"""
        updates = []
        for team in self.server.TEAM_LIST:
            update = {"team_number": team}

            team_data = dict()
            if obj := list(filter(lambda t: t["team_number"] == team, obj_team)):
                team_data.update(obj[0])
            else:
                log.error(f"No `obj_team` data found for team {team}.")
                updates.append(update)
            if sbj := list(filter(lambda t: t["team_number"] == team, subj_team)):
                team_data.update(sbj[0])
            else:
                log.error(f"No `subj_team` data found for team {team}.")
                updates.append(update)

            for calc_name in self.pickability_schema["calculations"]:
                value = self.calculate_pickability(calc_name, team_data)
                update[calc_name] = value

            update["offensive_second_pickability"] = self.calc_offensive_2nd_pickability(
                team, obj_team, tba_team, auto_paths
            )[0]

            updates.append(update)

        return utils.unique_ld(updates)

    def run(self) -> None:
        """Detects when and for which teams to calculate pickabilty"""
        timer = Timer()

        obj_team = self.server.local_db.find("obj_team")
        tba_team = self.server.local_db.find("tba_team")
        auto_paths = self.server.local_db.find("auto_paths")
        subj_team = self.server.local_db.find("subj_team")

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

        self.server.local_db.delete_data("pickability")
        self.server.local_db.insert_documents(
            "pickability", self.update_pickability(obj_team, tba_team, auto_paths, subj_team)
        )

        override.apply_override("pickability")

        timer.end_timer(__file__)
