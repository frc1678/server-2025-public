import tba_communicator
from calculations.predicted_aim import PredictedAimCalc
from calculations.base_calculations import BaseCalculations
from timer import Timer
import utils
import override


class PredictedElims(BaseCalculations):
    FIRST_ROUND_STRUCTURE = {
        "1": (1, 8),
        "2": (4, 5),
        "3": (2, 7),
        "4": (3, 6),
    }
    PLAYOFF_STRUCTURE = {
        "5": (-1, -2),
        "6": (-3, -4),
        "7": (1, 2),
        "8": (3, 4),
        "9": (-7, 6),
        "10": (-8, 5),
        "11": (7, 8),
        "12": (9, 10),
        "13": (-11, 12),
        "14": (11, 13),
        "15": (11, 13),
        "16": (11, 13),
    }

    def __init__(self, server):
        super().__init__(server)
        self.watched_collections = ["obj_team"]
        self.predicted_aim_calc = PredictedAimCalc(self.server)
        self.tba_data = self.predicted_aim_calc.get_playoffs_alliances()
        self.obj_team = self.server.local_db.find("obj_team")
        self.tba_team = self.server.local_db.find("tba_team")
        self.schema = utils.read_schema("schema/calc_predicted_elims_schema.yml")

    def predict_first_round(self, tba_match_data):
        matches = {}
        predicted_outcome = {}
        for match, teams in self.FIRST_ROUND_STRUCTURE.items():
            for alliance in self.tba_data:
                if alliance["alliance_num"] == teams[0]:
                    red_alliance = alliance
                elif alliance["alliance_num"] == teams[1]:
                    blue_alliance = alliance
            matches[match] = {"R": red_alliance["picks"], "B": blue_alliance["picks"]}
        for match_num, alliances in matches.items():
            predicted_outcome[match_num] = self.predict_match(
                alliances, int(match_num), tba_match_data
            )
            predicted_outcome[match_num]["alliances"] = alliances
        return predicted_outcome

    def predict_match(self, alliances, match_number, tba_match_data):
        result = {"R": {}, "B": {}}
        for color in ["R", "B"]:
            predicted_values = self.predicted_aim_calc.calc_predicted_values(
                self.obj_team, self.tba_team, alliances[color]
            )
            for action, value in predicted_values.items():
                result[color][f"_{action}"] = value
            result[color]["predicted_score"] = self.predicted_aim_calc.predict_value(
                predicted_values
            )
        red_win_chance = self.predicted_aim_calc.calc_win_chance(self.obj_team, alliances)
        result["red_win_chance"] = red_win_chance
        for match in tba_match_data:
            if match["comp_level"] != "qm" and match["score_breakdown"] is not None:
                if match["comp_level"] == "sf":
                    if int(match["key"].split("_")[1].split("m")[0][2:]) != match_number:
                        continue
                elif match["comp_level"] == "f":
                    if int(match["key"].split("_")[1].split("m")[0][1:]) + 13 != match_number:
                        continue
                result["red_win_chance"] = 1 if match["winning_alliance"] == "red" else 0
                for color in ["red", "blue"]:
                    for calc, schema in self.schema["calculations"].items():
                        result[color[0].upper()][calc] = match["score_breakdown"][color][
                            schema["tba_point"]
                        ]
        return result

    def predict_future_rounds(self, played_matches, tba_match_data):
        match_outcomes = played_matches
        for i in range(1, 16):
            predicted_alliances = {}
            if str(i) in match_outcomes.keys():
                continue
            red_match = self.PLAYOFF_STRUCTURE[str(i)][0]
            match_alliances = match_outcomes[str(abs(red_match))]["alliances"]
            if red_match < 0:
                predicted_alliances["R"] = (
                    match_alliances["R"]
                    if match_outcomes[str(abs(red_match))]["red_win_chance"] < 0.5
                    else match_alliances["B"]
                )
            else:
                predicted_alliances["R"] = (
                    match_alliances["R"]
                    if match_outcomes[str(abs(red_match))]["red_win_chance"] > 0.5
                    else match_alliances["B"]
                )
            blue_match = self.PLAYOFF_STRUCTURE[str(i)][1]
            match_alliances = match_outcomes[str(abs(blue_match))]["alliances"]
            if blue_match < 0:
                predicted_alliances["B"] = (
                    match_alliances["R"]
                    if match_outcomes[str(abs(blue_match))]["red_win_chance"] < 0.5
                    else match_alliances["B"]
                )
            else:
                predicted_alliances["B"] = (
                    match_alliances["R"]
                    if match_outcomes[str(abs(blue_match))]["red_win_chance"] > 0.5
                    else match_alliances["B"]
                )
            match_outcomes[str(i)] = self.predict_match(predicted_alliances, i, tba_match_data)
            match_outcomes[str(i)]["alliances"] = predicted_alliances
        if round(match_outcomes["14"]["red_win_chance"]) != round(
            match_outcomes["15"]["red_win_chance"]
        ):
            match_outcomes["16"] = self.predict_match(
                match_outcomes["15"]["alliances"], 16, tba_match_data
            )
        return match_outcomes

    def run(self):
        timer = Timer()
        tba_match_data = tba_communicator.tba_request(f"event/{self.server.TBA_EVENT_KEY}/matches")

        predicted_matches = self.predict_first_round(tba_match_data)
        predicted_matches.update(self.predict_future_rounds(predicted_matches, tba_match_data))

        formatted = []
        for match, predictions in predicted_matches.items():
            predictions["match_number"] = int(match)
            formatted.append(predictions)

        self.server.local_db.delete_data("predicted_elims")
        self.server.local_db.insert_documents(
            "predicted_elims",
            formatted,
        )

        override.apply_override("predicted_elims")

        timer.end_timer(__file__)
