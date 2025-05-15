from calculations.base_calculations import BaseCalculations
import logging
import database
import numpy as np
import math
from calculations.decompressor import get_qr_identifiers
import tba_communicator as tba
import utils
import json
import os
from timer import Timer

from typing import Union, List, Dict

log = logging.getLogger("data_validation")


class AnomalyDetection(BaseCalculations):
    def __init__(self, server):
        super().__init__(server)
        self.watched_collections = database.VALID_COLLECTIONS

    def find_outliers(self, data, threshold=7):
        data = np.array(data)

        mean = np.mean(data)
        std_dev = np.std(data)

        # Define extreme outlier bounds
        low_cutoff = math.floor(mean - 3 * std_dev)
        high_cutoff = math.ceil(mean + threshold * std_dev)

        return low_cutoff, high_cutoff

    def run(self):
        self.server.local_db.delete_data("anomalous_data")
        collections = ["auto_pim", "obj_tim", "obj_team"]

        for c in collections:
            collection = self.server.local_db.find(c)

            if not collection:
                continue

            for data_key in collection[0].keys():
                data = [
                    tim[data_key]
                    for tim in collection
                    if isinstance(tim.get(data_key), (float, int))
                    and not isinstance(tim[data_key], bool)
                ]

                if data:
                    low_thresh, high_thresh = self.find_outliers(data)

                    for entry in collection:
                        team = entry.get("team_number")
                        color = entry.get("alliance_color_is_red")
                        match = entry.get("match_number")

                        if data_key in entry and (
                            entry[data_key] < low_thresh or entry[data_key] > high_thresh
                        ):
                            data_to_add = {
                                "collection": c,
                                "team_number": team,
                                "match_number": match,
                                "alliance_color_is_red": color,
                                "low": low_thresh,
                                "high": high_thresh,
                                data_key: entry[data_key],
                            }
                            self.server.local_db.insert_documents("anomalous_data", data_to_add)


# TODO Add functionality to write flagged matches from DataAccuracy and ScoutDisagreements to data_status.txt
class DataStatus(BaseCalculations):
    def __init__(self, server):
        super().__init__(server)

        self.SCOUT_IDS = list(map(lambda num: str(num), range(1, 19)))
        try:
            with open(f"data/{utils.server_key()}_scout_names.json") as f:
                self.SCOUT_NAMES = json.load(f)
        except:
            log.error("No scout names JSON file, manually calculating")

            self.SCOUT_NAMES = list(
                set(
                    map(
                        lambda t: t["scout_name"],
                        self.server.local_db.find("unconsolidated_totals"),
                    )
                )
            )

    def calc_match_summaries(self):
        match_summaries = []

        tba_data = tba.tba_request(f"event/{utils.TBA_EVENT_KEY}/matches")
        obj_tim_data = self.server.local_db.find("obj_tim")
        qr_data = list(
            map(lambda doc: get_qr_identifiers(doc["data"]), self.server.local_db.find("raw_qr"))
        )

        ids_to_scouts = {id: [] for id in self.SCOUT_IDS}
        for qr in qr_data:
            if qr["is_obj"] and qr["match_number"] and qr["scout_id"] and qr["scout_name"]:
                if qr["scout_id"] not in ids_to_scouts.keys():
                    ids_to_scouts[qr["scout_id"]] = []
                ids_to_scouts[qr["scout_id"]].append(
                    {"match_number": qr["match_number"], "scout_name": qr["scout_name"]}
                )

        for tba_match in sorted(
            list(filter(lambda doc: doc["comp_level"] == "qm", tba_data)),
            key=lambda doc: doc["match_number"],
        ):
            match_summary = {
                "match_number": tba_match["match_number"],
                "missing_qrs": [],
                "played": False,
            }
            scout_ids = []
            teams = []

            obj_tim_match = list(
                filter(lambda doc: doc["match_number"] == tba_match["match_number"], obj_tim_data)
            )
            if not obj_tim_match:
                match_summaries.append(match_summary)
                continue
            else:
                match_summary["played"] = True
            qr_match = list(
                filter(lambda doc: doc["match_number"] == tba_match["match_number"], qr_data)
            )

            for qr in qr_match:
                if qr["scout_id"]:
                    scout_ids.append(qr["scout_id"])
            for team in obj_tim_match:
                teams.append(team["team_number"])

            match_summary["num_obj_qrs"] = len(list(filter(lambda qr: qr["is_obj"], qr_match)))
            match_summary["num_subj_qrs"] = len(list(filter(lambda qr: not qr["is_obj"], qr_match)))

            match_summary["duplicate_scout_ids"] = (
                list(map(lambda id: int(id), utils.modes(scout_ids)))
                if len(utils.modes(scout_ids)) != len(scout_ids)
                else []
            )
            match_summary["missing_teams"] = list(
                set(
                    tba.get_teams_in_match(tba_match)["red"]
                    + tba.get_teams_in_match(tba_match)["blue"]
                ).difference(set(teams))
            )

            if not (match_summary["num_obj_qrs"] == 18 and match_summary["num_subj_qrs"] == 2):
                missing_ids = list(set(self.SCOUT_IDS).difference(set(scout_ids)))
                for id in missing_ids:
                    sn = sorted(ids_to_scouts[id], key=lambda doc: doc["match_number"])
                    match_summary["missing_qrs"].append(
                        {
                            "scout_id": id,
                            "scout_name": sn[-1]["scout_name"] if sn else None,
                        }
                    )

                if not os.path.exists(f"data/{utils.server_key()}_scout_scan_history.json"):
                    with open(f"data/{utils.server_key()}_scout_scan_history.json", "x") as f:
                        f.write(json.dumps([]))
                with open(f"data/{utils.server_key()}_scout_scan_history.json", "r") as f:
                    history = json.load(f)
                for missing_qr in match_summary["missing_qrs"]:
                    if (
                        new_missing := ({"match_number": tba_match["match_number"]} | missing_qr)
                    ) not in history:
                        history.append(new_missing)
                with open(f"data/{utils.server_key()}_scout_scan_history.json", "w") as f:
                    f.write(json.dumps(history, indent=4))

            match_summary["num_obj_tim"] = len(obj_tim_match)

            match_summary["flagged"] = not (
                match_summary["num_obj_tim"] == 6
                and not match_summary["duplicate_scout_ids"]
                and not match_summary["missing_qrs"]
                and match_summary["num_subj_qrs"] == 2
            )
            match_summaries.append(match_summary)

        with open(f"data/{utils.server_key()}_match_summaries.json", "w") as f:
            f.write(json.dumps(match_summaries, indent=4))
        return match_summaries

    def write_summaries(self, match_summaries):
        out = ""

        for match in match_summaries:
            if not match["played"]:
                out += f"No data: MATCH {match['match_number']}\n"
                continue
            elif not match["flagged"]:
                out += f"MATCH {match['match_number']}\n"
                continue
            out += f"\nMATCH {match['match_number']}\n - Obj tim: {match['num_obj_tim']}\n - Obj QRs: {match['num_obj_qrs']}\n - Subj QRs: {match['num_subj_qrs']}\n - Duplicate IDs: {str(match['duplicate_scout_ids'])[1:-1]}\n - Missing QRs:\n"
            for missing in match["missing_qrs"]:
                out += f"    - ID {missing['scout_id']} ({missing['scout_name']})\n"
            out += "\n"

        out += "_______________________________________\nSCOUT SCAN HISTORY\n"
        scout_counts = self.count_history()
        for scout, count in sorted(scout_counts.items(), key=lambda s: s[1], reverse=True):
            out += f" - {scout}: {count}\n"

        with open("data/data_status.txt", "w") as f:
            f.write(out)

    def count_history(self) -> dict[str, int]:
        counts = dict()

        if not os.path.exists(p := f"data/{utils.server_key()}_scout_scan_history.json"):
            with open(p, "w") as f:
                f.write(json.dumps([]))
            history = []
        else:
            with open(f"data/{utils.server_key()}_scout_scan_history.json") as f:
                history = json.load(f)

        for scout in self.SCOUT_NAMES:
            counts[scout] = len(
                list(filter(lambda doc: doc["scout_name"] == scout.upper(), history))
            )

        return counts

    def run(self):
        timer = Timer()
        self.write_summaries(self.calc_match_summaries())

        timer.end_timer("data_validation.DataStatus")


class DataAccuracy(BaseCalculations):
    SCHEMA = utils.read_schema("schema/data_accuracy.yml")

    def __init__(self, server):
        super().__init__(server)

    def calc_data_accuracy(self, obj_tims: List[dict], tba_matches: List[dict]) -> List[dict]:
        documents = []

        for match_tba in list(filter(lambda t: t["comp_level"] == "qm", tba_matches)):
            teams = tba.get_teams_in_match(match_tba)

            for color in ["red", "blue"]:
                document = {
                    "match_number": match_tba["match_number"],
                    "alliance_color": color,
                    "team_numbers": teams[color],
                }

                alliance_tims = list(
                    filter(
                        lambda t: t["team_number"] in teams[color]
                        and t["match_number"] == match_tba["match_number"],
                        obj_tims,
                    )
                )
                if not alliance_tims:
                    continue

                if len(alliance_tims) != 3:
                    log.error(
                        f"Missing {6 - len(alliance_tims)} obj_tim documents in match {match_tba['match_number']}"
                    )
                    continue

                for calculation, info in self.SCHEMA["--diffs"].items():
                    scouted_value = 0

                    for tim in alliance_tims:
                        scouted_value += utils.calc_weighted_sum(tim, info["tim_weights"])

                    document[calculation] = abs(
                        scouted_value
                        - utils.calc_weighted_sum(
                            match_tba["score_breakdown"][color], info["tba_weights"]
                        )
                    )

                documents.append(document)

        return documents

    def run(self):
        timer = Timer()

        updates = self.calc_data_accuracy(
            self.server.local_db.find("obj_tim"),
            tba.tba_request(f"event/{utils.TBA_EVENT_KEY}/matches"),
        )

        self.server.local_db.delete_data("data_accuracy")
        self.server.local_db.insert_documents("data_accuracy", updates)

        timer.end_timer("data_validation.DataAccuracy")


class ScoutDisagreements(BaseCalculations):
    def __init__(self, server):
        super().__init__(server)
        self.SCHEMA = utils.read_schema("schema/scout_disagreements.yml")["--datapoints"]

    def calc_disagreements(self, sims: List[Dict], tba_matches: List[Dict]) -> List[Dict]:
        result = []

        for match_tba in list(filter(lambda t: t["comp_level"] == "qm", tba_matches)):
            teams = tba.get_teams_in_match(match_tba)

            for color in ["red", "blue"]:
                for team in teams[color]:
                    team_doc = {
                        "match_number": match_tba["match_number"],
                        "alliance_color": color,
                        "team_number": team,
                    }
                    team_sims = list(
                        filter(
                            lambda s: s["match_number"] == match_tba["match_number"]
                            and s["team_number"] == team,
                            sims,
                        )
                    )
                    if not team_sims:
                        continue

                    for new, old in self.SCHEMA.items():
                        reported_vals = list(map(lambda s: s[old], team_sims))

                        try:
                            team_doc[new] = max(reported_vals) - min(reported_vals)
                        except Exception as err:
                            log.critical(
                                f"Unable to calculate datapoint '{new}' for team {team} in match {match_tba['match_number']}: {err}"
                            )
                            team_doc[new] = None

                    result.append(team_doc)

        return result

    def run(self):
        timer = Timer()

        self.server.local_db.delete_data("scout_disagreements")
        self.server.local_db.insert_documents(
            "scout_disagreements",
            self.calc_disagreements(
                self.server.local_db.find("unconsolidated_totals"),
                tba.tba_request(f"event/{self.server.TBA_EVENT_KEY}/matches"),
            ),
        )

        timer.end_timer("data_validation.ScoutDisagreements")


class DataFlagging(BaseCalculations):
    def __init__(self, server):
        super().__init__(server)
        self.SCHEMA = utils.read_schema("schema/data_flagging.yml")

    def parse_limits(self, datapoint: Union[int, bool], limits: List[str]) -> bool:
        "Returns True if `datapoint` is within the limit of `limits`, otherwise False"
        if datapoint is None:
            log.warning(f"Datapoint is None (limits of {limits})")
            return False

        for limit in limits:
            operator = limit.split()[0]
            bound = int(limit.split()[1])

            if operator == "=":
                if datapoint != bound:
                    return False
            elif operator == ">":
                if datapoint <= bound:
                    return False
            elif operator == ">=":
                if datapoint < bound:
                    return False
            elif operator == "<":
                if datapoint >= bound:
                    return False
            elif operator == "<=":
                if datapoint > bound:
                    return False
            elif operator == "!=":
                if datapoint == bound:
                    return False
        return True

    def flag_data(self, data_to_flag: Dict[str, List[Dict]], tba_matches: List[Dict]) -> List[Dict]:
        result = []

        for match_tba in list(filter(lambda t: t["comp_level"] == "qm", tba_matches)):
            match_doc = {"match_number": match_tba["match_number"], "flagged": False, "flags": []}

            match_disagreements = list(
                filter(
                    lambda t: t["match_number"] == match_tba["match_number"],
                    data_to_flag["scout_disagreements"],
                )
            )
            match_accuracy = list(
                filter(
                    lambda t: t["match_number"] == match_tba["match_number"],
                    data_to_flag["data_accuracy"],
                )
            )
            if not match_disagreements and not match_accuracy:
                continue

            for robot in match_disagreements:
                for datapoint, limits in self.SCHEMA["--scout_disagreements"].items():
                    if not self.parse_limits(robot[datapoint], limits):
                        match_doc["flags"].append(
                            {
                                "alliance_color": robot["alliance_color"],
                                "team_number": robot["team_number"],
                                "datapoint": datapoint,
                                "value": robot[datapoint],
                                "limits": limits,
                            }
                        )

            for alliance in match_accuracy:
                for datapoint, limits in self.SCHEMA["--data_accuracy"].items():
                    if not self.parse_limits(alliance[datapoint], limits):
                        match_doc["flags"].append(
                            {
                                "alliance_color": alliance["alliance_color"],
                                "team_number": None,
                                "datapoint": datapoint,
                                "value": alliance[datapoint],
                                "limits": limits,
                            }
                        )

            match_doc["flagged"] = len(match_doc["flags"]) > 0
            result.append(match_doc)

        return result

    def flag_in_obj_tims(self, flags: list[dict]) -> None:
        count = 0
        for flagged_match in flags:
            if not flagged_match["flagged"]:
                continue
            for flag in flagged_match["flags"]:
                if "diff" in flag["datapoint"]:
                    operation = self.server.local_db.update_document(
                        "obj_tim",
                        {"flagged": True},
                        {
                            "match_number": flagged_match["match_number"],
                            "alliance_color_is_red": flag["alliance_color"] == "red",
                        },
                        many=True,
                    )
                    count += operation.modified_count
                elif "range" in flag["datapoint"]:
                    operation = self.server.local_db.update_document(
                        "obj_tim",
                        {"flagged": True},
                        {
                            "match_number": flagged_match["match_number"],
                            "team_number": flag["team_number"],
                        },
                    )
                    count += operation.modified_count
                else:
                    log.error(f"Flag type not recognized: {flag}")
        log.info(f"Flagged {count} documents in obj_tim")

    def run(self):
        timer = Timer()

        flags = self.flag_data(
            {
                "data_accuracy": self.server.local_db.find("data_accuracy"),
                "scout_disagreements": self.server.local_db.find("scout_disagreements"),
            },
            tba.tba_request(f"event/{self.server.TBA_EVENT_KEY}/matches"),
        )

        self.server.local_db.delete_data("flagged_data")
        self.server.local_db.insert_documents(
            "flagged_data",
            list(filter(lambda t: t["flagged"], flags)),
        )
        self.flag_in_obj_tims(flags)

        timer.end_timer("data_validation.DataFlagging")
