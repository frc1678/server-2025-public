from unittest.mock import patch, MagicMock
import utils
import builtins
import utils
from calculations import decompressor
import server
import generate_test_qrs
import random

# Get schema
SCHEMA = utils.read_schema("schema/match_collection_qr_schema.yml")

# Get decompressor
with patch("doozernet_communicator.check_model_availability", return_value=None):
    with patch("utils.get_match_schedule", return_value=[]):
        with patch("utils.get_team_list", return_value=[]):
            DECOMPRESSOR = decompressor.Decompressor(server.Server())

ALLIANCE_COLORS = ["red", "blue"]


# Test generic data generator
def test_gen_generic_data():
    # get generic schema
    generic_schema = SCHEMA["generic_data"]

    # run test multiple times
    for i in range(4):
        # Generate some generic data
        generic_data = generate_test_qrs.gen_generic_data(1678, ALLIANCE_COLORS[i % 2], str(i))

        # Decompress it
        decompressed_data = DECOMPRESSOR.decompress_generic_qr(generic_data)
        # check decompressed data type against match collection schema type
        for entry in list(decompressed_data.keys()):
            assert type(decompressed_data[entry]) == getattr(builtins, generic_schema[entry][1])


def test_gen_timeline():
    # get timeline schema
    timeline_schema = SCHEMA["timeline"]

    # get action type schema
    action_schema = SCHEMA["action_type"]

    has_preload = random.choice([True, False])

    # get a generated timeline
    timeline_data = generate_test_qrs.gen_timeline("1678", (1, "red"), has_preload)

    # decompress data
    decompressed_data = DECOMPRESSOR.decompress_timeline(timeline_data[1:], has_preload)

    for entry in decompressed_data:
        assert entry["time"] >= 0
        assert entry["time"] <= 230


def test_gen_obj_tim():
    # get objective tim schema
    obj_tim_schema = SCHEMA["objective_tim"]

    # generated objective tim data
    obj_tim_data = generate_test_qrs.gen_obj_tim("1678", (1, "red"))

    # seperate
    obj_tim_data = obj_tim_data.split(obj_tim_schema["_separator"])

    # decompress data
    decompressed_data = DECOMPRESSOR.decompress_data(obj_tim_data, "objective_tim")

    for entry in list(decompressed_data.keys()):
        assert type(decompressed_data[entry]) == getattr(builtins, obj_tim_schema[entry][1])


def test_gen_subj_aim():
    # get subjective aim schema
    subj_aim_schema = SCHEMA["subjective_aim"]

    # generate subjective aim data
    subj_aim_data = generate_test_qrs.gen_subj_aim("1678")

    # seperate
    subj_aim_data = subj_aim_data.split(subj_aim_schema["_separator"])

    # decompress data
    decompressed_data = DECOMPRESSOR.decompress_data(subj_aim_data, "subjective_aim")

    for entry in list(decompressed_data.keys()):
        assert type(decompressed_data[entry]) == getattr(builtins, subj_aim_schema[entry][1])
