#!/usr/bin/env python3
import database
import utils
import logging
import json
import os
from utils import get_qr_identifiers

log = logging.getLogger(__name__)

SCHEMA = utils.read_schema("schema/collection_schema.yml")
db = database.BetterDatabase(utils.server_key(), False)
file_name = f"data/{utils.server_key()}_overrides.json"


def apply_override(collection):
    if os.path.exists(file_name):
        with open(file_name, "r") as file:
            data = json.load(file)
    else:
        return

    if collection not in data.keys():
        return

    count = 0
    for query in data[collection]:
        new_value = query.pop("new_value")
        datapoint = query.pop("datapoint")

        result = db.update_document(collection, {datapoint: new_value}, query, update_many=True)

        count += result.modified_count

    log.info(f"Overrode {count} documents in {collection=}")


if __name__ == "__main__":
    utils.confirm_comp()

    if utils.input("Would you like to override data or blocklist QRs? O/B: ").upper() == "O":
        if not os.path.exists(file_name):
            with open(file_name, "w") as f:
                json.dump({}, f)
        try:
            with open(file_name, "r") as f:
                data = json.load(f)
        except Exception as err:
            log.error(f"Cannot load overrides: {err}")
            data = dict()

        print()
        collection_name = utils.input("Collection: ")

        if collection_name not in data:
            data[collection_name] = []

        new_entry = dict()
        collection_schema = SCHEMA["collections"][collection_name]["indexes"][0]
        for field in collection_schema["fields"]:
            new_entry[field] = utils.type_cast(
                a := utils.input(f"{field}: "), collection_schema["types"][field]
            )

        result = db.get_documents(collection_name, new_entry)

        datapoint = utils.input("Datapoint: ")
        print(f"Current value for {datapoint}: {result[0][datapoint]}")

        new_value = utils.input("Enter new value: ")
        new_value = type(result[0][datapoint])(new_value)

        new_entry["datapoint"] = datapoint
        new_entry["new_value"] = new_value
        new_entry[datapoint] = result[0][datapoint]

        if not new_entry in data[collection_name]:
            data[collection_name].append(new_entry)

        with open(file_name, "w") as f:
            json.dump(data, f, indent=4)
    else:
        key = {
            "match_number": int(utils.input("Match number: ")),
            "scout_name": None,
            "scout_id": None,
        }
        name_or_id = utils.input("Scout ID/name: ")
        if any([num in name_or_id for num in list(map(lambda n: str(n), range(1, 10)))]):
            key["scout_id"] = name_or_id
        else:
            key["scout_name"] = name_or_id.upper()
        for qr in db.get_documents("raw_qr", include_obj_id=True):
            identifiers = get_qr_identifiers(qr["data"])
            if key["match_number"] == identifiers["match_number"] and (
                (key["scout_name"] == identifiers["scout_name"] and key["scout_name"])
                or (key["scout_id"] == identifiers["scout_id"] and key["scout_id"])
            ):
                utils.confirm_comp(f"Found a matching QR with identifiers {identifiers}")
                db.update_document("raw_qr", {"blocklisted": True}, {"_id": qr["_id"]}, True)
                break
        else:
            log.error("No matching QRs found.")
