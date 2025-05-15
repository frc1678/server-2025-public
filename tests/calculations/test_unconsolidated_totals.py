# Copyright (c) 2024 FRC Team 1678: Citrus Circuits


from unittest import mock


import logging


with mock.patch("logging.getLogger", side_effect=logging.getLogger):
    with mock.patch("utils.confirm_comp", side_effect=mock.MagicMock()):
        from calculations import base_calculations
        from calculations import unconsolidated_totals
        from server import Server
import pytest
from unittest.mock import patch


@pytest.mark.clouddb
class TestUnconsolidatedTotals:
    tba_test_data = [
        {
            "match_number": 42,
            "actual_time": 1100291640,
            "comp_level": "qm",
            "score_breakdown": {
                "blue": {
                    "foulPoints": 8,
                    "autoMobilityPoints": 15,
                    "autoGamePiecePoints": 12,
                    "teleopGamePiecePoints": 40,
                    "autoCommunity": {
                        "B": [
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                        ],
                        "M": [
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                        ],
                        "T": [
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "Cube",
                            "Cone",
                        ],
                    },
                    "teleopCommunity": {
                        "B": [
                            "Cone",
                            "Cube",
                            "None",
                            "Cone",
                            "Cube",
                            "Cube",
                            "Cube",
                            "Cube",
                            "None",
                        ],
                        "M": [
                            "None",
                            "None",
                            "None",
                            "Cone",
                            "Cube",
                            "None",
                            "None",
                            "None",
                            "None",
                        ],
                        "T": [
                            "Cone",
                            "Cube",
                            "Cone",
                            "None",
                            "None",
                            "None",
                            "Cone",
                            "Cube",
                            "Cone",
                        ],
                    },
                },
                "red": {
                    "foulPoints": 10,
                    "autoMobilityPoints": 0,
                    "autoGamePiecePoints": 6,
                    "teleopGamePiecePoints": 63,
                    "autoCommunity": {
                        "B": [
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                        ],
                        "M": [
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                        ],
                        "T": [
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "None",
                            "Cone",
                        ],
                    },
                    "teleopCommunity": {
                        "B": [
                            "Cone",
                            "Cube",
                            "Cube",
                            "Cone",
                            "Cube",
                            "Cube",
                            "Cube",
                            "Cube",
                            "None",
                        ],
                        "M": [
                            "None",
                            "None",
                            "Cone",
                            "Cone",
                            "Cube",
                            "None",
                            "None",
                            "None",
                            "None",
                        ],
                        "T": [
                            "Cone",
                            "Cube",
                            "Cone",
                            "Cone",
                            "Cube",
                            "Cone",
                            "Cone",
                            "Cube",
                            "Cone",
                        ],
                    },
                },
            },
            "alliances": {
                "blue": {
                    "team_keys": [
                        "frc254",
                    ]
                },
                "red": {
                    "team_keys": [
                        "frc254",
                    ]
                },
            },
        },
    ]
    scout_precision_data = {
        "EDWIN": 3,
        "RAY": 2,
        "ADRIAN": 1,
    }
    unconsolidated_tims = [
        {
            "schema_version": 1,
            "serial_number": "STR6",
            "match_number": 42,
            "timestamp": 5,
            "match_collection_version_number": "STR5",
            "scout_name": "EDWIN",
            "alliance_color_is_red": True,
            "team_number": "254",
            "scout_id": 17,
            "timeline": [
                {"in_teleop": False, "time": 150, "action_type": "auto_score_F1_L4"},
                {"in_teleop": False, "time": 149, "action_type": "auto_intake_ground_1_coral"},
                {"in_teleop": False, "time": 148, "action_type": "auto_score_F2_L3"},
                {"in_teleop": False, "time": 147, "action_type": "auto_intake_reef_F6"},
                {"in_teleop": False, "time": 146, "action_type": "auto_processor"},
                {"in_teleop": True, "time": 135, "action_type": "to_teleop"},
                {"in_teleop": True, "time": 127, "action_type": "end_incap"},
                {"in_teleop": True, "time": 117, "action_type": "fail"},
                {"in_teleop": True, "time": 117, "action_type": "tele_coral_L2"},
                {"in_teleop": True, "time": 117, "action_type": "tele_intake_station"},
                {"in_teleop": True, "time": 110, "action_type": "tele_coral_L4"},
                {"in_teleop": True, "time": 105, "action_type": "tele_coral_L3"},
                {"in_teleop": True, "time": 94, "action_type": "tele_coral_L2"},
                {"in_teleop": True, "time": 81, "action_type": "tele_coral_L1"},
                {"in_teleop": True, "time": 75, "action_type": "tele_net"},
                {"in_teleop": True, "time": 73, "action_type": "tele_processor"},
                {"in_teleop": True, "time": 68, "action_type": "tele_coral_L4"},
                {"in_teleop": True, "time": 51, "action_type": "tele_coral_L3"},
                {"in_teleop": True, "time": 45, "action_type": "tele_coral_L2"},
                {"in_teleop": True, "time": 35, "action_type": "start_incap"},
                {"in_teleop": True, "time": 2, "action_type": "end_incap"},
                {"in_teleop": True, "time": 0, "action_type": "to_endgame"},
            ],
            "cage_level": "N",
            "park": True,
            "cage_fail": False,
            "start_position": "1",
            "has_preload": True,
            "override": {"tele_intake_reef": 42},
        },
        {
            "schema_version": 1,
            "serial_number": "STR6",
            "match_number": 42,
            "timestamp": 5,
            "match_collection_version_number": "STR5",
            "scout_name": "RAY",
            "alliance_color_is_red": True,
            "team_number": "254",
            "scout_id": 17,
            "timeline": [
                {"in_teleop": False, "time": 150, "action_type": "auto_score_F1_L4"},
                {"in_teleop": False, "time": 149, "action_type": "auto_intake_ground_1_coral"},
                {"in_teleop": False, "time": 148, "action_type": "auto_score_F2_L3"},
                {"in_teleop": False, "time": 147, "action_type": "auto_intake_reef_F6"},
                {"in_teleop": False, "time": 146, "action_type": "auto_processor"},
                {"in_teleop": True, "time": 135, "action_type": "to_teleop"},
                {"in_teleop": True, "time": 127, "action_type": "end_incap"},
                {"in_teleop": True, "time": 117, "action_type": "fail"},
                {"in_teleop": True, "time": 117, "action_type": "tele_coral_L2"},
                {"in_teleop": True, "time": 117, "action_type": "tele_intake_station"},
                {"in_teleop": True, "time": 110, "action_type": "tele_coral_L4"},
                {"in_teleop": True, "time": 105, "action_type": "tele_coral_L3"},
                {"in_teleop": True, "time": 94, "action_type": "tele_coral_L2"},
                {"in_teleop": True, "time": 81, "action_type": "tele_coral_L1"},
                {"in_teleop": True, "time": 75, "action_type": "tele_net"},
                {"in_teleop": True, "time": 73, "action_type": "tele_processor"},
                {"in_teleop": True, "time": 68, "action_type": "tele_coral_L4"},
                {"in_teleop": True, "time": 51, "action_type": "tele_coral_L3"},
                {"in_teleop": True, "time": 45, "action_type": "tele_coral_L2"},
                {"in_teleop": True, "time": 35, "action_type": "start_incap"},
                {"in_teleop": True, "time": 2, "action_type": "end_incap"},
                {"in_teleop": True, "time": 0, "action_type": "to_endgame"},
            ],
            "cage_level": "S",
            "park": False,
            "cage_fail": False,
            "start_position": "1",
            "has_preload": True,
            "override": {"tele_net": 12},
        },
        {
            "schema_version": 1,
            "serial_number": "STR6",
            "match_number": 42,
            "timestamp": 5,
            "match_collection_version_number": "STR5",
            "scout_name": "ADRIAN",
            "alliance_color_is_red": True,
            "team_number": "254",
            "scout_id": 17,
            "timeline": [
                {"in_teleop": False, "time": 150, "action_type": "auto_score_F1_L4"},
                {"in_teleop": False, "time": 149, "action_type": "auto_intake_ground_1_coral"},
                {"in_teleop": False, "time": 148, "action_type": "auto_score_F2_L3"},
                {"in_teleop": False, "time": 147, "action_type": "auto_intake_reef_F6"},
                {"in_teleop": False, "time": 146, "action_type": "auto_processor"},
                {"in_teleop": True, "time": 135, "action_type": "to_teleop"},
                {"in_teleop": True, "time": 127, "action_type": "end_incap"},
                {"in_teleop": True, "time": 117, "action_type": "fail"},
                {"in_teleop": True, "time": 117, "action_type": "tele_coral_L2"},
                {"in_teleop": True, "time": 117, "action_type": "tele_intake_station"},
                {"in_teleop": True, "time": 110, "action_type": "tele_coral_L4"},
                {"in_teleop": True, "time": 105, "action_type": "tele_coral_L3"},
                {"in_teleop": True, "time": 94, "action_type": "tele_coral_L2"},
                {"in_teleop": True, "time": 81, "action_type": "tele_coral_L1"},
                {"in_teleop": True, "time": 75, "action_type": "tele_net"},
                {"in_teleop": True, "time": 73, "action_type": "tele_processor"},
                {"in_teleop": True, "time": 68, "action_type": "tele_coral_L4"},
                {"in_teleop": True, "time": 51, "action_type": "tele_coral_L3"},
                {"in_teleop": True, "time": 45, "action_type": "tele_coral_L2"},
                {"in_teleop": True, "time": 35, "action_type": "start_incap"},
                {"in_teleop": True, "time": 2, "action_type": "end_incap"},
                {"in_teleop": True, "time": 0, "action_type": "to_endgame"},
            ],
            "cage_level": "D",
            "park": False,
            "cage_fail": False,
            "start_position": "1",
            "has_preload": True,
            "override": {"tele_intake_reef": 42},
        },
    ]
    fake_match_schedule = {"42": {"teams": [{"number": "254", "color": "red"}]}}

    @mock.patch.object(
        base_calculations.BaseCalculations, "get_teams_list", return_value=["3", "254", "1"]
    )
    def setup_method(self, method, get_teams_list_dummy):
        with patch("doozernet_communicator.check_model_availability", return_value=None), patch(
            "utils.get_match_schedule", return_value=self.fake_match_schedule
        ):
            self.test_server = Server()
        self.test_calculator = unconsolidated_totals.UnconsolidatedTotals(self.test_server)

    def test_merge_timeline_actions(self):
        unconsolidated_tims = [
            {
                "team_number": "1678",
                "match_number": 40,
                "alliance_color_is_red": True,
                "timeline": [
                    {"in_teleop": False, "time": 150, "action_type": "auto_score_F5_L4"},
                    {"in_teleop": False, "time": 149, "action_type": "auto_intake_mark_1_coral"},
                    {"in_teleop": False, "time": 148, "action_type": "auto_score_F3_L2"},
                    {"in_teleop": False, "time": 147, "action_type": "auto_intake_reef_F3"},
                    {"in_teleop": False, "time": 146, "action_type": "auto_net"},
                    {"in_teleop": False, "time": 135, "action_type": "auto_intake_station_2"},
                    {"in_teleop": False, "time": 69, "action_type": "auto_score_F4_L3"},
                ],
            }
        ]
        assert self.test_calculator.merge_timeline_actions(unconsolidated_tims) == [
            {
                "team_number": "1678",
                "match_number": 40,
                "alliance_color_is_red": True,
                "timeline": [
                    {"in_teleop": False, "time": 150, "action_type": "auto_coral_L4"},
                    {"in_teleop": False, "time": 149, "action_type": "auto_intake_ground_coral"},
                    {"in_teleop": False, "time": 148, "action_type": "auto_coral_L2"},
                    {"in_teleop": False, "time": 147, "action_type": "auto_intake_reef"},
                    {"in_teleop": False, "time": 146, "action_type": "auto_net"},
                    {"in_teleop": False, "time": 135, "action_type": "auto_intake_station"},
                    {"in_teleop": False, "time": 69, "action_type": "auto_coral_L3"},
                ],
            }
        ]

    def test_filter_timeline_actions(self):
        actions = self.test_calculator.filter_timeline_actions(self.unconsolidated_tims[0])
        assert actions == [
            {"in_teleop": False, "time": 150, "action_type": "auto_score_F1_L4"},
            {"in_teleop": False, "time": 149, "action_type": "auto_intake_ground_1_coral"},
            {"in_teleop": False, "time": 148, "action_type": "auto_score_F2_L3"},
            {"in_teleop": False, "time": 147, "action_type": "auto_intake_reef_F6"},
            {"in_teleop": False, "time": 146, "action_type": "auto_processor"},
            {"in_teleop": True, "time": 135, "action_type": "to_teleop"},
            {"in_teleop": True, "time": 127, "action_type": "end_incap"},
            {"in_teleop": True, "time": 117, "action_type": "fail"},
            {"in_teleop": True, "time": 117, "action_type": "tele_coral_L2"},
            {"in_teleop": True, "time": 117, "action_type": "tele_intake_station"},
            {"in_teleop": True, "time": 110, "action_type": "tele_coral_L4"},
            {"in_teleop": True, "time": 105, "action_type": "tele_coral_L3"},
            {"in_teleop": True, "time": 94, "action_type": "tele_coral_L2"},
            {"in_teleop": True, "time": 81, "action_type": "tele_coral_L1"},
            {"in_teleop": True, "time": 75, "action_type": "tele_net"},
            {"in_teleop": True, "time": 73, "action_type": "tele_processor"},
            {"in_teleop": True, "time": 68, "action_type": "tele_coral_L4"},
            {"in_teleop": True, "time": 51, "action_type": "tele_coral_L3"},
            {"in_teleop": True, "time": 45, "action_type": "tele_coral_L2"},
            {"in_teleop": True, "time": 35, "action_type": "start_incap"},
            {"in_teleop": True, "time": 2, "action_type": "end_incap"},
            {"in_teleop": True, "time": 0, "action_type": "to_endgame"},
        ]

    def test_calculate_expected_fields(self):
        expected_results = {
            "expected_cycle_time": 2.6530612244897958,
            "expected_cycles": 24.5,
        }
        # Fails must be calculated first in order for the calculation to work
        unconsolidated_total = [
            {
                "timeline": [
                    {"in_teleop": False, "time": 150, "action_type": "auto_score_F1_L4"},
                    {"in_teleop": False, "time": 149, "action_type": "auto_intake_ground_1_coral"},
                    {"in_teleop": False, "time": 148, "action_type": "auto_score_F2_L3"},
                    {"in_teleop": False, "time": 147, "action_type": "auto_intake_reef_F6"},
                    {"in_teleop": False, "time": 146, "action_type": "auto_processor"},
                    {"in_teleop": True, "time": 135, "action_type": "to_teleop"},
                    {"in_teleop": True, "time": 117, "action_type": "tele_intake_station"},
                    {"in_teleop": True, "time": 110, "action_type": "tele_coral_L4"},
                    {"in_teleop": True, "time": 117, "action_type": "tele_intake_station"},
                    {"in_teleop": True, "time": 105, "action_type": "tele_coral_L3"},
                    {"in_teleop": True, "time": 117, "action_type": "tele_intake_station"},
                    {"in_teleop": True, "time": 94, "action_type": "tele_coral_L2"},
                    {"in_teleop": True, "time": 117, "action_type": "tele_intake_station"},
                    {"in_teleop": True, "time": 81, "action_type": "tele_coral_L1"},
                    {"in_teleop": True, "time": 117, "action_type": "tele_intake_reef"},
                    {"in_teleop": True, "time": 75, "action_type": "tele_net"},
                    {"in_teleop": True, "time": 73, "action_type": "tele_processor"},
                    {"in_teleop": True, "time": 117, "action_type": "tele_intake_station"},
                    {"in_teleop": True, "time": 68, "action_type": "tele_coral_L4"},
                    {"in_teleop": True, "time": 117, "action_type": "tele_intake_station"},
                    {"in_teleop": True, "time": 51, "action_type": "tele_coral_L3"},
                    {"in_teleop": True, "time": 117, "action_type": "tele_intake_station"},
                    {"in_teleop": True, "time": 45, "action_type": "tele_coral_L2"},
                    {"in_teleop": True, "time": 35, "action_type": "start_incap"},
                    {"in_teleop": True, "time": 2, "action_type": "end_incap"},
                    {"in_teleop": True, "time": 0, "action_type": "to_endgame"},
                ]
            }
        ]
        tim_totals = {
            "tele_net": 0,
            "tele_processor": 1,
            "tele_coral_L1": 2,
            "tele_coral_L2": 0,
            "tele_coral_L3": 1,
            "tele_coral_L4": 6,
            "tele_fail_net": 5,
            "tele_fail_processor": 1,
            "tele_fail_coral_L1": 2,
            "tele_fail_coral_L2": 3,
            "tele_fail_coral_L3": 1,
            "tele_fail_coral_L4": 2,
            "tele_drop_coral": 1,
            "tele_drop_algae": 1,
        }
        after_fails = self.test_calculator.score_fail_type(unconsolidated_total)
        result = self.test_calculator.calculate_expected_fields(after_fails[0], tim_totals)
        assert result == expected_results

    def test_count_timeline_actions(self):
        action_num = self.test_calculator.count_timeline_actions(self.unconsolidated_tims[0])
        assert action_num == 22

    def test_score_fail_type(self):
        score_fails = self.test_calculator.score_fail_type(self.unconsolidated_tims)
        assert score_fails[2]["timeline"][8]["action_type"] == "tele_fail_coral_L2"

    def test_calculate_unconsolidated_tims(self):
        self.test_server.local_db.insert_documents(
            "unconsolidated_obj_tim", self.unconsolidated_tims
        )
        with patch("tba_communicator.tba_request", return_value=self.tba_test_data):
            with patch(
                "calculations.unconsolidated_totals.UnconsolidatedTotals.pull_spr",
                return_value=self.scout_precision_data,
            ), patch("tba_communicator.tba_request"):
                self.test_calculator.run()
        result = self.test_server.local_db.find("unconsolidated_totals")
        assert len(result) == 3
        calculated_tim = result[0]
        del calculated_tim["_id"]
        assert calculated_tim == {
            "scout_name": "EDWIN",
            "match_number": 42,
            "team_number": "254",
            "alliance_color_is_red": True,
            "scored_preload": True,
            "auto_net": 0,
            "auto_total_intakes": 2,
            "auto_processor": 1,
            "auto_coral_L1": 0,
            "auto_coral_L2": 0,
            "auto_coral_L3": 1,
            "auto_coral_L4": 1,
            "auto_fail_net": 0,
            "auto_fail_processor": 0,
            "auto_fail_coral_L1": 0,
            "auto_fail_coral_L2": 0,
            "auto_fail_coral_L3": 0,
            "auto_fail_coral_L4": 0,
            "auto_intake_ground_coral": 1,
            "auto_intake_ground_algae": 0,
            "auto_intake_reef": 1,
            "auto_intake_station": 0,
            "auto_drop_coral": 0,
            "auto_drop_algae": 0,
            "tele_net": 12,
            "tele_processor": 1,
            "tele_coral_L1": 1,
            "tele_coral_L2": 2,
            "tele_coral_L3": 2,
            "tele_coral_L4": 2,
            "tele_fail_net": 0,
            "tele_fail_processor": 0,
            "tele_fail_coral_L1": 0,
            "tele_fail_coral_L2": 1,
            "tele_fail_coral_L3": 0,
            "tele_fail_coral_L4": 0,
            "tele_intake_ground_coral": 0,
            "tele_intake_ground_algae": 0,
            "tele_intake_station": 1,
            "tele_intake_reef": 42,
            "tele_intake_poach": 0,
            "tele_drop_coral": 0,
            "tele_drop_algae": 0,
            "auto_intakes_ground": 1,
            "auto_total_pieces": 3,
            "auto_total_failed_pieces": 0,
            "tele_total_intakes": 1,
            "total_intakes": 3,
            "tele_total_pieces": 9,
            "tele_total_failed_pieces": 1,
            "total_pieces": 12,
            "total_failed_pieces": 1,
            "cage_level": "N",
            "cage_fail": False,
            "start_position": "1",
            "has_preload": True,
            "park": True,
            "tele_incap": 0,
            "median_cycle_time": 0,
            "expected_cycles": 10.0,
            "expected_cycle_time": 7.2,
        }

    def test_in_list_check1(self, caplog):
        with patch("tba_communicator.tba_request", return_value=self.tba_test_data):
            self.test_calculator.run()
        assert len([rec.message for rec in caplog.records if rec.levelname == "WARNING"]) > 0

    @mock.patch.object(
        unconsolidated_totals.UnconsolidatedTotals, "update_calcs", return_value=[{}]
    )
    def test_in_list_check2(self, caplog):
        with patch("tba_communicator.tba_request", return_value=self.tba_test_data):
            self.test_calculator.run()
        assert len([rec.message for rec in caplog.records if rec.levelname == "WARNING"]) == 0
