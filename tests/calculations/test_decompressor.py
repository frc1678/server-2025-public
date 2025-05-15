import datetime

import pytest
from unittest.mock import patch

import server
from calculations import decompressor


@pytest.mark.clouddb
class TestDecompressor:
    def setup_method(self, method):
        with patch("doozernet_communicator.check_model_availability", return_value=None), patch(
            "utils.get_match_schedule", return_value=[]
        ), patch("utils.get_team_list", return_value=[]):
            self.test_server = server.Server()
        self.test_decompressor = decompressor.Decompressor(self.test_server)

    def test___init__(self):
        assert self.test_decompressor.server == self.test_server
        assert self.test_decompressor.watched_collections == ["raw_qr"]

    def test_convert_data_type(self):
        # List of compressed names and decompressed names of enums
        action_type_dict = {
            "auto_reef": "RR",
            "auto_drop_algae": "AA",
            "auto_drop_coral": "AB",
            "auto_intake_ground_1": "AC",
            "auto_intake_ground_2": "AD",
            "auto_intake_mark_1_coral": "AE",
            "auto_intake_mark_2_coral": "AF",
            "auto_intake_mark_3_coral": "AG",
            "auto_intake_mark_1_algae": "BK",
            "auto_intake_mark_2_algae": "BI",
            "auto_intake_mark_3_algae": "BJ",
            "auto_intake_reef_F1": "AH",
            "auto_intake_reef_F2": "AI",
            "auto_intake_reef_F3": "AJ",
            "auto_intake_reef_F4": "AK",
            "auto_intake_reef_F5": "AL",
            "auto_intake_reef_F6": "AM",
            "auto_intake_station_1": "AN",
            "auto_intake_station_2": "AO",
            "tele_coral_L1": "AP",
            "tele_coral_L2": "AQ",
            "tele_coral_L3": "AR",
            "tele_coral_L4": "BF",
            "tele_drop_algae": "AS",
            "tele_drop_coral": "AT",
            "tele_intake_ground": "AU",
            "tele_intake_reef": "AV",
            "tele_intake_station": "AW",
            "tele_processor": "AX",
            "tele_net": "BG",
            "start_incap": "AY",
            "end_incap": "AZ",
            "to_teleop": "BA",
            "to_endgame": "BB",
            "auto_net": "BC",
            "auto_processor": "BD",
            "fail": "BE",
            "tele_intake_poach": "BH",
        }
        # Test a few values for each type to make sure they make sense
        assert 5 == self.test_decompressor.convert_data_type("5", "int")
        assert 6 == self.test_decompressor.convert_data_type(6.43, "int")
        assert 5.0 == self.test_decompressor.convert_data_type("5", "float")
        assert 6.32 == self.test_decompressor.convert_data_type("6.32", "float")
        assert 3.0 == self.test_decompressor.convert_data_type(3, "float")
        assert self.test_decompressor.convert_data_type("1", "bool")
        assert self.test_decompressor.convert_data_type("T", "bool")
        assert self.test_decompressor.convert_data_type("TRUE", "bool")
        assert not self.test_decompressor.convert_data_type("0", "bool")
        assert not self.test_decompressor.convert_data_type("F", "bool")
        assert not self.test_decompressor.convert_data_type("FALSE", "bool")
        assert "" == self.test_decompressor.convert_data_type("", "str")
        # Test all enums
        for decompressed, compressed in action_type_dict.items():
            assert decompressed == self.test_decompressor.convert_data_type(
                compressed, "Enum", name="action_type"
            )
        # Test error raising
        with pytest.raises(ValueError) as type_error:
            self.test_decompressor.convert_data_type("", "tuple")
        assert "Type tuple not recognized" in str(type_error.value)

    def test_get_decompressed_name(self):
        # Test for the that '$' returns '_separator' in all 3 sections that have it
        sections = ["generic_data", "objective_tim", "subjective_aim"]
        for section in sections:
            assert "_separator" == self.test_decompressor.get_decompressed_name("$", section)
        # Test for a name with a string and a name with a list from each section
        assert "_section_separator" == self.test_decompressor.get_decompressed_name(
            "%", "generic_data"
        )
        assert "timeline" == self.test_decompressor.get_decompressed_name("W", "objective_tim")
        assert "_start_character" == self.test_decompressor.get_decompressed_name(
            "+", "objective_tim"
        )
        assert "time" == self.test_decompressor.get_decompressed_name(3, "timeline")
        assert "_start_character" == self.test_decompressor.get_decompressed_name(
            "*", "subjective_aim"
        )
        assert "_team_separator" == self.test_decompressor.get_decompressed_name(
            "#", "subjective_aim"
        )
        assert "scout_id" == self.test_decompressor.get_decompressed_name("Y", "objective_tim")
        assert "start_position" == self.test_decompressor.get_decompressed_name(
            "X", "objective_tim"
        )
        assert "field_awareness_score" == self.test_decompressor.get_decompressed_name(
            "C", "subjective_aim"
        )
        assert "tele_coral_L1" == self.test_decompressor.get_decompressed_name("AP", "action_type")
        assert "auto_intake_mark_2_coral" == self.test_decompressor.get_decompressed_name(
            "AF", "action_type"
        )
        assert "has_preload" == self.test_decompressor.get_decompressed_name("V", "objective_tim")
        with pytest.raises(ValueError) as excinfo:
            self.test_decompressor.get_decompressed_name("#", "generic_data")
        assert "Retrieving Variable Name # from generic_data failed." in str(excinfo)

    def test_get_decompressed_type(self):
        # Test when there are two values in a list
        assert "int" == self.test_decompressor.get_decompressed_type(
            "schema_version", "generic_data"
        )
        # Test when list has more than two values
        assert ["list", "dict"] == self.test_decompressor.get_decompressed_type(
            "timeline", "objective_tim"
        )

    def test_decompress_data(self):
        # Test generic data
        assert {
            "schema_version": 7,
            "scout_name": "Name",
        } == self.test_decompressor.decompress_data(["A7", "EName"], "generic_data")
        # Test objective tim
        assert {"team_number": "1678"} == self.test_decompressor.decompress_data(
            ["Z1678"], "objective_tim"
        )
        # Test timeline decompression
        assert {
            "timeline": [{"action_type": "auto_drop_coral", "time": 51, "in_teleop": False}]
        } == self.test_decompressor.decompress_data(["W051AB"], "objective_tim")
        # Test using list with internal separators
        assert {
            "agility_score": 1,
            "field_awareness_score": 3,
        } == self.test_decompressor.decompress_data(["B1", "C3"], "subjective_aim")

    def test_decompress_generic_qr(self):
        # Test if the correct error is raised when the Schema version is incorrect
        with pytest.raises(LookupError) as version_error:
            self.test_decompressor.decompress_generic_qr("A250$")
        assert "does not match Server version" in str(version_error)
        # What decompress_generic_qr() should return
        expected_decompressed_data = {
            "schema_version": decompressor.Decompressor.SCHEMA["schema_file"][
                "version"
            ],  # read the current version of schema file
            "match_number": 34,
            "timestamp": 1230,
            "match_collection_version_number": "v1.3",
            "scout_name": "Name",
        }
        assert expected_decompressed_data == self.test_decompressor.decompress_generic_qr(
            f"A{decompressor.Decompressor.SCHEMA['schema_file']['version']}$B34$C1230$Dv1.3$EName"
        )

    def test_super_decompress(self):

        super_compressed_schema = decompressor.Decompressor.SCHEMA["super_compressed"]

        assert (
            self.test_decompressor.super_decompress(super_compressed_schema, "auto_reef", "123")
            == "auto_score_F2_L3"
        )
        assert (
            self.test_decompressor.super_decompress(super_compressed_schema, "auto_reef", "023")
            == "auto_fail_score_F2_L3"
        )
        assert (
            self.test_decompressor.super_decompress(super_compressed_schema, "auto_reef", "134")
            == "auto_score_F3_L4"
        )
        assert (
            self.test_decompressor.super_decompress(super_compressed_schema, "auto_reef", "011")
            == "auto_fail_score_F1_L1"
        )

        with pytest.raises(ValueError) as super_decompress_error:
            self.test_decompressor.super_decompress(super_compressed_schema, "auto_reef", "223")
        assert "Super compressed datapoint auto_reef has a value out of range at index: 0" in str(
            super_decompress_error
        )

        with pytest.raises(ValueError) as super_decompress_error:
            self.test_decompressor.super_decompress(super_compressed_schema, "auto_doozer", "121")

        assert "Action auto_doozer is not in the super compressed schema" in str(
            super_decompress_error
        )

    def test_superposition_collapser(self):

        test_timeline_1 = [
            {"time": 140, "action_type": "auto_score_F2_L2", "in_teleop": False},
            {"time": 135, "action_type": "auto_intake_ground_1", "in_teleop": False},
            {"time": 130, "action_type": "auto_score_F3_L3", "in_teleop": False},
            {"time": 125, "action_type": "auto_intake_reef_F1", "in_teleop": False},
            {"time": 120, "action_type": "auto_intake_ground_1", "in_teleop": False},
            {"time": 115, "action_type": "to_teleop", "in_teleop": True},
            {"time": 110, "action_type": "tele_coral_L1", "in_teleop": True},
            {"time": 105, "action_type": "fail", "in_teleop": True},
            {"time": 102, "action_type": "tele_net", "in_teleop": True},
            {"time": 97, "action_type": "tele_intake_ground", "in_teleop": True},
            {"time": 93, "action_type": "auto_intake_station_1", "in_teleop": True},
            {"time": 90, "action_type": "tele_drop_algae", "in_teleop": True},
            {"time": 85, "action_type": "to_endgame", "in_teleop": True},
        ]

        test_timeline_2 = [
            {"time": 135, "action_type": "auto_intake_ground_1", "in_teleop": False},
            {"time": 130, "action_type": "auto_intake_ground_1", "in_teleop": False},
            {"time": 125, "action_type": "auto_net", "in_teleop": False},
            {"time": 125, "action_type": "auto_score_F3_L4", "in_teleop": False},
            {"time": 120, "action_type": "auto_intake_ground_1", "in_teleop": False},
            {"time": 115, "action_type": "to_teleop", "in_teleop": True},
            {"time": 105, "action_type": "fail", "in_teleop": True},
            {"time": 102, "action_type": "tele_net", "in_teleop": True},
            {"time": 97, "action_type": "tele_intake_ground", "in_teleop": True},
            {"time": 93, "action_type": "auto_intake_station_1", "in_teleop": True},
            {"time": 90, "action_type": "tele_drop_algae", "in_teleop": True},
            {"time": 85, "action_type": "to_endgame", "in_teleop": True},
        ]

        test_collapsed_timeline_1 = [
            {"time": 140, "action_type": "auto_score_F2_L2", "in_teleop": False},
            {"time": 135, "action_type": "auto_intake_ground_1_coral", "in_teleop": False},
            {"time": 130, "action_type": "auto_score_F3_L3", "in_teleop": False},
            {"time": 125, "action_type": "auto_intake_reef_F1", "in_teleop": False},
            {"time": 120, "action_type": "auto_intake_ground_1_coral", "in_teleop": False},
            {"time": 115, "action_type": "to_teleop", "in_teleop": True},
            {"time": 110, "action_type": "tele_coral_L1", "in_teleop": True},
            {"time": 105, "action_type": "fail", "in_teleop": True},
            {"time": 102, "action_type": "tele_net", "in_teleop": True},
            {"time": 97, "action_type": "tele_intake_ground_algae", "in_teleop": True},
            {"time": 93, "action_type": "auto_intake_station_1", "in_teleop": True},
            {"time": 90, "action_type": "tele_drop_algae", "in_teleop": True},
            {"time": 85, "action_type": "to_endgame", "in_teleop": True},
        ]

        test_collapsed_timeline_2 = [
            {"time": 135, "action_type": "auto_intake_ground_1_algae", "in_teleop": False},
            {"time": 130, "action_type": "auto_intake_ground_1_coral", "in_teleop": False},
            {"time": 125, "action_type": "auto_net", "in_teleop": False},
            {"time": 125, "action_type": "auto_score_F3_L4", "in_teleop": False},
            {"time": 120, "action_type": "auto_intake_ground_1_algae", "in_teleop": False},
            {"time": 115, "action_type": "to_teleop", "in_teleop": True},
            {"time": 105, "action_type": "fail", "in_teleop": True},
            {"time": 102, "action_type": "tele_net", "in_teleop": True},
            {"time": 97, "action_type": "tele_intake_ground_algae", "in_teleop": True},
            {"time": 93, "action_type": "auto_intake_station_1", "in_teleop": True},
            {"time": 90, "action_type": "tele_drop_algae", "in_teleop": True},
            {"time": 85, "action_type": "to_endgame", "in_teleop": True},
        ]

        assert (
            self.test_decompressor.superposition_collapser(test_timeline_1, True)
            == test_collapsed_timeline_1
        )
        assert (
            self.test_decompressor.superposition_collapser(test_timeline_2, False)
            == test_collapsed_timeline_2
        )

    def test_fail_consolidator(self):

        test_preconsolidated_timeline = [
            {"time": 135, "action_type": "auto_intake_ground_1_algae", "in_teleop": False},
            {"time": 130, "action_type": "auto_intake_ground_1_coral", "in_teleop": False},
            {"time": 125, "action_type": "auto_net", "in_teleop": False},
            {"time": 125, "action_type": "auto_score_F3_L4", "in_teleop": False},
            {"time": 120, "action_type": "auto_intake_ground_1_algae", "in_teleop": False},
            {"time": 115, "action_type": "to_teleop", "in_teleop": True},
            {"time": 105, "action_type": "fail", "in_teleop": True},
            {"time": 102, "action_type": "tele_net", "in_teleop": True},
            {"time": 97, "action_type": "tele_intake_ground_algae", "in_teleop": True},
            {"time": 93, "action_type": "auto_intake_station_1", "in_teleop": True},
            {"time": 90, "action_type": "tele_drop_algae", "in_teleop": True},
            {"time": 85, "action_type": "to_endgame", "in_teleop": True},
        ]

        test_consolidated_timeline = [
            {"time": 135, "action_type": "auto_intake_ground_1_algae", "in_teleop": False},
            {"time": 130, "action_type": "auto_intake_ground_1_coral", "in_teleop": False},
            {"time": 125, "action_type": "auto_net", "in_teleop": False},
            {"time": 125, "action_type": "auto_score_F3_L4", "in_teleop": False},
            {"time": 120, "action_type": "auto_intake_ground_1_algae", "in_teleop": False},
            {"time": 115, "action_type": "to_teleop", "in_teleop": True},
            {"time": 105, "action_type": "fail", "in_teleop": True},
            {"time": 102, "action_type": "tele_fail_net", "in_teleop": True},
            {"time": 97, "action_type": "tele_intake_ground_algae", "in_teleop": True},
            {"time": 93, "action_type": "auto_intake_station_1", "in_teleop": True},
            {"time": 90, "action_type": "tele_drop_algae", "in_teleop": True},
            {"time": 85, "action_type": "to_endgame", "in_teleop": True},
        ]

    def test_decompress_timeline(self):
        # Function should raise an error if the data isn't the right length
        with pytest.raises(ValueError) as excinfo:
            self.test_decompressor.decompress_timeline("abcdefg", False)
        assert "Timeline length invalid - extra characters in: abcdefg" in str(excinfo)

        # Test timeline decompression
        assert [
            {"time": 61, "action_type": "auto_intake_reef_F1", "in_teleop": False},
            {"time": 60, "action_type": "auto_score_F3_L4", "in_teleop": False},
            {"time": 59, "action_type": "to_teleop", "in_teleop": True},
            {"time": 56, "action_type": "tele_intake_station", "in_teleop": True},
        ] == self.test_decompressor.decompress_timeline("061AH060RR134059BA056AW", True)
        # Should return empty list if passed an empty string
        assert [] == self.test_decompressor.decompress_timeline("", True)

    def test_decompress_single_qr(self):
        # Expected decompressed objective qr
        expected_objective = [
            {
                "schema_version": decompressor.Decompressor.SCHEMA["schema_file"]["version"],
                "match_number": 34,
                "override": {},
                "timestamp": 1230,
                "match_collection_version_number": "v1.3",
                "scout_name": "Doozer",
                "alliance_color_is_red": False,
                "cage_level": "2",
                "cage_fail": False,
                "has_preload": True,
                "team_number": "1678",
                "scout_id": 12,
                "start_position": "2",
                "timeline": [
                    {"time": 61, "action_type": "auto_drop_coral", "in_teleop": False},
                    {"time": 60, "action_type": "auto_intake_reef_F1", "in_teleop": False},
                ],
                "park": True,
            },
        ]
        # Expected decompressed subjective qr
        # Only 2 teams should be returned, 254 should be cut due to an invalid agility score
        expected_subjective = [
            {
                "schema_version": 1,
                "match_number": 1,
                "timestamp": 1212,
                "match_collection_version_number": "4.8.1",
                "scout_name": "DOOZER",
                "alliance_color_is_red": False,
                "team_number": "7056",
                "time_left_to_climb": 10,
                "agility_score": 1,
                "field_awareness_score": 1,
                "died": False,
                "can_cross_barge": False,
                "was_tippy": True,
                "hp_from_team": False,
            },
            {
                "schema_version": 1,
                "match_number": 1,
                "timestamp": 1212,
                "match_collection_version_number": "4.8.1",
                "scout_name": "DOOZER",
                "alliance_color_is_red": False,
                "team_number": "9496",
                "time_left_to_climb": 10,
                "agility_score": 1,
                "field_awareness_score": 1,
                "died": False,
                "can_cross_barge": True,
                "was_tippy": False,
                "hp_from_team": True,
            },
            {
                "schema_version": 1,
                "match_number": 1,
                "timestamp": 1212,
                "match_collection_version_number": "4.8.1",
                "scout_name": "DOOZER",
                "alliance_color_is_red": False,
                "team_number": "6090",
                "time_left_to_climb": 10,
                "agility_score": 2,
                "field_awareness_score": 1,
                "died": True,
                "can_cross_barge": False,
                "was_tippy": False,
                "hp_from_team": False,
            },
        ]
        # Test objective qr decompression
        assert expected_objective == self.test_decompressor.decompress_single_qr(
            f"A{decompressor.Decompressor.SCHEMA['schema_file']['version']}$B34$C1230$Dv1.3$EDoozer$FFALSE%Z1678$Y14$X3$W061AB060AH$STrue$U2$TFalse$VTRUE$X2$Y12$Z1678",
            decompressor.QRType.OBJECTIVE,
            {},
        )
        # Test subjective qr decompression
        assert expected_subjective == self.test_decompressor.decompress_single_qr(
            f"A{decompressor.Decompressor.SCHEMA['schema_file']['version']}$B1$C1212$D4.8.1$EDOOZER$FFALSE%A7056$B1$C1$D10$GFALSE$EFALSE$D10$ITRUE$HFALSE#A9496$B1$C1$D10$GFALSE$ETRUE$D10$IFALSE$HTRUE#A6090$B2$C1$D10$GTRUE$EFALSE$D10$IFALSE$HFALSE",
            decompressor.QRType.SUBJECTIVE,
            {},
        )
        # Test error raising for objective and subjective using incomplete qrs
        with pytest.raises(ValueError) as excinfo:
            self.test_decompressor.decompress_single_qr(
                f"A{decompressor.Decompressor.SCHEMA['schema_file']['version']}$B34$C1230$Dv1.3$EName$FTRUE%Z1678$Y14$VTRUE$UO",
                decompressor.QRType.OBJECTIVE,
                {},
            )
        assert "QR missing data fields" in str(excinfo)
        with pytest.raises(IndexError) as excinfo:
            self.test_decompressor.decompress_single_qr(
                f"A{decompressor.Decompressor.SCHEMA['schema_file']['version']}$B34$C1230$Dv1.3$EName$FFALSE%A1678$B1$C1$D10$D3$EFALSE$D10",
                decompressor.QRType.SUBJECTIVE,
                {},
            )
        assert "Incorrect number of teams in Subjective QR" in str(excinfo)
        with pytest.raises(ValueError) as excinfo:
            self.test_decompressor.decompress_single_qr(
                f"A{decompressor.Decompressor.SCHEMA['schema_file']['version']}$B34$C1230$Dv1.3$ENameFTRUE%A1678$B1$C2#A254#A1323",
                decompressor.QRType.SUBJECTIVE,
                {},
            )
        assert "QR missing data fields" in str(excinfo)

    def test_decompress_qrs(self):
        # Expected output from a list containing one obj qr and one subj qr
        expected_output = {
            "unconsolidated_obj_tim": [
                {
                    "schema_version": decompressor.Decompressor.SCHEMA["schema_file"]["version"],
                    "match_number": 34,
                    "override": {},
                    "timestamp": 1230,
                    "match_collection_version_number": "v1.3",
                    "scout_name": "Doozer",
                    "alliance_color_is_red": False,
                    "cage_level": "2",
                    "cage_fail": False,
                    "has_preload": True,
                    "team_number": "1678",
                    "scout_id": 12,
                    "start_position": "2",
                    "timeline": [
                        {"time": 61, "action_type": "auto_drop_coral", "in_teleop": False},
                        {"time": 60, "action_type": "auto_intake_reef_F1", "in_teleop": False},
                    ],
                    "park": False,
                    "ulid": "01GWSXQYKYQQ963QMT77A3NPBZ",
                },
            ],
            "subj_tim": [
                {
                    "schema_version": 1,
                    "match_number": 1,
                    "timestamp": 1212,
                    "match_collection_version_number": "4.8.1",
                    "scout_name": "DOOZER",
                    "alliance_color_is_red": False,
                    "team_number": "7056",
                    "time_left_to_climb": 10,
                    "agility_score": 1,
                    "field_awareness_score": 1,
                    "died": False,
                    "can_cross_barge": False,
                    "hp_team_number": "9496",
                    "was_tippy": True,
                    "hp_from_team": False,
                    "ulid": "01GWSXSNSF93BQZ2GRG0C4E7AC",
                },
                {
                    "schema_version": 1,
                    "match_number": 1,
                    "timestamp": 1212,
                    "match_collection_version_number": "4.8.1",
                    "scout_name": "DOOZER",
                    "alliance_color_is_red": False,
                    "team_number": "9496",
                    "time_left_to_climb": 10,
                    "agility_score": 1,
                    "field_awareness_score": 1,
                    "died": False,
                    "can_cross_barge": True,
                    "hp_team_number": "9496",
                    "was_tippy": False,
                    "hp_from_team": True,
                    "ulid": "01GWSXSNSF93BQZ2GRG0C4E7AC",
                },
                {
                    "schema_version": 1,
                    "match_number": 1,
                    "timestamp": 1212,
                    "match_collection_version_number": "4.8.1",
                    "scout_name": "DOOZER",
                    "alliance_color_is_red": False,
                    "team_number": "6090",
                    "time_left_to_climb": 10,
                    "agility_score": 2,
                    "field_awareness_score": 1,
                    "died": True,
                    "can_cross_barge": False,
                    "was_tippy": False,
                    "hp_from_team": False,
                    "ulid": "01GWSXSNSF93BQZ2GRG0C4E7AC",
                },
            ],
        }
        assert expected_output == self.test_decompressor.decompress_qrs(
            [
                {
                    "data": f"+A{decompressor.Decompressor.SCHEMA['schema_file']['version']}$B34$C1230$Dv1.3$EDoozer$FFALSE%Z1678$Y14$X3$W061AB060AH$SFalse$U2$TFalse$VTRUE$X2$Y12$Z1678",
                    "ulid": "01GWSXQYKYQQ963QMT77A3NPBZ",
                    "override": {},
                },
                {
                    "data": f"*A{decompressor.Decompressor.SCHEMA['schema_file']['version']}$B1$C1212$D4.8.1$EDOOZER$FFALSE%A7056$B1$C1$D10$GFALSE$EFALSE$D10$ITRUE$HFALSE#A9496$B1$C1$D10$GFALSE$ETRUE$D10$IFALSE$HTRUE#A6090$B2$C1$D10$GTRUE$EFALSE$D10$IFALSE$HFALSE",
                    "ulid": "01GWSXSNSF93BQZ2GRG0C4E7AC",
                    "override": {},
                },
            ]
        )

    def test_decompress_pit_data(self):
        raw_obj_pit = {
            "team_number": "9998",
            "drivetrain": 3,
            "weight": 100.2,
            "algae_score_mech": 2,
            "algae_intake_mech": 1,
            "reef_score_ability": 3,
            "can_leave": True,
            "has_processor_mech": True,
        }

        expected_obj_pit = {
            "team_number": "9998",
            "drivetrain": "swerve",
            "weight": 100.2,
            "algae_score_mech": "processor",
            "algae_intake_mech": "none",
            "reef_score_ability": 3,
            "can_leave": True,
            "has_processor_mech": True,
            "coral_intake_mech": None,
            "max_climb": None,
        }
        citrus_seal = {
            "team_number": "1212",
            "drivetrain": 3,
            "can_leave": False,
            "algae_score_mech": 2,
            "algae_intake_mech": 2,
            "reef_score_ability": 1,
            "has_processor_mech": True,
            "weight": 1,
        }
        new_expected_obj_pit = {
            "team_number": "1212",
            "drivetrain": "swerve",
            "can_leave": False,
            "algae_score_mech": "processor",
            "algae_intake_mech": "reef",
            "reef_score_ability": 1,
            "has_processor_mech": True,
            "weight": 1,
            "coral_intake_mech": None,
            "max_climb": None,
        }
        raw2_obj_pit = {
            "team_number": "3448",
            "drivetrain": 2,
            "can_leave": False,
            "algae_score_mech": 0,
            "algae_intake_mech": 0,
            "reef_score_ability": 2,
            "has_processor_mech": False,
            "weight": 1,
        }
        expected2_obj_pit = {
            "team_number": "3448",
            "drivetrain": "mecanum",
            "can_leave": False,
            "algae_score_mech": "no_data",
            "algae_intake_mech": "no_data",
            "reef_score_ability": 2,
            "has_processor_mech": False,
            "coral_intake_mech": None,
            "max_climb": None,
            "weight": 1,
        }
        citrus2_seal = {
            "team_number": "1678",
            "drivetrain": 1,
            "can_leave": True,
            "algae_score_mech": 3,
            "algae_intake_mech": 3,
            "reef_score_ability": 4,
            "has_processor_mech": True,
            "weight": 999,
        }
        new2_expected_obj_pit = {
            "team_number": "1678",
            "drivetrain": "tank",
            "can_leave": True,
            "algae_score_mech": "net",
            "algae_intake_mech": "ground",
            "reef_score_ability": 4,
            "has_processor_mech": True,
            "weight": 999,
            "coral_intake_mech": None,
            "max_climb": None,
        }

        assert (
            self.test_decompressor.decompress_pit_data(raw_obj_pit, "raw_obj_pit")
            == expected_obj_pit
        )
        self.test_server.local_db.insert_documents("raw_obj_pit", expected_obj_pit)
        assert (
            self.test_decompressor.decompress_pit_data(citrus_seal, "raw_obj_pit")
            == new_expected_obj_pit
        )
        assert (
            self.test_decompressor.decompress_pit_data(citrus2_seal, "raw_obj_pit")
            == new2_expected_obj_pit
        )
        self.test_server.local_db.insert_documents("raw_obj_pit", new2_expected_obj_pit)
        assert (
            self.test_decompressor.decompress_pit_data(raw2_obj_pit, "raw_obj_pit")
            == expected2_obj_pit
        )

    def test_decompress_ss_team(self):
        input_1 = {"weaknesses": "steam powered"}
        input_2 = {
            "auto_strategies_team": "goes to center first",
        }
        input_3 = {
            "strengths": "very fast",
            "weaknesses": "tippy",
        }
        input_4 = {
            "strengths": "fast cycles",
        }

        expected_output_1 = {
            "auto_strategies_team": None,
            "can_intake_ground": None,
            "strengths": None,
            "team_notes": None,
            "weaknesses": "steam powered",
        }
        expected_output_2 = {
            "auto_strategies_team": "goes to center first",
            "can_intake_ground": None,
            "strengths": None,
            "team_notes": None,
            "weaknesses": None,
        }
        expected_output_3 = {
            "auto_strategies_team": None,
            "can_intake_ground": None,
            "strengths": "very fast",
            "team_notes": None,
            "weaknesses": "tippy",
        }
        expected_output_4 = {
            "auto_strategies_team": None,
            "can_intake_ground": None,
            "strengths": "fast cycles",
            "team_notes": None,
            "weaknesses": None,
        }

        assert decompressor.Decompressor.decompress_ss_team(input_1) == expected_output_1
        assert decompressor.Decompressor.decompress_ss_team(input_2) == expected_output_2
        assert decompressor.Decompressor.decompress_ss_team(input_3) == expected_output_3
        assert decompressor.Decompressor.decompress_ss_team(input_4) == expected_output_4

    def test_decompress_ss_tim(self):
        # Creates 8 instances and checks them with their expected outputs.
        input_1 = {"played_defense": True}
        input_2 = {"broken_mechanism": "shooter broke"}
        input_3 = {"played_defense": True, "defense_rating": 2}
        input_4 = {"tim_notes": "can shoot from anywhere"}
        input_5 = {"played_defense": True, "broken_mechanism": "shooter broke"}
        input_6 = {"defense_rating": 3, "broken_mechanism": "shooter broke", "played_defense": True}
        input_7 = {"defense_rating": 2}
        input_8 = {"tim_notes": "can shoot from anywhere"}

        excepted_output_1 = {
            "broken_mechanism": None,
            "defense_rating": None,
            "tim_notes": None,
            "played_defense": True,
            "defense_timestamp": None,
            "played_against_defense": None,
            "tim_auto_strategies": None,
        }
        excepted_output_2 = {
            "broken_mechanism": True,
            "defense_rating": None,
            "tim_notes": None,
            "played_defense": None,
            "defense_timestamp": None,
            "played_against_defense": None,
            "tim_auto_strategies": None,
        }

        excepted_output_3 = {
            "broken_mechanism": None,
            "defense_rating": 2,
            "tim_notes": None,
            "played_defense": True,
            "defense_timestamp": None,
            "played_against_defense": None,
            "tim_auto_strategies": None,
        }
        excepted_output_4 = {
            "broken_mechanism": None,
            "defense_rating": None,
            "tim_notes": "can shoot from anywhere",
            "played_defense": None,
            "defense_timestamp": None,
            "played_against_defense": None,
            "tim_auto_strategies": None,
        }
        excepted_output_5 = {
            "broken_mechanism": True,
            "defense_rating": None,
            "tim_notes": None,
            "played_defense": True,
            "defense_timestamp": None,
            "played_against_defense": None,
            "tim_auto_strategies": None,
        }
        excepted_output_6 = {
            "broken_mechanism": True,
            "defense_rating": 3,
            "tim_notes": None,
            "played_defense": True,
            "defense_timestamp": None,
            "played_against_defense": None,
            "tim_auto_strategies": None,
        }
        excepted_output_7 = {
            "broken_mechanism": None,
            "defense_rating": 2,
            "tim_notes": None,
            "played_defense": None,
            "defense_timestamp": None,
            "played_against_defense": None,
            "tim_auto_strategies": None,
        }
        excepted_output_8 = {
            "broken_mechanism": None,
            "defense_rating": None,
            "tim_notes": "can shoot from anywhere",
            "played_defense": None,
            "defense_timestamp": None,
            "played_against_defense": None,
            "tim_auto_strategies": None,
        }

        assert decompressor.Decompressor.decompress_ss_tim(input_1) == excepted_output_1
        assert decompressor.Decompressor.decompress_ss_tim(input_2) == excepted_output_2
        assert decompressor.Decompressor.decompress_ss_tim(input_3) == excepted_output_3
        assert decompressor.Decompressor.decompress_ss_tim(input_4) == excepted_output_4
        assert decompressor.Decompressor.decompress_ss_tim(input_5) == excepted_output_5
        assert decompressor.Decompressor.decompress_ss_tim(input_6) == excepted_output_6
        assert decompressor.Decompressor.decompress_ss_tim(input_7) == excepted_output_7
        assert decompressor.Decompressor.decompress_ss_tim(input_8) == excepted_output_8

    def test_run(self):
        expected_obj = {
            "schema_version": 1,
            "match_number": 34,
            "timestamp": 1230,
            "match_collection_version_number": "V1.3",
            "scout_name": "DOOZER",
            "alliance_color_is_red": False,
            "team_number": "1678",
            "scout_id": 12,
            "start_position": "1",
            "timeline": [
                {"time": 61, "action_type": "auto_drop_coral", "in_teleop": False},
                {"time": 60, "action_type": "auto_intake_reef_F1", "in_teleop": False},
            ],
            "cage_level": "2",
            "cage_fail": False,
            "park": True,
            "has_preload": True,
            "override": {"start_position": "1", "doesnt_exist": 5},
            "ulid": "01GWSXQYKYQQ963QMT77A3NPBZ",
        }
        expected_sbj = [
            {
                "schema_version": 1,
                "match_number": 1,
                "timestamp": 1212,
                "match_collection_version_number": "4.8.1",
                "scout_name": "DOOZER",
                "alliance_color_is_red": False,
                "team_number": "7056",
                "time_left_to_climb": 10,
                "agility_score": 1,
                "field_awareness_score": 1,
                "died": False,
                "hp_team_number": "9496",
                "can_cross_barge": False,
                "was_tippy": True,
                "hp_from_team": False,
                "ulid": "01GWSXSNSF93BQZ2GRG0C4E7AC",
            },
            {
                "schema_version": 1,
                "match_number": 1,
                "timestamp": 1212,
                "match_collection_version_number": "4.8.1",
                "scout_name": "DOOZER",
                "alliance_color_is_red": False,
                "team_number": "9496",
                "time_left_to_climb": 10,
                "agility_score": 1,
                "field_awareness_score": 1,
                "died": False,
                "can_cross_barge": True,
                "hp_team_number": "9496",
                "was_tippy": False,
                "hp_from_team": True,
                "ulid": "01GWSXSNSF93BQZ2GRG0C4E7AC",
            },
            {
                "schema_version": 1,
                "match_number": 1,
                "timestamp": 1212,
                "match_collection_version_number": "4.8.1",
                "scout_name": "DOOZER",
                "alliance_color_is_red": False,
                "team_number": "6090",
                "time_left_to_climb": 10,
                "agility_score": 2,
                "field_awareness_score": 1,
                "died": True,
                "can_cross_barge": False,
                "was_tippy": False,
                "hp_from_team": False,
                "ulid": "01GWSXSNSF93BQZ2GRG0C4E7AC",
            },
        ]

        print(
            self.test_decompressor.decompress_qrs(
                [
                    {
                        "data": f"*A{decompressor.Decompressor.SCHEMA['schema_file']['version']}$B1$C1212$D4.8.1$EDOOZER$FFALSE%A7056$B1$C1$D10$GFALSE$EFALSE$D10$ITRUE$HFALSE#A9496$B1$C1$D10$GFALSE$ETRUE$D10$IFALSE$HTRUE#A6090$B2$C1$D10$GTRUE$EFALSE$D10$IFALSE$HFALSE",
                        "ulid": "01GWSXQYKYQQ963QMT77A3NPBZ",
                        "override": {},
                    },
                ]
            )
        )

        self.test_server.local_db.insert_documents(
            "raw_qr",
            [
                {
                    "data": f"+A{decompressor.Decompressor.SCHEMA['schema_file']['version']}$B101$C7635685774$D4.5.4$ECYRUS$FTRUE%TFALSE$UN$VFALSE$W151BE151BD149AK149AJ149AE149AH149AF149AE146AM146AL146AG146AI146AG135BA134AW133BG130AV125AX123AV119BE119BF105AW104BE104AR098AV089AR076AW073AX065AU064BE064AQ057BF054BE054AQ015BB$STrue$U2$TFalse$VTRUE$X2$Y12$Z1678",
                    "blocklisted": True,
                    "override": {"start_position": "1", "doesnt_exist": 5},
                    "ulid": "01GWEXQY2YQQE63QMT37A3RPBZ",
                    "readable_time": "2023-03-30 19:05:38.821000+00:00",
                },
                {
                    "data": f"+A{decompressor.Decompressor.SCHEMA['schema_file']['version']}$B34$C1230$Dv1.3$EDOOZER$FFALSE%Z1678$Y14$X3$W061AB060AH$STrue$U2$TFalse$VTRUE$X2$Y12$Z1678",
                    "blocklisted": False,
                    "override": {"start_position": "1", "doesnt_exist": 5},
                    "ulid": "01GWSXQYKYQQ963QMT77A3NPBZ",
                    "readable_time": "2023-03-30 19:06:07.725000+00:00",
                },
                {
                    "data": f"*A{decompressor.Decompressor.SCHEMA['schema_file']['version']}$B104$C3158176127$D5.8.1$ECYRUS$FFALSE%A5166$B2$C1$D10$GFALSE$ETRUE$D10$IFALSE$HTRUE#A9418$B2$C1$D10$GFALSE$EFALSE$D10$IFALSE$HFALSE#A3767$B2$C1$D10$GFALSE$EFALSE$D10$ITRUE$HFALSE",
                    "blocklisted": True,
                    "override": {},
                    "ulid": "013WSXENSF9RBQZ2DRG0C4E7AP",
                    "readable_time": "2023-03-30 19:06:28.822000+00:00",
                },
                {
                    "data": f"*A{decompressor.Decompressor.SCHEMA['schema_file']['version']}$B1$C1212$D4.8.1$EDOOZER$FFALSE%A7056$B1$C1$D10$GFALSE$EFALSE$D10$ITRUE$HFALSE#A9496$B1$C1$D10$GFALSE$ETRUE$D10$IFALSE$HTRUE#A6090$B2$C1$D10$GTRUE$EFALSE$D10$IFALSE$HFALSE",
                    "blocklisted": False,
                    "override": {},
                    "ulid": "01GWSXSNSF93BQZ2GRG0C4E7AC",
                    "readable_time": "2023-03-30 19:06:52.936000+00:00",
                },
            ],
        )
        self.test_decompressor.run()
        result_obj = self.test_server.local_db.find("unconsolidated_obj_tim")
        result_sbj = self.test_server.local_db.find("subj_tim")
        assert len(result_obj) == 1
        assert len(result_sbj) == 3
        result_obj = result_obj[0]
        result_obj.pop("_id")
        assert result_obj == expected_obj
        for i, result in enumerate(result_sbj):
            result.pop("_id")
            assert result == expected_sbj[i]

    def test_get_qr_type(self):
        # Test when QRType.OBJECTIVE returns when first character is '+'
        assert decompressor.QRType.OBJECTIVE == self.test_decompressor.get_qr_type("+")
        # Test when QRType.SUBJECTIVE returns when first character is '*'
        assert decompressor.QRType.SUBJECTIVE == self.test_decompressor.get_qr_type("*")

        # Test if correct error runs when neither '+' or '*' is the first character
        with pytest.raises(ValueError) as char_error:
            self.test_decompressor.get_qr_type("a")
        assert "QR type unknown" in str(char_error)
