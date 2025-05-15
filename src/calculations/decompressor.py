#!/usr/bin/env python3

"""Decompresses objective and subjective match collection QR codes."""

import enum
import os
import re

import yaml
import utils
from calculations import base_calculations
from calculations import qr_state
from calculations.qr_state import QRState
import logging
import database
from timer import Timer
import copy
from typing import List, Dict
import override

log = logging.getLogger(__name__)


class QRType(enum.Enum):
    """Enum that stores QR types."""

    OBJECTIVE = 0
    SUBJECTIVE = 1


def get_qr_identifiers(qr) -> dict:
    "Extracts the match number, scout name, team number, scout ID, and alliance team list from a raw QR. If datapoint does not exist (for example subjective QRs have no scout ID), the dict value is `None`."
    # TODO un-hardcode this to use the character codes in match_collection_qr_schema
    # Currently, it's using the positions of character codes withint the QR, which is fine until the orders are changed in schema
    data = {
        "is_obj": qr[0] == "+",
        "match_number": None,
        "scout_name": None,
        "team_number": None,
        "scout_id": None,
        "aim_team_list": None,
    }

    try:
        generic_data = qr.split("%")[0].split("$")
        data["match_number"] = int(generic_data[1][1:])
        data["scout_name"] = generic_data[4][1:]
        if data["is_obj"]:
            tim_data = qr.split("%")[1].split("$")
            data["team_number"] = tim_data[0][1:]
            data["scout_id"] = tim_data[1][1:]
        else:
            data["aim_team_list"] = list(
                map(lambda section: section.split("$")[0][1:], qr.split("%")[1].split("#"))
            )
    except Exception as err:
        log.error(f"Invalid QR '{qr}', cannot extract data: {err}")

    return data


class Decompressor(base_calculations.BaseCalculations):

    # Load latest match collection compression QR code schema
    SCHEMA = qr_state.SCHEMA
    OBJ_TIM_SCHEMA = utils.read_schema("schema/calc_obj_tim_schema.yml")
    OBJ_PIT_SCHEMA = utils.read_schema("schema/obj_pit_collection_schema.yml")
    SUBJ_PIT_SCHEMA = utils.read_schema("schema/subj_pit_collection_schema.yml")
    _GENERIC_DATA_FIELDS = QRState._get_data_fields("generic_data")
    OBJECTIVE_QR_FIELDS = _GENERIC_DATA_FIELDS.union(QRState._get_data_fields("objective_tim"))
    SUBJECTIVE_QR_FIELDS = _GENERIC_DATA_FIELDS.union(QRState._get_data_fields("subjective_aim"))
    TIMELINE_FIELDS = QRState.get_timeline_info()

    MISSING_TIM_IGNORE_FILE_PATH = utils.create_file_path("data/missing_tim_ignore.yml")

    def __init__(self, server):
        super().__init__(server)
        self.watched_collections = ["raw_qr"]
        self.super_compressed_actions = []

        for calc in self.SCHEMA["super_compressed"]:
            self.super_compressed_actions.append(self.SCHEMA["action_type"][calc])

    def convert_data_type(self, value, type_, name=None):
        """Convert from QR string representation to database data type."""
        # Enums are stored as int in the database
        if type_ == "int":
            return int(value)
        if type_ == "float":
            return float(value)
        if type_ == "bool":
            return utils.get_bool(value)
        if type_ == "str":
            return value  # Value is already a str
        if "Enum" in type_:
            return self.get_decompressed_name(value, name)
        raise ValueError(f"Type {type_} not recognized")

    def get_decompressed_name(self, compressed_name, section):
        """Returns decompressed variable name from schema.

        compressed_name: str - Compressed variable name within QR code
        section: str - Section of schema that name comes from.
        """
        for key, value in self.SCHEMA[section].items():
            if isinstance(value, list):
                if value[0] == compressed_name:
                    return key
            else:
                if value == compressed_name:
                    return key
        raise ValueError(f"Retrieving Variable Name {compressed_name} from {section} failed.")

    def get_decompressed_type(self, name, section):
        """Returns server-side data type from schema.

        name: str - Decompressed variable name within Schema
        section: str - Section of schema that name comes from.
        """
        # Type all items after the first item
        type_ = self.SCHEMA[section][name][1:]
        # Detect special case of data type being a list
        if len(type_) > 1:
            return type_  # Returns list of the type (list) and the type of data stored in the list
        return type_[0]  # Return the type of the value

    def decompress_data(self, data, section):
        """Decompress (split) data given the section of the QR it came from.

        This matches compressed data names to actual variable names. It treats embedded dictionaries as
        special cases, a parsing function needs to be written for each (e.g. timeline).
        """
        decompressed_data = {}
        # Iterate through data
        for data_field in data:
            if not data_field:
                continue

            compressed_name = data_field[0]  # Compressed name is always first character
            value = data_field[1:]  # Actual data value is everything after the first character
            # Get uncompressed name and the target data type
            uncompressed_name = self.get_decompressed_name(compressed_name, section)
            uncompressed_type = self.get_decompressed_type(uncompressed_name, section)
            # Detect special cases in typing (e.g. value is list)
            if isinstance(uncompressed_type, list):
                # If second data type is dictionary, it should be handled separately
                if "dict" in uncompressed_type:
                    # Decompress timeline
                    if uncompressed_name == "timeline":

                        # TODO ADD SAFETY HERE
                        if (
                            "start_position" in decompressed_data.keys()
                            and decompressed_data["start_position"] == "0"
                        ):
                            # No show team goes through 150 seconds of incap
                            typed_value = [
                                {"action_type": "to_teleop", "time": 150, "in_teleop": True},
                                {"action_type": "start_incap", "time": 150, "in_teleop": True},
                                {"action_type": "end_incap", "time": 0, "in_teleop": True},
                                {"action_type": "to_endgame", "time": 0, "in_teleop": True},
                            ]
                        elif "has_preload" in decompressed_data.keys():
                            typed_value = self.decompress_timeline(
                                value, decompressed_data["has_preload"]
                            )
                        else:
                            typed_value = self.decompress_timeline(value, True)
                    # Value is not one of the currently known dictionaries
                    else:
                        raise NotImplementedError(
                            f"Decompression of {uncompressed_name} as a dict not supported."
                        )
                # Decompress list of none-dicts
                elif uncompressed_type[1] in ["int", "float", "bool", "str"]:
                    if len(uncompressed_type) == 2:
                        # Default case, use _list_data_separator to seperate value into list items
                        split_values = value.split(self.SCHEMA["_list_data_separator"])
                    else:
                        # Use the specified length of each item to seperate
                        split_values = [
                            value[i : i + uncompressed_type[2]]
                            for i in range(0, len(value), uncompressed_type[2])
                        ]
                    # Convert string to appropriate data type
                    typed_value = [
                        self.convert_data_type(split_value, uncompressed_type[1])
                        for split_value in split_values
                    ]
            else:  # Normal data type
                typed_value = self.convert_data_type(value, uncompressed_type, uncompressed_name)
            decompressed_data[uncompressed_name] = typed_value
        return decompressed_data

    def decompress_generic_qr(self, data):
        """Decompress generic section of QR or raise error if schema is outdated."""
        # Split data by separator specified in schema
        data = data.split(self.SCHEMA["generic_data"]["_separator"])
        for entry in data:
            if entry[0] == "A":
                schema_version = int(entry[1:])
                if schema_version != self.SCHEMA["schema_file"]["version"]:
                    raise LookupError(
                        f'QR Schema (v{schema_version}) does not match Server version (v{self.SCHEMA["schema_file"]["version"]})'
                    )
        return self.decompress_data(data, "generic_data")

    def fail_consolidator(self, timeline):
        if not timeline:
            return []

        # create a new timeline
        new_timeline = []

        skip_next = False

        # loop through each action in the timeline
        for index in range(len(timeline)):

            # get the timeline action
            timeline_action = timeline[index]

            # if we skip this action (after a fail) just continue on
            if skip_next:
                skip_next = False

            # if the action is a fail and we arent at the end of the timeline
            elif timeline_action["action_type"] == "fail" and index != len(timeline) - 1:

                # we skip the next action as we are handling it already
                skip_next = True

                # if the next action has a valid failed actions
                if timeline[index + 1]["action_type"] in self.OBJ_TIM_SCHEMA["--fail_actions"]:

                    # replace the timeline actions action type with the cooresponding failed version
                    timeline_action["action_type"] = self.OBJ_TIM_SCHEMA["--fail_actions"][
                        timeline[index + 1]["action_type"]
                    ]["name"]
                else:
                    timeline_action["action_type"] = timeline[index + 1]["action_type"]

                # add the action to the new timeline
                new_timeline.append(timeline_action)
            else:

                # if there is no fail we just continue on
                new_timeline.append(timeline_action)

        return new_timeline

    # TODO: action types that are deemed "intake", "score", "drop", or ambiguous are super hard-coded since we don't have a consistent naming system nor a schema for this. We need to soften this by creating a schema
    def superposition_collapser(self, timeline, has_preload):
        """Fixes impossible timelines by just removing impossible actions"""

        if not timeline:
            return []

        updated_timeline = []

        queue = [[0, "coral", False]] if has_preload else []  # index, action, ambiguous

        index = 0
        for action in timeline:
            if "intake" in action["action_type"]:
                if len(queue) == 0:
                    queue.append(
                        [
                            index,
                            action["action_type"],
                            self.get_piece(action["action_type"], "intake") == "ambiguous",
                        ]
                    )
                elif len(queue) == 1:
                    hypothetical = [
                        self.get_piece(queue[0][1], "intake"),
                        self.get_piece(action["action_type"], "intake"),
                    ]

                    if hypothetical[0] == hypothetical[1]:
                        if "ambiguous" in hypothetical:
                            queue.append([index, action["action_type"], True])
                        else:
                            continue
                    # Once a robot has intaken a known piece, we automatically know what the other piece must be
                    elif "ambiguous" in hypothetical:
                        if hypothetical[1] == "ambiguous":
                            new_action = self.unambiguify(
                                action["action_type"],
                                "coral" if hypothetical[0] == "algae" else "algae",
                            )

                            queue.append([index, new_action, False])
                            updated_action = action
                            updated_action["action_type"] = new_action
                            updated_timeline.append(action)
                            index += 1
                            continue
                        else:
                            queue[0][1] = self.unambiguify(
                                queue[0][1], "coral" if hypothetical[1] == "algae" else "algae"
                            )

                            updated_timeline[queue[0][0]]["action_type"] = queue[0][1]
                    else:
                        queue.append([index, action["action_type"], False])
                else:
                    continue
            elif (
                "score" in action["action_type"]
                or "reef" in action["action_type"]
                or "processor" in action["action_type"]
                or "drop" in action["action_type"]
                or "coral" in action["action_type"]
                or "net" in action["action_type"]
            ):
                score_piece = self.get_piece(action["action_type"], "score")

                if len(queue) == 0:
                    continue
                elif len(queue) == 1:
                    held_piece = self.get_piece(queue[0][1], "intake")

                    if score_piece == held_piece:
                        queue.pop(0)
                    elif held_piece == "ambiguous":
                        updated_timeline[queue[0][0]]["action_type"] = self.unambiguify(
                            queue[0][1], score_piece
                        )
                        queue.pop(0)
                    else:
                        continue
                elif len(queue) == 2:
                    held_pieces = [
                        self.get_piece(queue[0][1], "intake"),
                        self.get_piece(queue[1][1], "intake"),
                    ]

                    if "ambiguous" in held_pieces:
                        updated_timeline[queue[0][0]]["action_type"] = self.unambiguify(
                            queue[0][1], score_piece
                        )
                        queue.pop(0)
                    elif score_piece == held_pieces[0]:
                        queue.pop(0)
                    elif score_piece == held_pieces[1]:
                        queue.pop(1)

            updated_timeline.append(action)
            index += 1

        return updated_timeline

    def get_piece(self, action, _type):
        if "coral" in action:
            return "coral"
        elif "algae" in action:
            return "algae"
        elif _type == "score":
            element_to_piece = {"reef": "coral", "net": "algae", "processor": "algae"}

            if action.split("_")[-2][0] == "F" and action.split("_")[-1][0] == "L":
                return "coral"
            elif "drop" not in action:
                return element_to_piece[action.split("_")[1]]
            else:
                return action.split("_")[-1]
        elif _type == "intake":
            element_to_piece = {
                "ground": "ambiguous",
                "poach": "ambiguous",
                "reef": "algae",
                "station": "coral",
            }

            return element_to_piece[action.split("_")[2]]

    def unambiguify(self, action, piece):
        if "ground" in action or "poach" in action:
            return f"{action}_{piece}"

    @staticmethod
    def super_decompress(super_compressed_schema, action_name, compressed_data):
        """ "decompresses but SUPER"""
        # initialize the ordinal values, unfortunately the max number has to be hardcoded, but is easily changed
        decompressed = {"first": "", "second": "", "third": "", "fourth": ""}

        if action_name not in super_compressed_schema:
            raise ValueError(f"Action {action_name} is not in the super compressed schema")
        else:
            action_info = super_compressed_schema[action_name]

        # loop through each ordinal (first, second, etc) in the super compressed schema
        for index, ordinal in enumerate(action_info["compressed"]):

            if int(compressed_data[index]) not in action_info["compressed"][ordinal].keys():
                raise ValueError(
                    f"Super compressed datapoint auto_reef has a value out of range at index: {index}"
                )

            # get the value from the schema based on the index of the compressed data
            value = action_info["compressed"][ordinal][int(compressed_data[index])]

            # makes none values empty
            if value:
                decompressed[ordinal] = value

        # It looks like these arent being used, but the eval statement uses them
        first, second, third, fourth = decompressed.values()

        # Evaluate the fstring from the schema using the above ordinal values
        return eval(f'f"""{action_info["template"]}"""')

    @staticmethod
    def check_timeline(timeline):

        data = timeline

        super_compressed = re.findall(r"RR\d{3}", data)

        # Remove all supercompressed occurrences from the timeline to simplify further validation
        # TODO soften code
        timeline_without_special = re.sub(r"RR\d{3}", "", data)

        # Pattern to find all two-letter codes
        letter_codes = re.findall(r"[A-Za-z]{2}", timeline_without_special)

        # Pattern to find all three-digit numbers
        numbers = re.findall(r"\d{3}", timeline_without_special)

        # Ensure the combined lengths match the original timeline length
        # This checks that there are no extra characters
        # TODO soften
        expected_length = (len(letter_codes) * 2) + (len(numbers) * 3) + (len(super_compressed) * 5)
        if expected_length != len(data):
            raise ValueError(f"Timeline length invalid - extra characters in: {data}")

        return True

    def decompress_timeline(self, data, has_preload):
        """Decompress the timeline based on schema."""
        decompressed_timeline = []  # Timeline is a list of dictionaries

        self.check_timeline(data)

        # return an empty list if there is no timeline
        if not data:
            return decompressed_timeline

        time_length = 0
        symbol_length = 0

        # get the legnths of the time and compressed symbol fields
        for entry in self.TIMELINE_FIELDS:
            if entry["name"] == "time":
                time_length = entry["length"]
            elif entry["name"] == "action_type":
                symbol_length = entry["length"]

        # initilize the current position in the timeline as well as the next one
        current_position = 0

        # Start in auto
        in_teleop = False
        # Loop through the entire timeline
        while current_position < len(data):

            # Initilize the decompressed action
            decompressed_action = {"time": 0, "action_type": "", "in_teleop": False}

            # split the time (like 007 or 012) from the current action
            action_time = data[current_position : current_position + time_length]
            current_position += time_length

            # Split the compressed symbol (like AC or BA) from the current action
            action_symbol = data[current_position : current_position + symbol_length]

            # advance the next position by one symbol
            current_position += symbol_length

            # Set the decompressed actions time
            decompressed_action["time"] = int(action_time)

            # change to teleop if the action is to teleop
            if action_symbol == self.SCHEMA["action_type"]["to_teleop"]:
                in_teleop = True

            # Set whether the decompressed action is in teleop
            decompressed_action["in_teleop"] = in_teleop

            # dectect if the symbol is a super com  pressed action
            if action_symbol in self.super_compressed_actions:

                # Get the name of the super compressed action
                action_name = self.get_decompressed_name(action_symbol, "action_type")

                # Get the number of fields in the compressed action
                super_compressed_data_length = len(
                    self.SCHEMA["super_compressed"][action_name]["compressed"].values()
                )

                super_compressed_data = data[
                    current_position : current_position + super_compressed_data_length
                ]

                # get the rest of the super compressed data and send it through the super decompress function
                decompressed_value = self.super_decompress(
                    self.SCHEMA["super_compressed"], action_name, super_compressed_data
                )

                # advance over the super compressed data
                current_position += super_compressed_data_length
            else:
                # Get the name of the normal timeline action
                decompressed_value = self.get_decompressed_name(action_symbol, "action_type")

            # Set the decompressed action type
            decompressed_action["action_type"] = decompressed_value

            # Add the decompressed action to the timeline
            if (
                "auto" in decompressed_action["action_type"] and decompressed_action["in_teleop"]
            ) or (
                "tele" in decompressed_action["action_type"]
                and not decompressed_action["in_teleop"]
            ):
                continue
            decompressed_timeline.append(decompressed_action)
        decompressed_timeline = self.superposition_collapser(decompressed_timeline, has_preload)
        decompressed_timeline = self.fail_consolidator(decompressed_timeline)

        return decompressed_timeline

    def get_qr_type(self, first_char):
        """Returns the qr type from QRType enum based on first character."""
        if first_char == self.SCHEMA["objective_tim"]["_start_character"]:
            return QRType.OBJECTIVE
        if first_char == self.SCHEMA["subjective_aim"]["_start_character"]:
            return QRType.SUBJECTIVE
        raise ValueError(f"QR type unknown - Invalid first character for QR: {first_char}")

    def decompress_single_qr(self, qr_data, qr_type, override):
        """Decompress a full QR."""
        # Split into generic data and objective/subjective data
        qr_data = qr_data.split(self.SCHEMA["generic_data"]["_section_separator"])
        # Generic QR is first section of QR
        decompressed_data = []
        # Decompress subjective QR
        if qr_type == QRType.SUBJECTIVE:
            teams_data = qr_data[1].split(self.SCHEMA["subjective_aim"]["_team_separator"])
            """none_generic_data = qr_data[1].split(
                self.SCHEMA["subjective_aim"]["_alliance_data_separator"]
            )
            if len(none_generic_data) != 2:
                raise IndexError("Subjective QR missing whole-alliance data")
            teams_data = none_generic_data[0].split(
                self.SCHEMA["subjective_aim"]["_team_separator"]
            )
            alliance_data = none_generic_data[1].split(
                self.SCHEMA["subjective_aim"]["_alliance_data_separator"]
            )
            """

            if len(teams_data) != 3:
                raise IndexError("Incorrect number of teams in Subjective QR")
            for team in teams_data:
                # Regular expression that finds all occurences of an integer occuring after "B" and "C" and returns the matches as a list of strings
                scores = re.findall(r"(?<=[BC])\d+", team)
                invalid = False
                for score in scores:
                    if score not in ["1", "2", "3"]:
                        invalid = True

                if invalid:
                    continue

                decompressed_document = self.decompress_generic_qr(qr_data[0])
                """
                subjective_data = team.split(self.SCHEMA["subjective_aim"]["_separator"]) + (
                    alliance_data if alliance_data != [""] else []
                )
                decompressed_data.append(decompressed_document)
                """
                subjective_data = team.split(self.SCHEMA["subjective_aim"]["_separator"])
                decompressed_document.update(
                    self.decompress_data(subjective_data, "subjective_aim")
                )
                if set(decompressed_document.keys()) != self.SUBJECTIVE_QR_FIELDS:
                    raise ValueError(
                        f"{qr_type} QR missing data fields. Expected {sorted(set(decompressed_document.keys()))}, got {sorted(self.SUBJECTIVE_QR_FIELDS)}"
                    )

                decompressed_data.append(decompressed_document)
        elif qr_type == QRType.OBJECTIVE:  # Decompress objective QR
            objective_data = qr_data[1].split(self.SCHEMA["objective_tim"]["_separator"])
            decompressed_document = self.decompress_generic_qr(qr_data[0])
            decompressed_document.update(self.decompress_data(objective_data, "objective_tim"))
            decompressed_data.append(decompressed_document)
            if set(decompressed_document.keys()) != self.OBJECTIVE_QR_FIELDS:
                raise ValueError("QR missing data fields", qr_type)
            decompressed_document.update({"override": override})
        return decompressed_data

    def decompress_qrs(self, split_qrs):
        """Decompresses a list of QRs. Returns dict of decompressed QRs split by type."""
        output = {"unconsolidated_obj_tim": [], "subj_tim": []}
        unique_qrs = set()
        for qr in split_qrs:
            qr_type = utils.catch_function_errors(self.get_qr_type, qr["data"][0])
            if qr_type is None:
                continue
            decompressed_qr = utils.catch_function_errors(
                self.decompress_single_qr, qr["data"][1:], qr_type, qr["override"]
            )
            if decompressed_qr is None:
                log.info(f"Bad QR not decompressed:")
                print(f"{qr['data']}")
                continue
            decompressed_qrs = []
            for d_qr in decompressed_qr:
                if (d_qr["match_number"], d_qr["scout_name"], d_qr["team_number"]) in unique_qrs:
                    continue
                else:
                    unique_qrs.add((d_qr["match_number"], d_qr["scout_name"], d_qr["team_number"]))
                    decompressed_qrs.append(d_qr)
            # Override non-timeline datapoints at decompression
            for decompressed in decompressed_qrs:
                decompressed["ulid"] = qr["ulid"]
                for override in qr["override"]:
                    if override in decompressed and override not in list(
                        self.OBJ_TIM_SCHEMA["timeline_counts"].keys()
                    ):  # Checks that override is not a timeline datapoint
                        decompressed[override] = qr["override"][override]
                # If there were datapoints in override that weren't in decompressed data,
                # add override to data for obj_tim calcs to handle
            if qr_type == QRType.OBJECTIVE:
                output["unconsolidated_obj_tim"].extend(decompressed_qrs)
            elif qr_type == QRType.SUBJECTIVE:
                output["subj_tim"].extend(decompressed_qrs)

        finished_matches = []
        for i in range(len(output["subj_tim"])):
            if output["subj_tim"][i]["match_number"] not in finished_matches:
                hp_team_number = ""
                indices_in_match = []
                for j in range(len(output["subj_tim"])):
                    if (
                        output["subj_tim"][j]["match_number"]
                        == output["subj_tim"][i]["match_number"]
                    ):
                        indices_in_match.append(j)
                        if output["subj_tim"][j]["hp_from_team"]:
                            hp_team_number = output["subj_tim"][j]["team_number"]
                            break
                for index in indices_in_match:
                    output["subj_tim"][index]["hp_team_number"] = hp_team_number
                finished_matches.append(output["subj_tim"][i]["match_number"])

        return output

    def decompress_pit_data(self, pit_data, pit_type):
        """Decompresses ONE obj or subj pit data dict

        pit_data: a dict of raw pit data
        pit_type: raw_obj_pit or raw_subj_pit"""
        # Get pit schema file
        if pit_type == "raw_obj_pit":
            pit_schema = self.OBJ_PIT_SCHEMA
        elif pit_type == "raw_subj_pit":
            pit_schema = self.SUBJ_PIT_SCHEMA

        decompressed_data = {}
        db = database.Database()
        # Use team number to find if team already has pit data inserted into MongoDB
        current_data = [
            document
            for document in db.find(pit_type)
            if document["team_number"] == pit_data["team_number"]
        ]

        # Enter data into a dictionary
        for name, value in pit_data.items():
            # if variable is an Enum, decompress it
            if "Enum" in pit_schema["schema"][name]["type"]:
                for enum_name, enum_value in pit_schema["enums"][name].items():
                    if enum_value == value:
                        decompressed_data[name] = enum_name
                        break
            else:
                decompressed_data[name] = value

        # Since Front-End doesn't keep variables empty when they don't
        # have values, we have to iterate through every variable to make
        # sure there's either (a) data or (b) a "None" placeholder
        for var in pit_schema["schema"].keys():
            if var not in decompressed_data:
                decompressed_data[var] = None

        if current_data:
            team_num = decompressed_data["team_number"]
            current_document = current_data[0]
            for name, value in decompressed_data.items():
                if current_document[name] == value:
                    continue
                # If type is a boolean, since default is false, if one is true, that means it was scouted, therefore we put true
                if pit_schema["schema"][name]["type"] == "bool":
                    if current_document[name] or value:
                        decompressed_data.update({name: True})
                # For nums, the default is 0, if the new document has a 0, go with the previously inserted one, else let the new one be inserted
                elif (
                    pit_schema["schema"][name]["type"] == "int"
                    or pit_schema["schema"][name]["type"] == "float"
                ):
                    if current_document[name] != 0 and value == 0:
                        decompressed_data.update({name: current_document[name]})
                    elif current_document[name] != 0 and value != 0:
                        log.warning(
                            f"Both pit scouts collected data on team {team_num} for field {name} and collected different values"
                        )
                # For the enum strings, they must be compared individually
                elif name == "drivetrain":
                    if value != "no_data":
                        continue
                    if current_document[name] != "no_data":
                        decompressed_data.update({name: current_document[name]})
                        continue
                    log.warning(
                        f"Both pit scouts collected data for team: {team_num} for the field: {name} and came up with different values"
                    )
        return decompressed_data

    def check_scout_ids(self):
        """Checks unconsolidated TIMs in `tim_queue` to see which scouts have not sent data.

        This operation is done by `scout_id` -- if a match is missing data, then the scout_id will not
        have sent data for the match.
        returns None -- warnings are issued directly through `log.warning`.
        """
        # Load matches or matches and ids to ignore from ignore file
        if os.path.exists(self.MISSING_TIM_IGNORE_FILE_PATH):
            with open(self.MISSING_TIM_IGNORE_FILE_PATH) as ignore_file:
                items_to_ignore = yaml.load(ignore_file, Loader=yaml.Loader)
        else:
            items_to_ignore = []
        matches_to_ignore = [item["match_number"] for item in items_to_ignore if len(item) == 1]
        tims = self.server.local_db.find("unconsolidated_obj_tim")
        matches = {}
        for tim in tims:
            match_number = tim["match_number"]
            matches[match_number] = matches.get(match_number, []) + [tim["scout_id"]]

        for match, scout_ids in matches.items():
            if match in matches_to_ignore:
                continue
            unique_scout_ids = []
            for id_ in scout_ids:
                if id_ in unique_scout_ids:
                    if {"match_number": match, "scout_id": id_} not in items_to_ignore:
                        log.warning(f"Duplicate Scout ID {id_} for Match {match}")
                else:
                    unique_scout_ids.append(id_)
            # Scout IDs are from 1-18 inclusive
            for id_ in range(1, 19):
                if id_ not in unique_scout_ids:
                    if {"match_number": match, "scout_id": id_} not in items_to_ignore:
                        log.warning(f"Scout ID {id_} missing from Match {match}")

    @staticmethod
    def decompress_ss_team(data):
        schema = utils.read_schema("schema/calc_ss_team.yml")
        for point, value in schema["schema"].items():
            if point not in list(data.keys()):
                data[point] = None
        return data

    @staticmethod
    def decompress_ss_tim(data):
        # If data is an empty dict, return it since the TIM was not scouted
        if not data:
            return data
        schema = utils.read_schema("schema/calc_ss_tim.yml")
        for point, val in schema["schema"].items():
            if point not in list(data.keys()):
                data[point] = None
            elif point == "broken_mechanism":
                data[point] = True if data[point] != "" else False
            elif val["type"] == "bool" and data[point] is None:
                data[point] = False
        return data

    @staticmethod
    def consolidate_ss_team(team_number, db_read):
        schema = utils.read_schema("schema/calc_ss_team.yml")
        documents = db_read.find("unconsolidated_ss_team", {"team_number": team_number})
        if len(documents) == 1:
            return documents[0]
        else:
            final = {}
            for field, val in schema["schema"].items():
                if val["type"] == "bool":
                    if documents[0][field] or documents[1][field]:
                        # Default to True for booleans (if we ever get a different default value we will make schema changes)
                        final[field] = True
                    else:
                        final[field] = False
                elif val["type"] == "str":
                    final[field] = ""
                    if documents[0][field] == documents[1][field]:
                        final[field] = f"{documents[0][field]}"
                    else:
                        final[field] = f"{documents[0][field]} + {documents[1][field]}"
            # Averages will be the same for both (since they both pull from ss_tim)
            for point in schema["averages"].keys():
                final[point] = documents[0][point]
            return final

    def run(self):
        timer = Timer()

        all_qrs = self.server.local_db.find("raw_qr")
        modified = []
        for qr in all_qrs:
            if not qr["blocklisted"]:
                qr["data"] = qr["data"].upper()
                modified.append(qr)
        all_qrs = modified
        decompressed_qrs = self.decompress_qrs(all_qrs)

        # Checks if two subjective scouts scouted the same alliance in a match
        # If so, delete one of the qrs
        unique_combinations = set()
        filtered_qrs = []
        for qr in decompressed_qrs["subj_tim"]:
            match_number = qr["match_number"]
            alliance_color = qr["alliance_color_is_red"]
            team_number = qr["team_number"]

            if (match_number, alliance_color, team_number) not in unique_combinations:
                unique_combinations.add((match_number, alliance_color, team_number))
                filtered_qrs.append(qr)

        decompressed_qrs["subj_tim"] = filtered_qrs

        for collection in ["unconsolidated_obj_tim", "subj_tim"]:
            self.server.local_db.delete_data(collection)
            self.server.local_db.insert_documents(collection, decompressed_qrs[collection])

        override.apply_override("unconsolidated_obj_tim")
        override.apply_override("subj_tim")

        timer.end_timer(__file__)
