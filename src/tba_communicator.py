#!/usr/bin/env python3

"""Sends web requests to The Blue Alliance (TBA) APIv3.

API documentation: https://www.thebluealliance.com/apidocs/v3.
"""

import requests
import utils
import logging
import json
from typing import Dict
import copy
import datetime
import httpx
import asyncio

log = logging.getLogger(__name__)

ALL_EVENT_TYPES = [
    "Preseason",
    "District",
    "Regional",
    "Championship Finals",
    "Championship Division",
    "Offseason",
    "District Championship",
    "District Championship Division",
]


def get_reef_score(reef: dict, mode: str, row: int = 0) -> int:
    """
    Mode is either 'auto' or 'tele'.
    rows should be an int representing the reef level. 0 is all of them, 1-4 is a reef level
    """
    if mode == "auto":
        weights = {"trough": 3, "botRow": 4, "midRow": 6, "topRow": 7}
    elif mode == "tele":
        weights = {"trough": 2, "botRow": 3, "midRow": 4, "topRow": 5}
    else:
        return None

    all_rows = ["trough", "botRow", "midRow", "topRow"]
    if row == 0:
        levels = all_rows
    elif row == 1:
        return reef["trough"] * weights["trough"]
    else:
        levels = [all_rows[row - 1]]

    return sum(
        [sum([int(scored) for scored in reef[level].values()]) * weights[level] for level in levels]
    )


def tba_request(api_url, modify=True):
    """Sends a single web request to the TBA API v3.

    `api_url`: suffix of the API request URL (the part after '/api/v3/').

    `modify`: if True, we calculate certain more useful datapoints before returning it

    Returns the data received by the TBA API.
    """
    full_url = f"https://www.thebluealliance.com/api/v3/{api_url}"
    request_headers = {"X-TBA-Auth-Key": get_api_key()}

    try:
        request = requests.get(full_url, headers=request_headers)
    except requests.exceptions.ConnectionError:
        log.error("No internet connection.")
        return None
    response = request.json()

    modified_response = []
    if "matches" in api_url and modify:
        for match in response:
            if not match["score_breakdown"]:
                continue

            updated_match = copy.deepcopy(match)
            updated_breakdown = updated_match["score_breakdown"]

            for color in ["red", "blue"]:
                color_breakdown = match["score_breakdown"][color]

                color_breakdown["auto_L1_count"] = color_breakdown["autoReef"]["trough"]
                color_breakdown["auto_L2_count"] = color_breakdown["autoReef"]["tba_botRowCount"]
                color_breakdown["auto_L3_count"] = color_breakdown["autoReef"]["tba_midRowCount"]
                color_breakdown["auto_L4_count"] = color_breakdown["autoReef"]["tba_topRowCount"]

                color_breakdown["tele_L1_count"] = (
                    color_breakdown["teleopReef"]["trough"] - color_breakdown["auto_L1_count"]
                )
                color_breakdown["tele_L2_count"] = (
                    color_breakdown["teleopReef"]["tba_botRowCount"]
                    - color_breakdown["auto_L2_count"]
                )
                color_breakdown["tele_L3_count"] = (
                    color_breakdown["teleopReef"]["tba_midRowCount"]
                    - color_breakdown["auto_L3_count"]
                )
                color_breakdown["tele_L4_count"] = (
                    color_breakdown["teleopReef"]["tba_topRowCount"]
                    - color_breakdown["auto_L4_count"]
                )

                # TODO add auto and tele net & processor counts
                color_breakdown["net_algae_count_no_hp"] = (
                    color_breakdown["netAlgaeCount"]
                    - match["score_breakdown"]["red" if color == "blue" else "blue"][
                        "wallAlgaeCount"
                    ]
                )
                color_breakdown["total_points_no_hp_foul"] = (
                    match["alliances"][color]["score"]
                    - 4
                    * match["score_breakdown"]["red" if color == "blue" else "blue"][
                        "wallAlgaeCount"
                    ]
                    - color_breakdown["foulPoints"]
                )
                color_breakdown["total_points_no_foul"] = (
                    match["alliances"][color]["score"]
                    - match["score_breakdown"][color]["foulPoints"]
                )

                updated_breakdown[color] = color_breakdown

            updated_match["score_breakdown"] = updated_breakdown
            modified_response.append(updated_match)

        return modified_response
    return response


def get_api_key() -> str:
    with open(utils.create_file_path("data/api_keys/tba_key.txt")) as file:
        api_key = file.read().rstrip("\n")
    return api_key


def create_match_schedule(event_key: str) -> Dict[str, Dict]:
    "Creates a match schedule JSON using the TBA API."
    matches = tba_request(f"event/{event_key}/matches/simple", modify=False)

    if not matches:
        log.error(f"Cannot create match schedule for {event_key}; no TBA data.")
        return dict()

    # Filter out elimination matches
    matches = [match for match in matches if match["comp_level"] == "qm"]
    match_schedule_dict = dict()

    for match in matches:
        # example: '2019carv_qm118'
        match_key = match["key"].split("_qm")[1]
        team_dicts = []
        for alliance in ["blue", "red"]:
            teams = match["alliances"][alliance]["team_keys"]
            teams = [{"number": str(team[3:]), "color": alliance} for team in teams]
            team_dicts.extend(teams)
        match_schedule_dict[match_key] = {"teams": team_dicts}

    with open(f"data/{event_key}_match_schedule.json", "w") as json_file:
        json.dump(match_schedule_dict, json_file)

    log.info(f"Created match schedule for competition {event_key}")


def get_teams_in_match(match: dict) -> dict[str, list]:
    "Returns all teams playing in a TBA match."
    return {
        "red": list(map(lambda key: key[3:], match["alliances"]["red"]["team_keys"])),
        "blue": list(
            map(
                lambda key: key[3:],
                match["alliances"]["blue"]["team_keys"],
            )
        ),
    }


def create_team_list(event_key: str):
    "Creates a team list JSON at `TEAM_LIST_LOCAL_PATH` using the TBA API."
    team_numbers = sorted(
        list(
            set(
                [
                    str(team["team_number"])
                    for team in tba_request(f"event/{event_key}/teams/simple")
                ]
            )
        )
    )
    with open(f"data/{event_key}_team_list.json", "w") as file:
        json.dump(team_numbers, file)

    log.info(f"Created team list for competition {event_key}")


def get_teams_from_matches(matches: list[dict]) -> list[str]:
    team_list = []

    for match in matches:
        teams_in_match = get_teams_in_match(match)
        team_list.extend(teams_in_match["red"] + teams_in_match["blue"])

    return list(set(team_list))


def get_events_played(
    year: str,
    excluded_types: list[str] = [
        "Preseason",
        "Offseason",
    ],
    date_window: list[str] = ["1000-01-01", "9999-12-31"],
) -> list[str]:
    "Date window is a half-open interval: [date1, date2)"
    date_window = [
        datetime.datetime.strptime(date_window[0], r"%Y-%m-%d"),
        datetime.datetime.strptime(date_window[1], r"%Y-%m-%d"),
    ]
    raw = tba_request(f"events/{year}")
    played = []

    for event in raw:
        event_date = datetime.datetime.strptime(event["end_date"], r"%Y-%m-%d")
        if (
            event["event_type_string"] not in excluded_types
            and datetime.datetime.today() > event_date
            and date_window[0] <= event_date < date_window[1]
        ):
            played.append(event["key"])

    return played


def get_teams_in_event(event_key: str) -> list[str]:
    return list(map(lambda t: t["key"][3:], tba_request(f"event/{event_key}/teams")))


async def get_team_events(team, year):
    async with httpx.AsyncClient(headers={"X-TBA-Auth-Key": get_api_key()}, timeout=20) as client:
        resp = await client.get(
            f"https://www.thebluealliance.com/api/v3/team/frc{team}/events/{year}/simple"
        )
        resp.raise_for_status()
        return list(map(lambda t: t["key"], resp.json()))


async def get_event_keys_async(teams: list[str], year: int) -> list[str]:
    "Given a list of teams, gets all events where one or more of those teams played"
    log.info("Extracting event keys...")

    data = []
    for team in teams:
        data.append(get_team_events(team, year))
    data = await asyncio.gather(*data)

    flattened = []
    for team_events in data:
        flattened.extend(team_events)

    return list(set(flattened))


def get_event_keys(teams: list[str], year: int) -> list[str]:
    log.info("Extracting event keys...")
    all_keys = []

    count = 1
    total = len(teams)

    for team in teams:
        utils.progress_bar(count, total)

        all_keys.extend(tba_request(f"/team/frc{team}/events/{year}/simple"))

        count += 1

    return list(set(map(lambda t: t["key"], all_keys)))


def get_team_latest_event(team: str, year: int) -> str:
    events = tba_request(f"team/frc{team}/events/simple")
    latest_date = datetime.datetime.strptime("1000-01-01", r"%Y-%m-%d")

    for event in events:
        if (
            d := datetime.datetime.strptime(event["end_date"], r"%Y-%m-%d")
        ) > latest_date and event["key"] not in [
            "2025arc",
            "2025cur",
            "2025gal",
            "2025hop",
            "2025dal",
            "2025joh",
            "2025mil",
            "2025new",
            "2025cmptx",
        ]:
            latest_date = d
    for event in events:
        if datetime.datetime.strptime(event["end_date"], r"%Y-%m-%d") == latest_date:
            return event["key"]
