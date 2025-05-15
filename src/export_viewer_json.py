#!/usr/bin/env python3

"Creates a JSON export that can be used by Viewer in case Grosbeak is down"

import json
import utils
from export_csvs import BaseExport
import datetime
import logging
from typing import Union

log = logging.getLogger("export_viewer_json")

read_cloud = True

collections = ["obj_team", "obj_tim", "predicted_aim", "predicted_alliances", "auto_paths"]

# Converts our collection names into Front-end's weird naming system
name_map = {
    "obj_team": "team",
    "obj_tim": "tim",
    "predicted_aim": "aim",
    "predicted_alliances": "alliance",
    "auto_paths": "auto_paths",
}
# Variables to group by for each collection
key_map = {
    "obj_team": "team_number",
    "obj_tim": ["match_number", "team_number"],
    "predicted_aim": ["match_number", "alliance_color_is_red"],
    "predicted_alliances": "alliance_num",
    "auto_paths": ["team_number", "path_number"],
}
# Special conversion for predicted_aim's `alliance_color_is_red` variable
color_map = {True: "red", False: "blue"}


def key_by(data: list[dict], key: Union[str, list[str]]) -> dict:
    """Groups data from the database by one or more variables

    `data`: data pulled from MongoDB

    `key`: one or more keys used to group data under. If a list of keys is specified, creates nested dictionaries, each with its own grouping.

    Returns a (potentially multi-layer) dict with the same data grouped by the specified variables.
    """
    # Feasibility check
    if type(data) == dict:
        data = [data]
    if key == "" or not key:
        return dict()

    final_data = dict()
    first_key = key if type(key) == str else key[0]

    # Group by first key ===================================
    # Find unique keys and group all documents together
    for item in data:
        if not item:
            continue
        key_val = item[first_key]
        del item[first_key]

        if key_val not in final_data:
            final_data[key_val] = []
        final_data[key_val].append(item)
    # Make sure the data isn't formatted as `[data]`
    for group, items in final_data.items():
        if len(items) == 1:
            final_data[group] = items[0]

    # Run recursively on all keys ==========================
    if type(key) == list:
        for next_key in key[1:]:
            for key1, item in final_data.items():
                final_data[key1] = key_by(item, next_key)

    return final_data


if __name__ == "__main__":
    # Prompt user
    utils.confirm_comp(f"You are working with competition {utils.server_key()}, and {read_cloud=}.")

    exporter = BaseExport()

    # Final viewer export
    viewer_export = {name_map[collection]: dict() for collection in collections}

    # Iterate through all collections ==========================
    for collection in collections:
        log.info(f"Exporting {collection} data...")
        data = exporter.get_data([collection], read_cloud)[collection]

        for item in data:
            del item["_id"]

        # HARD-CODED SECTION -----------------------------------
        # Viewer uses strange data inputs so we convert the odd variables here

        # Hard-coded conversion for predicted_aim because Viewer needs `"red"` or `"blue"` and we give `True` or `False`
        if collection == "predicted_aim":
            for i in range(len(data)):
                data[i]["alliance_color_is_red"] = color_map[data[i]["alliance_color_is_red"]]
        # Viewer needs all lists to be in str form
        for i in range(0, len(data)):
            for datapoint, value in data[i].items():
                if type(value) is list:
                    data[i][datapoint] = str(value)

        # Upload data
        viewer_export[name_map[collection]] = key_by(data, key_map[collection])

    # Write final data to JSON file ============================
    filepath = f"data/{utils.server_key()}_viewer_export_{datetime.datetime.today().strftime(r'%Y-%m-%d_%H-%M')}.json"
    with open(filepath, "w") as f:
        f.write(json.dumps(viewer_export, indent=4))

    log.info(f"Wrote viewer export to {filepath}")
