from calculations import compression
import pytest
from utils import read_schema


def test_compress_timeline():
    timeline_data = [
        {"time": 1, "action_type": "start_incap"},
        {"time": 0, "action_type": "end_incap"},
    ]
    assert compression.compress_timeline(timeline_data) == "001AY000AZ"
    timeline_data[1]["action_type"] = "tele_intake_reef"
    assert compression.compress_timeline(timeline_data) == "001AY000AV"


def test_compress_section_generic_data():
    # Make sure it adds schema version
    assert (
        compression.compress_section({}, "generic_data")
        == f'A{read_schema("schema/match_collection_qr_schema.yml")["schema_file"]["version"]}'
    )
    # Check generic data compression
    schema_data = {"schema_version": 5}
    compressed_schema = "A5"
    assert compression.compress_section(schema_data, "generic_data") == compressed_schema


def test_compress_section_obj():
    # Without timeline
    schema_data = {"team_number": "1678", "scout_id": 18}
    compressed_schema = "Z1678$Y18"
    assert compression.compress_section(schema_data, "objective_tim") == compressed_schema
    # With timeline
    schema_data["timeline"] = [
        {"time": 51, "action_type": "auto_intake_ground_2", "in_teleop": False}
    ]
    compressed_schema += "$W051AD"
    assert compression.compress_section(schema_data, "objective_tim") == compressed_schema


def test_compress_section_subj():
    data = {
        "team_number": "1678",
        "agility_score": 2,
        "field_awareness_score": 1,
    }
    compressed_data = "A1678$B2$C1"
    assert compression.compress_section(data, "subjective_aim") == compressed_data


def test_compress_obj_tim():
    data = {
        "schema_version": 1,
        "match_number": 1,
        "timestamp": 8392049382,
        "match_collection_version_number": "1.0.2",
        "team_number": "9999",
        "scout_name": "JELLY K",
        "scout_id": 2,
        "start_position": "3",
        "timeline": [
            {"time": 45, "action_type": "start_incap"},
            {"time": 7, "action_type": "end_incap"},
        ],
        "has_preload": True,
        "stage_level_left": "O",
        "stage_level_right": "N",
        "stage_level_center": "N",
        "park": False,
    }
    compressed_data = "+A1$B1$C8392049382$D1.0.2$EJELLY K%Z9999$Y2$X3$W045AY007AZ$VTRUE$SFALSE"
    assert compression.compress_obj_tim(data) == compressed_data


def test_compress_subj_aim():
    data = [
        {
            "schema_version": 1,
            "match_number": 1,
            "timestamp": 1582994470,
            "match_collection_version_number": "1.0.2",
            "scout_name": "YOUYOU X",
            "team_number": "3128",
            "agility_score": 1,
            "field_awareness_score": 2,
            "time_left_to_climb": 3,
            "climb_after": True,
        },
        {
            "schema_version": 1,
            "match_number": 1,
            "timestamp": 1582994470,
            "match_collection_version_number": "1.0.2",
            "scout_name": "YOUYOU X",
            "team_number": "1678",
            "agility_score": 2,
            "field_awareness_score": 1,
            "time_left_to_climb": 1,
            "climb_after": False,
        },
        {
            "schema_version": 1,
            "match_number": 1,
            "timestamp": 1582994470,
            "match_collection_version_number": "1.0.2",
            "scout_name": "YOUYOU X",
            "team_number": "972",
            "agility_score": 3,
            "field_awareness_score": 3,
            "time_left_to_climb": 3,
            "climb_after": False,
        },
    ]
    compressed_data = (
        "*A1$B1$C1582994470$D1.0.2$EYOUYOU X%A3128$B1$C2$D3#A1678$B2$C1$D1#A972$B3$C3$D3"
    )
    assert compression.compress_subj_aim(data) == compressed_data
    error_data = [
        {
            "schema_version": 1,
            "match_number": 2,
            "timestamp": 3849293920,
            "match_collection_version_number": "1.0.2",
            "scout_name": "KINA L",
            "team_number": "3128",
            "agility_score": 2,
            "field_awareness_score": 2,
            "time_left_to_climb": 3,
            "climb_after": False,
        },
        {
            "schema_version": 1,
            "match_number": 1,
            "timestamp": 1582994470,
            "match_collection_version_number": "1.0.2",
            "scout_name": "YOUYOU X",
            "team_number": "1678",
            "agility_score": 2,
            "field_awareness_score": 3,
            "time_left_to_climb": 1,
            "climb_after": True,
        },
        {
            "schema_version": 1,
            "match_number": 1,
            "timestamp": 48392039483,
            "match_collection_version_number": "1.0.2",
            "scout_name": "YOUYOU X",
            "team_number": "972",
            "agility_score": 1,
            "field_awareness_score": 3,
            "time_left_to_climb": 2,
            "climb_after": True,
        },
    ]
    with pytest.raises(ValueError) as error:
        compression.compress_subj_aim(error_data)
    assert "Different generic data between documents in the same subj QR" in str(error)
