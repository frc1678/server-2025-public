# Copyright (c) 2023 FRC Team 1678: Citrus Circuits

from unittest import mock

from calculations import base_calculations
from calculations import obj_tims
from calculations import auto_pims
from server import Server
import pytest


class TestAutoPIMCalc:

    obj_teams = [{"team_number": "254"}, {"team_number": "4414"}, {"team_number": "1678"}]

    sim_precisions = [
        {
            "scout_name": "EDWIN",
            "team_number": "254",
            "match_number": 42,
            "sim_precision": -1.0,
            "ignore": 123,
        },
        {
            "scout_name": "RAY",
            "team_number": "254",
            "match_number": 42,
            "sim_precision": 0.5,
            "ignore": 1234,
        },
    ]

    tba_tims = [
        {
            "match_number": 42,
            "team_number": "254",
            "leave": True,
        },
        {
            "match_number": 44,
            "team_number": "4414",
            "leave": True,
        },
        {
            "match_number": 49,
            "team_number": "4414",
            "leave": False,
        },
        {
            "match_number": 1,
            "team_number": "1678",
            "leave": True,
        },
        {
            "match_number": 2,
            "team_number": "1678",
            "leave": False,
        },
    ]
    unconsolidated_obj_tims = [
        {
            "schema_version": 6,
            "serial_number": "STR6",
            "match_number": 42,
            "timestamp": 5,
            "match_collection_version_number": "STR5",
            "scout_name": "AIMEE",
            "alliance_color_is_red": True,
            "team_number": "254",
            "scout_id": 17,
            "timeline": [
                {"in_teleop": False, "time": 150, "action_type": "auto_score_F1_L1"},
                {"in_teleop": False, "time": 149, "action_type": "auto_intake_mark_3_algae"},
                {"in_teleop": False, "time": 148, "action_type": "auto_net"},
                {"in_teleop": False, "time": 147, "action_type": "auto_intake_ground_1_coral"},
                {"in_teleop": False, "time": 146, "action_type": "auto_score_F1_L4"},
                {"in_teleop": False, "time": 145, "action_type": "auto_intake_station_1"},
                {"in_teleop": False, "time": 144, "action_type": "auto_score_F2_L4"},
                {"in_teleop": False, "time": 143, "action_type": "auto_intake_reef_F1"},
                {"in_teleop": True, "time": 135, "action_type": "start_incap_time"},
                {"in_teleop": True, "time": 95, "action_type": "end_incap"},
                {"in_teleop": True, "time": 94, "action_type": "tele_intake_station"},
                {"in_teleop": True, "time": 81, "action_type": "tele_coral_L3"},
                {"in_teleop": True, "time": 75, "action_type": "tele_intake_ground"},
                {"in_teleop": True, "time": 73, "action_type": "tele_net"},
                {"in_teleop": True, "time": 68, "action_type": "tele_intake_ground"},
                {"in_teleop": True, "time": 51, "action_type": "tele_coral_L2"},
                {"in_teleop": True, "time": 45, "action_type": "tele_intake_reef"},
                {"in_teleop": True, "time": 35, "action_type": "start_incap_time"},
                {"in_teleop": True, "time": 2, "action_type": "end_incap"},
            ],
            "start_position": "1",
            "has_preload": True,
            "override": {"failed_scores": 0},
        },
        {
            "schema_version": 6,
            "serial_number": "STR2",
            "match_number": 42,
            "timestamp": 6,
            "match_collection_version_number": "STR1",
            "scout_name": "RAY",
            "alliance_color_is_red": True,
            "team_number": "254",
            "scout_id": 17,
            "timeline": [
                {"in_teleop": False, "time": 150, "action_type": "auto_score_F1_L2"},
                {"in_teleop": False, "time": 149, "action_type": "auto_intake_mark_3_coral"},
                {"in_teleop": False, "time": 148, "action_type": "auto_net"},
                {"in_teleop": False, "time": 147, "action_type": "auto_intake_ground_1_algae"},
                {"in_teleop": False, "time": 146, "action_type": "auto_score_F1_L4"},
                {"in_teleop": False, "time": 145, "action_type": "auto_intake_station_1"},
                {"in_teleop": False, "time": 144, "action_type": "auto_score_F2_L3"},
                {"in_teleop": True, "time": 135, "action_type": "start_incap_time"},
                {"in_teleop": True, "time": 95, "action_type": "end_incap"},
                {"in_teleop": True, "time": 94, "action_type": "tele_intake_station"},
                {"in_teleop": True, "time": 81, "action_type": "tele_coral_L3"},
                {"in_teleop": True, "time": 75, "action_type": "tele_intake_ground"},
                {"in_teleop": True, "time": 73, "action_type": "tele_net"},
                {"in_teleop": True, "time": 68, "action_type": "tele_intake_ground"},
                {"in_teleop": True, "time": 51, "action_type": "tele_coral_L2"},
                {"in_teleop": True, "time": 45, "action_type": "tele_intake_reef"},
                {"in_teleop": True, "time": 35, "action_type": "start_incap_time"},
                {"in_teleop": True, "time": 2, "action_type": "end_incap"},
            ],
            "start_position": "2",
            "has_preload": True,
            "override": {"failed_scores": 0},
        },
        {
            "schema_version": 6,
            "serial_number": "STR5",
            "match_number": 42,
            "timestamp": 11,
            "match_collection_version_number": "STR6",
            "scout_name": "ADRIAN",
            "alliance_color_is_red": False,
            "team_number": "254",
            "scout_id": 17,
            "timeline": [
                {"in_teleop": False, "time": 150, "action_type": "auto_score_F1_L1"},
                {"in_teleop": False, "time": 149, "action_type": "auto_intake_mark_3_algae"},
                {"in_teleop": False, "time": 148, "action_type": "auto_net"},
                {"in_teleop": False, "time": 147, "action_type": "auto_intake_ground_1_algae"},
                {"in_teleop": False, "time": 146, "action_type": "auto_processor"},
                {"in_teleop": False, "time": 145, "action_type": "auto_intake_station_1"},
                {"in_teleop": False, "time": 144, "action_type": "fail_auto_score_F2_L3"},
                {"in_teleop": True, "time": 135, "action_type": "start_incap_time"},
                {"in_teleop": True, "time": 95, "action_type": "end_incap"},
                {"in_teleop": True, "time": 94, "action_type": "tele_intake_station"},
                {"in_teleop": True, "time": 81, "action_type": "tele_coral_L3"},
                {"in_teleop": True, "time": 75, "action_type": "tele_intake_ground"},
                {"in_teleop": True, "time": 73, "action_type": "tele_net"},
                {"in_teleop": True, "time": 68, "action_type": "tele_intake_ground"},
                {"in_teleop": True, "time": 51, "action_type": "tele_coral_L2"},
                {"in_teleop": True, "time": 45, "action_type": "tele_intake_reef"},
                {"in_teleop": True, "time": 35, "action_type": "start_incap_time"},
                {"in_teleop": True, "time": 2, "action_type": "end_incap"},
            ],
            "start_position": "1",
            "has_preload": True,
            "override": {"failed_scores": 0},
        },
    ]
    calculated_obj_tims = [
        {
            "match_number": 42,
            "team_number": "254",
            "has_preload": True,
            "start_position": "1",
            "auto_net": 1,
            "auto_processor": 1,
            "auto_coral_L1": 1,
            "auto_coral_L2": 0,
            "auto_coral_L3": 0,
            "auto_coral_L4": 1,
            "auto_intake_ground_coral": 0,
            "auto_intake_ground_algae": 2,
            "auto_intake_station": 1,
            "auto_intake_reef": 0,
            "tele_net": 1,
            "tele_processor": 0,
            "tele_coral_L1": 0,
            "tele_coral_L2": 1,
            "tele_coral_L3": 1,
            "tele_coral_L4": 0,
            "tele_intake_station": 1,
            "tele_intake_ground_coral": 1,
            "tele_intake_ground_algae": 1,
            "tele_intake_reef": 1,
            "auto_total_intakes_ground": 2,
            "auto_total_intakes": 3,
            "tele_total_intakes_ground": 2,
            "tele_total_intakes": 4,
            "auto_total_pieces": 4,
            "tele_total_pieces": 3,
            "total_pieces": 7,
            "total_intakes": 7,
            "failed_scores": 0,
            "tele_incap": 73,
        },
        {
            "match_number": 44,
            "team_number": "359",
            "has_preload": True,
            "start_position": "2",
            "auto_net": 0,
            "auto_processor": 0,
            "auto_coral_L1": 1,
            "auto_coral_L2": 0,
            "auto_coral_L3": 1,
            "auto_coral_L4": 1,
            "auto_intake_ground_coral": 1,
            "auto_intake_ground_algae": 2,
            "auto_intake_station": 1,
            "auto_intake_reef": 0,
            "tele_net": 6,
            "tele_processor": 0,
            "tele_coral_L1": 0,
            "tele_coral_L2": 1,
            "tele_coral_L3": 1,
            "tele_coral_L4": 0,
            "tele_intake_station": 1,
            "tele_intake_ground_coral": 1,
            "tele_intake_ground_algae": 5,
            "tele_intake_reef": 1,
            "auto_total_intakes_ground": 3,
            "auto_total_intakes": 4,
            "tele_total_intakes_ground": 6,
            "tele_total_intakes": 7,
            "auto_total_pieces": 3,
            "tele_total_pieces": 8,
            "total_pieces": 11,
            "total_intakes": 11,
            "failed_scores": 0,
            "tele_incap": 0,
        },
    ]
    expected_unconsolidated_auto_timelines = [
        [
            {"in_teleop": False, "time": 150, "action_type": "auto_score_F1_L1"},
            {"in_teleop": False, "time": 149, "action_type": "auto_intake_mark_3_algae"},
            {"in_teleop": False, "time": 148, "action_type": "auto_net"},
            {"in_teleop": False, "time": 147, "action_type": "auto_intake_ground_1_coral"},
            {"in_teleop": False, "time": 146, "action_type": "auto_score_F1_L4"},
            {"in_teleop": False, "time": 145, "action_type": "auto_intake_station_1"},
            {"in_teleop": False, "time": 144, "action_type": "auto_score_F2_L4"},
            {"in_teleop": False, "time": 143, "action_type": "auto_intake_reef_F1"},
        ],
        [
            {"in_teleop": False, "time": 150, "action_type": "auto_score_F1_L2"},
            {"in_teleop": False, "time": 149, "action_type": "auto_intake_mark_3_coral"},
            {"in_teleop": False, "time": 148, "action_type": "auto_net"},
            {"in_teleop": False, "time": 147, "action_type": "auto_intake_ground_1_algae"},
            {"in_teleop": False, "time": 146, "action_type": "auto_score_F1_L4"},
            {"in_teleop": False, "time": 145, "action_type": "auto_intake_station_1"},
            {"in_teleop": False, "time": 144, "action_type": "auto_score_F2_L3"},
        ],
        [
            {"in_teleop": False, "time": 150, "action_type": "auto_score_F1_L1"},
            {"in_teleop": False, "time": 149, "action_type": "auto_intake_mark_3_algae"},
            {"in_teleop": False, "time": 148, "action_type": "auto_net"},
            {"in_teleop": False, "time": 147, "action_type": "auto_intake_ground_1_algae"},
            {"in_teleop": False, "time": 146, "action_type": "auto_processor"},
            {"in_teleop": False, "time": 145, "action_type": "auto_intake_station_1"},
            {"in_teleop": False, "time": 144, "action_type": "fail_auto_score_F2_L3"},
        ],
    ]
    expected_consolidated_timelines = [
        {"in_teleop": False, "time": 150, "action_type": "auto_score_F1_L1"},
        {"in_teleop": False, "time": 149, "action_type": "auto_intake_mark_3_algae"},
        {"in_teleop": False, "time": 148, "action_type": "auto_net"},
        {"in_teleop": False, "time": 147, "action_type": "auto_intake_ground_1_algae"},
        {"in_teleop": False, "time": 146, "action_type": "auto_processor"},
        {"in_teleop": False, "time": 145, "action_type": "auto_intake_station_1"},
        {"in_teleop": False, "time": 144, "action_type": "auto_score_F2_L3"},
    ]
    expected_tim_fields = {
        "start_position": "1",
        "has_preload": True,
        "leave": True,
    }
    expected_auto_pim = [
        {
            "match_number": 42,
            "team_number": "254",
            "start_position": "1",
            "has_preload": True,
            "score_1": "reef_F1_L1",
            "intake_position_1": "mark_3_algae",
            "score_2": "net",
            "intake_position_2": "ground_1_algae",
            "score_3": "processor",
            "intake_position_3": "station_1",
            "score_4": "reef_F2_L3",
            "intake_position_4": "none",
            "intake_position_5": "none",
            "intake_position_6": "none",
            "intake_position_7": "none",
            "intake_position_8": "none",
            "intake_position_9": "none",
            "intake_position_10": "none",
            "intake_position_11": "none",
            "intake_position_12": "none",
            "is_compatible": False,
            "score_5": "none",
            "score_6": "none",
            "score_7": "none",
            "score_8": "none",
            "score_9": "none",
            "score_10": "none",
            "score_11": "none",
            "score_12": "none",
            "score_13": "none",
            "leave": True,
            "auto_timeline": [
                {"in_teleop": False, "time": 150, "action_type": "auto_score_F1_L1"},
                {"in_teleop": False, "time": 149, "action_type": "auto_intake_mark_3_algae"},
                {"in_teleop": False, "time": 148, "action_type": "auto_net"},
                {"in_teleop": False, "time": 147, "action_type": "auto_intake_ground_1_algae"},
                {"in_teleop": False, "time": 146, "action_type": "auto_processor"},
                {"in_teleop": False, "time": 145, "action_type": "auto_intake_station_1"},
                {"in_teleop": False, "time": 144, "action_type": "auto_score_F2_L3"},
            ],
            "match_numbers_played": [],
            "path_number": 0,
            "num_matches_ran": 0,
            "is_sus": True,
        }
    ]

    @mock.patch.object(
        base_calculations.BaseCalculations, "get_teams_list", return_value=["3", "254"]
    )
    def setup_method(self, method, get_teams_list_dummy):
        with mock.patch(
            "doozernet_communicator.check_model_availability", return_value=None
        ), mock.patch("utils.get_match_schedule", return_value=[]), mock.patch(
            "utils.get_team_list", return_value=[]
        ):
            self.test_server = Server()
        self.test_calculator = auto_pims.AutoPIMCalc(self.test_server)
        # Insert test data into database for testing
        self.test_server.local_db.insert_documents("obj_tim", self.calculated_obj_tims)
        self.test_server.local_db.insert_documents(
            "unconsolidated_obj_tim", self.unconsolidated_obj_tims
        )
        self.test_server.local_db.insert_documents("tba_tim", self.tba_tims)
        self.test_server.local_db.insert_documents("obj_team", self.obj_teams)
        self.test_server.local_db.insert_documents("sim_precision", self.sim_precisions)

    def test___init__(self):
        assert self.test_calculator.server == self.test_server
        assert self.test_calculator.watched_collections == [
            "unconsolidated_obj_tim",
            "sim_precision",
        ]

    def test_get_unconsolidated_auto_timelines(self):
        unconsolidated_auto_timelines = self.test_calculator.get_unconsolidated_auto_timelines(
            self.unconsolidated_obj_tims
        )
        assert unconsolidated_auto_timelines == (self.expected_unconsolidated_auto_timelines, 1)

    def test_consolidate_timelines(self):
        consolidated_timeline, is_sus = self.test_calculator.consolidate_timelines(
            self.expected_unconsolidated_auto_timelines, True
        )
        assert consolidated_timeline == self.expected_consolidated_timelines

    def test_get_consolidated_tim_fields(self):
        tim_fields = self.test_calculator.get_consolidated_tim_fields(self.calculated_obj_tims[0])
        assert tim_fields == self.expected_tim_fields

    def test_create_auto_fields(self):
        assert self.test_calculator.create_auto_fields(
            {
                "match_number": 1,
                "team_number": "1678",
                "has_preload": True,
                "auto_timeline": [
                    {"in_teleop": False, "time": 140, "action_type": "auto_score_F2_L2"},
                    {"in_teleop": False, "time": 139, "action_type": "auto_intake_station_2"},
                    {"in_teleop": False, "time": 138, "action_type": "auto_score_F5_L4"},
                ],
                "leave": True,
            }
        ) == {
            "score_1": "reef_F2_L2",
            "intake_position_1": "station_2",
            "score_2": "reef_F5_L4",
            "intake_position_2": "none",
            "intake_position_3": "none",
            "intake_position_4": "none",
            "intake_position_5": "none",
            "intake_position_6": "none",
            "intake_position_7": "none",
            "intake_position_8": "none",
            "intake_position_9": "none",
            "intake_position_10": "none",
            "intake_position_11": "none",
            "intake_position_12": "none",
            "score_3": "none",
            "score_4": "none",
            "score_5": "none",
            "score_6": "none",
            "score_7": "none",
            "score_8": "none",
            "score_9": "none",
            "score_10": "none",
            "score_11": "none",
            "score_12": "none",
            "score_13": "none",
        }

        assert self.test_calculator.create_auto_fields(
            {
                "match_number": 2,
                "team_number": "1678",
                "auto_timeline": [
                    {"in_teleop": False, "time": 140, "action_type": "auto_score_F6_L3"},
                    {"in_teleop": False, "time": 139, "action_type": "auto_intake_reef_F2"},
                    {"in_teleop": False, "time": 138, "action_type": "auto_processor"},
                    {"in_teleop": False, "time": 139, "action_type": "auto_intake_mark_1_coral"},
                    {"in_teleop": False, "time": 139, "action_type": "auto_score_F1_L1"},
                ],
                "has_preload": True,
                "leave": True,
            }
        ) == {
            "score_1": "reef_F6_L3",
            "intake_position_1": "intake_reef_2",
            "score_2": "processor",
            "intake_position_2": "mark_1_coral",
            "score_3": "reef_F1_L1",
            "intake_position_3": "none",
            "intake_position_4": "none",
            "intake_position_5": "none",
            "intake_position_6": "none",
            "intake_position_7": "none",
            "intake_position_8": "none",
            "intake_position_9": "none",
            "intake_position_10": "none",
            "intake_position_11": "none",
            "intake_position_12": "none",
            "score_4": "none",
            "score_5": "none",
            "score_6": "none",
            "score_7": "none",
            "score_8": "none",
            "score_9": "none",
            "score_10": "none",
            "score_11": "none",
            "score_12": "none",
            "score_13": "none",
        }

        assert self.test_calculator.create_auto_fields(
            {"team_number": "4414", "match_number": 49, "auto_timeline": []}
        ) == {
            "score_1": "none",
            "score_2": "none",
            "intake_position_1": "none",
            "intake_position_2": "none",
            "score_3": "none",
            "intake_position_3": "none",
            "intake_position_4": "none",
            "intake_position_5": "none",
            "intake_position_6": "none",
            "intake_position_7": "none",
            "intake_position_8": "none",
            "intake_position_9": "none",
            "intake_position_10": "none",
            "intake_position_11": "none",
            "intake_position_12": "none",
            "score_4": "none",
            "score_5": "none",
            "score_6": "none",
            "score_7": "none",
            "score_8": "none",
            "score_9": "none",
            "score_10": "none",
            "score_11": "none",
            "score_12": "none",
            "score_13": "none",
        }

    def test_calculate_auto_pim(self):
        calculated_auto_paths = self.test_calculator.calculate_auto_pims(
            [{"match_number": 42, "team_number": "254"}]
        )
        assert len(calculated_auto_paths) == 1
        assert len(self.expected_auto_pim) == 1
        assert calculated_auto_paths[0] == self.expected_auto_pim[0]

    def test_run(self):
        # Delete any data that is already in the database collections
        self.test_server.local_db.delete_data("auto_pim")
        self.test_server.local_db.delete_data("unconsolidated_obj_tim")
        self.test_server.local_db.delete_data("obj_tim")
        self.test_server.local_db.delete_data("sim_precision")
        # Insert test data for the run function
        self.test_server.local_db.insert_documents(
            "unconsolidated_obj_tim", self.unconsolidated_obj_tims
        )
        self.test_server.local_db.insert_documents("obj_tim", self.calculated_obj_tims)
        self.test_server.local_db.insert_documents("sim_precision", self.sim_precisions)

        self.test_calculator.run()
        result = self.test_server.local_db.find("auto_pim")

        for document in result:
            del document["_id"]

        assert result == self.expected_auto_pim
