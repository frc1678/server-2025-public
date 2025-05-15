import database
import json
import utils
import os
import logging

log = logging.getLogger("find_defense_matches")


def find_defense_matches():
    db = database.Database()

    ss_tim = db.find("ss_tim")
    obj_tim = db.find("obj_tim")
    matches = {}
    output = []

    for tim in ss_tim:
        if tim["match_number"] not in matches.keys():
            matches[tim["match_number"]] = []
        matches[tim["match_number"]].append(tim)
    for match_number, match in matches.items():
        output.append(
            {
                "match_number": match_number,
                "teams_played_defense": [],
                "teams_played_against_defense": [],
                "defense_ratings": {},
                "defense_timestamps": {},
            }
        )
        for tim in match:
            if tim["played_defense"]:
                output[-1]["teams_played_defense"].append(tim["team_number"])
                output[-1]["defense_ratings"][tim["team_number"]] = tim["defense_rating"]
                output[-1]["defense_timestamps"][tim["team_number"]] = tim["defense_timestamp"]
            elif tim["played_against_defense"]:
                output[-1]["teams_played_against_defense"].append(tim["team_number"])
        if output[-1]["teams_played_defense"] == []:
            output.pop(-1)
    return output


if __name__ == "__main__":
    export_file_path = f"data/{'test' if os.environ.get('SCOUTING_SERVER_ENV') != 'production' else ''}{utils.TBA_EVENT_KEY}_defense_matches.json"

    json.dump(find_defense_matches(), open(export_file_path, "w"), indent=4)
    log.info(f"Successfully found and exported defense matches to {export_file_path}")
