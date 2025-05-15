"Print the current Server settings to the terminal."
# TODO: add latest TBA match, TBA matches without data
# TODO: add database condition (duplicates, storage, on school wifi, etc)

import utils
import database
import tba_communicator as tba
import json
import os
import doozernet_communicator

with open("data/competition.txt") as f:
    event_key = f.read()

try:
    with open(f"data/{utils.server_key()}_valid_ss_profiles.json") as f:
        valid_ss_profiles = f.read()
except:
    valid_ss_profiles = None

try:
    with open(f"data/{utils.TBA_EVENT_KEY}_team_list.json") as f:
        if json.load(f):
            has_team_list = True
        else:
            has_team_list = False
except:
    has_team_list = False

try:
    with open(f"data/{utils.TBA_EVENT_KEY}_match_schedule.json") as f:
        if json.load(f):
            has_match_schedule = True
        else:
            has_match_schedule = False
except:
    has_match_schedule = False

utils.print(
    "If you want to connect to the cloud DB, make sure you're not connected to DJUSD Wi-Fi!",
    "green",
)

utils.print(
    f"""
Database name: {utils.server_key()}
Has internet: {utils.has_internet()}

Has team list: {has_team_list}
Has match schedule: {has_match_schedule}

Valid Stand Strat profiles: {valid_ss_profiles}
Has Matt's ratings: {os.path.exists(f"data/{utils.server_key()}_robustness_ratings.csv")}
Has DoozerNet model: {True if doozernet_communicator.check_model_availability() else False}
Has scout names: {os.path.exists(f"data/{utils.server_key()}_scout_names.json")}
Has overrides file: {os.path.exists(f"data/{utils.server_key()}_overrides.json")}
"""
)
