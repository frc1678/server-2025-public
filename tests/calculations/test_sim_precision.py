from unittest.mock import patch
import pytest
from utils import dict_near_in, dict_near, read_schema
import logging
import numpy as np

from calculations import sim_precision
import server


class TestSimPrecisionCalc:
    def setup_method(self):
        self.tba_test_data = [
            {
                "match_number": 1,
                "actual_time": 1100291640,
                "comp_level": "qm",
                "score_breakdown": {
                    "blue": {
                        "foulPoints": 8,
                        "autoLeavePoints": 15,
                        "totalPoints": 87,
                        "endgamePoints": 6,
                        "autoCoralPoints": 5,
                        "algaePoints": 0,
                        "autoPoints": 6,
                        "teleopCoralPoints": 31,
                        "teleopPoints": 35,
                        "netAlgaeCount": 2,
                        "wallAlgaeCount": 3,
                        "autoReef": {
                            "topRow": {
                                "NodeA": True,
                                "NodeB": False,
                                "NodeC": False,
                                "NodeD": False,
                                "NodeE": False,
                                "NodeF": False,
                                "NodeG": True,
                                "NodeH": False,
                                "NodeI": False,
                                "NodeJ": False,
                                "NodeK": False,
                                "NodeL": True,
                            },
                            "midRow": {
                                "NodeA": False,
                                "NodeB": True,
                                "NodeC": False,
                                "NodeD": False,
                                "NodeE": False,
                                "NodeF": True,
                                "NodeG": True,
                                "NodeH": False,
                                "NodeI": False,
                                "NodeJ": False,
                                "NodeK": False,
                                "NodeL": False,
                            },
                            "botRow": {
                                "NodeA": True,
                                "NodeB": False,
                                "NodeC": False,
                                "NodeD": False,
                                "NodeE": False,
                                "NodeF": False,
                                "NodeG": True,
                                "NodeH": False,
                                "NodeI": False,
                                "NodeJ": True,
                                "NodeK": True,
                                "NodeL": True,
                            },
                            "trough": 3,
                        },
                        "net_algae_count_no_hp": 0,
                    },
                    "red": {
                        "foulPoints": 6,
                        "autoLeavePoints": 20,
                        "totalPoints": 77,
                        "endgamePoints": 2,
                        "autoCoralPoints": 0,
                        "algaePoints": 0,
                        "autoPoints": 6,
                        "teleopCoralPoints": 21,
                        "teleopPoints": 15,
                        "netAlgaeCount": 0,
                        "wallAlgaeCount": 0,
                        "autoReef": {
                            "topRow": {
                                "NodeA": True,
                                "NodeB": False,
                                "NodeC": False,
                                "NodeD": False,
                                "NodeE": False,
                                "NodeF": False,
                                "NodeG": True,
                                "NodeH": False,
                                "NodeI": False,
                                "NodeJ": False,
                                "NodeK": False,
                                "NodeL": False,
                            },
                            "midRow": {
                                "NodeA": False,
                                "NodeB": True,
                                "NodeC": False,
                                "NodeD": False,
                                "NodeE": False,
                                "NodeF": True,
                                "NodeG": False,
                                "NodeH": False,
                                "NodeI": False,
                                "NodeJ": False,
                                "NodeK": False,
                                "NodeL": False,
                            },
                            "botRow": {
                                "NodeA": True,
                                "NodeB": False,
                                "NodeC": False,
                                "NodeD": False,
                                "NodeE": False,
                                "NodeF": False,
                                "NodeG": False,
                                "NodeH": False,
                                "NodeI": False,
                                "NodeJ": True,
                                "NodeK": True,
                                "NodeL": True,
                            },
                            "trough": 3,
                        },
                        "net_algae_count_no_hp": 1,
                    },
                },
            },
            {
                "match_number": 2,
                "actual_time": 1087511040,
                "comp_level": "qm",
                "score_breakdown": {
                    "blue": {
                        "foulPoints": 8,
                        "autoLeavePoints": 1,
                        "totalPoints": 0,
                        "endgamePoints": 6,
                        "autoCoralPoints": 10,
                        "algaePoints": 0,
                        "autoPoints": 6,
                        "teleopCoralPoints": 12,
                        "teleopPoints": 12,
                        "netAlgaeCount": 4,
                        "wallAlgaeCount": 4,
                        "autoReef": {
                            "topRow": {
                                "NodeA": True,
                                "NodeB": False,
                                "NodeC": False,
                                "NodeD": False,
                                "NodeE": False,
                                "NodeF": False,
                                "NodeG": True,
                                "NodeH": False,
                                "NodeI": False,
                                "NodeJ": False,
                                "NodeK": False,
                                "NodeL": True,
                            },
                            "midRow": {
                                "NodeA": False,
                                "NodeB": True,
                                "NodeC": False,
                                "NodeD": False,
                                "NodeE": False,
                                "NodeF": True,
                                "NodeG": True,
                                "NodeH": False,
                                "NodeI": False,
                                "NodeJ": False,
                                "NodeK": False,
                                "NodeL": False,
                            },
                            "botRow": {
                                "NodeA": True,
                                "NodeB": False,
                                "NodeC": False,
                                "NodeD": False,
                                "NodeE": False,
                                "NodeF": False,
                                "NodeG": True,
                                "NodeH": False,
                                "NodeI": False,
                                "NodeJ": True,
                                "NodeK": True,
                                "NodeL": True,
                            },
                            "trough": 3,
                        },
                        "net_algae_count_no_hp": 2,
                    },
                    "red": {
                        "foulPoints": 6,
                        "autoLeavePoints": 20,
                        "totalPoints": 10,
                        "endgamePoints": 2,
                        "autoCoralPoints": 18,
                        "algaePoints": 14,
                        "autoPoints": 6,
                        "teleopCoralPoints": 21,
                        "teleopPoints": 15,
                        "netAlgaeCount": 1,
                        "wallAlgaeCount": 1,
                        "autoReef": {
                            "topRow": {
                                "NodeA": True,
                                "NodeB": False,
                                "NodeC": False,
                                "NodeD": False,
                                "NodeE": False,
                                "NodeF": False,
                                "NodeG": True,
                                "NodeH": False,
                                "NodeI": False,
                                "NodeJ": False,
                                "NodeK": False,
                                "NodeL": False,
                            },
                            "midRow": {
                                "NodeA": False,
                                "NodeB": True,
                                "NodeC": False,
                                "NodeD": False,
                                "NodeE": False,
                                "NodeF": True,
                                "NodeG": False,
                                "NodeH": False,
                                "NodeI": False,
                                "NodeJ": False,
                                "NodeK": False,
                                "NodeL": False,
                            },
                            "botRow": {
                                "NodeA": True,
                                "NodeB": False,
                                "NodeC": False,
                                "NodeD": False,
                                "NodeE": False,
                                "NodeF": False,
                                "NodeG": False,
                                "NodeH": False,
                                "NodeI": False,
                                "NodeJ": True,
                                "NodeK": True,
                                "NodeL": True,
                            },
                            "trough": 6,
                        },
                        "net_algae_count_no_hp": 2,
                    },
                },
            },
            {
                "match_number": 3,
                "actual_time": None,
                "comp_level": "qm",
                "score_breakdown": None,
            },
        ]
        self.scout_tim_test_data = [
            # Match 1
            {
                "scout_name": "ALISON LIN",
                "team_number": "1678",
                "match_number": 1,
                "alliance_color_is_red": True,
                "auto_net": 0,
                "auto_processor": 1,
                "auto_coral_L1": 1,
                "auto_coral_L2": 0,
                "auto_coral_L3": 1,
                "auto_coral_L4": 1,
                "tele_net": 1,
                "tele_processor": 0,
                "tele_coral_L1": 0,
                "tele_coral_L2": 1,
                "tele_coral_L3": 1,
                "tele_coral_L4": 0,
            },
            {
                "scout_name": "NATHAN MILLS",
                "team_number": "1678",
                "match_number": 1,
                "alliance_color_is_red": True,
                "auto_net": 0,
                "auto_processor": 1,
                "auto_coral_L1": 1,
                "auto_coral_L2": 0,
                "auto_coral_L3": 0,
                "auto_coral_L4": 2,
                "tele_net": 1,
                "tele_processor": 0,
                "tele_coral_L1": 0,
                "tele_coral_L2": 0,
                "tele_coral_L3": 17,
                "tele_coral_L4": 1,
            },
            {
                "scout_name": "KATHY LI",
                "team_number": "4414",
                "match_number": 1,
                "alliance_color_is_red": True,
                "auto_net": 0,
                "auto_processor": 1,
                "auto_coral_L1": 1,
                "auto_coral_L2": 0,
                "auto_coral_L3": 1,
                "auto_coral_L4": 1,
                "tele_net": 1,
                "tele_processor": 0,
                "tele_coral_L1": 0,
                "tele_coral_L2": 1,
                "tele_coral_L3": 14,
                "tele_coral_L4": 0,
            },
            {
                "scout_name": "SCOTT WOOLLEY",
                "team_number": "589",
                "match_number": 1,
                "alliance_color_is_red": True,
                "auto_net": 0,
                "auto_processor": 1,
                "auto_coral_L1": 1,
                "auto_coral_L2": 0,
                "auto_coral_L3": 2,
                "auto_coral_L4": 1,
                "tele_net": 1,
                "tele_processor": 0,
                "tele_coral_L1": 9,
                "tele_coral_L2": 0,
                "tele_coral_L3": 1,
                "tele_coral_L4": 0,
            },
            {
                "scout_name": "JELLIFER KENT",
                "team_number": "589",
                "match_number": 1,
                "alliance_color_is_red": True,
                "auto_net": 0,
                "auto_processor": 1,
                "auto_coral_L1": 1,
                "auto_coral_L2": 0,
                "auto_coral_L3": 4,
                "auto_coral_L4": 1,
                "tele_net": 1,
                "tele_processor": 0,
                "tele_coral_L1": 5,
                "tele_coral_L2": 0,
                "tele_coral_L3": 1,
                "tele_coral_L4": 0,
            },
            {
                "scout_name": "ALISON YOUNG",
                "team_number": "589",
                "match_number": 1,
                "alliance_color_is_red": True,
                "auto_net": 0,
                "auto_processor": 1,
                "auto_coral_L1": 1,
                "auto_coral_L2": 0,
                "auto_coral_L3": 0,
                "auto_coral_L4": 1,
                "tele_net": 1,
                "tele_processor": 0,
                "tele_coral_L1": 4,
                "tele_coral_L2": 2,
                "tele_coral_L3": 1,
                "tele_coral_L4": 0,
            },
            # Match 2
            {
                "scout_name": "NATHAN MILLS",
                "team_number": "1678",
                "match_number": 2,
                "alliance_color_is_red": False,
                "auto_net": 0,
                "auto_processor": 1,
                "auto_coral_L1": 1,
                "auto_coral_L2": 1,
                "auto_coral_L3": 0,
                "auto_coral_L4": 1,
                "tele_net": 1,
                "tele_processor": 0,
                "tele_coral_L1": 0,
                "tele_coral_L2": 1,
                "tele_coral_L3": 2,
                "tele_coral_L4": 0,
            },
            {
                "scout_name": "KATHY LI",
                "team_number": "4414",
                "match_number": 2,
                "alliance_color_is_red": False,
                "auto_net": 0,
                "auto_processor": 1,
                "auto_coral_L1": 1,
                "auto_coral_L2": 0,
                "auto_coral_L3": 0,
                "auto_coral_L4": 1,
                "tele_net": 1,
                "tele_processor": 0,
                "tele_coral_L1": 0,
                "tele_coral_L2": 1,
                "tele_coral_L3": 1,
                "tele_coral_L4": 0,
            },
            {
                "scout_name": "AMY SHAN",
                "team_number": "589",
                "match_number": 2,
                "alliance_color_is_red": False,
                "auto_net": 0,
                "auto_processor": 1,
                "auto_coral_L1": 1,
                "auto_coral_L2": 0,
                "auto_coral_L3": 0,
                "auto_coral_L4": 2,
                "tele_net": 1,
                "tele_processor": 0,
                "tele_coral_L1": 0,
                "tele_coral_L2": 2,
                "tele_coral_L3": 0,
                "tele_coral_L4": 0,
            },
        ]
        self.auto_pim_test_data = [
            {
                "team_number": "1678",
                "match_number": 1,
                "auto_coral_F1_L2": 0,
                "auto_coral_F2_L2": 2,
                "auto_coral_F3_L2": 1,
                "auto_coral_F4_L2": 0,
                "auto_coral_F5_L2": 0,
                "auto_coral_F6_L2": 0,
                "auto_coral_F1_L3": 1,
                "auto_coral_F2_L3": 1,
                "auto_coral_F3_L3": 1,
                "auto_coral_F4_L3": 0,
                "auto_coral_F5_L3": 0,
                "auto_coral_F6_L3": 0,
                "auto_coral_F1_L4": 0,
                "auto_coral_F2_L4": 0,
                "auto_coral_F3_L4": 0,
                "auto_coral_F4_L4": 0,
                "auto_coral_F5_L4": 0,
                "auto_coral_F6_L4": 0,
            },
            {
                "team_number": "589",
                "match_number": 1,
                "auto_coral_F1_L2": 0,
                "auto_coral_F2_L2": 0,
                "auto_coral_F3_L2": 0,
                "auto_coral_F4_L2": 0,
                "auto_coral_F5_L2": 0,
                "auto_coral_F6_L2": 0,
                "auto_coral_F1_L3": 0,
                "auto_coral_F2_L3": 0,
                "auto_coral_F3_L3": 0,
                "auto_coral_F4_L3": 0,
                "auto_coral_F5_L3": 0,
                "auto_coral_F6_L3": 0,
                "auto_coral_F1_L4": 0,
                "auto_coral_F2_L4": 0,
                "auto_coral_F3_L4": 1,
                "auto_coral_F4_L4": 1,
                "auto_coral_F5_L4": 1,
                "auto_coral_F6_L4": 1,
            },
            {
                "team_number": "4414",
                "match_number": 1,
                "auto_coral_F1_L2": 0,
                "auto_coral_F2_L2": 0,
                "auto_coral_F3_L2": 0,
                "auto_coral_F4_L2": 0,
                "auto_coral_F5_L2": 0,
                "auto_coral_F6_L2": 0,
                "auto_coral_F1_L3": 0,
                "auto_coral_F2_L3": 0,
                "auto_coral_F3_L3": 0,
                "auto_coral_F4_L3": 0,
                "auto_coral_F5_L3": 0,
                "auto_coral_F6_L3": 0,
                "auto_coral_F1_L4": 1,
                "auto_coral_F2_L4": 1,
                "auto_coral_F3_L4": 0,
                "auto_coral_F4_L4": 1,
                "auto_coral_F5_L4": 0,
                "auto_coral_F6_L4": 1,
            },
            {
                "team_number": "1678",
                "match_number": 2,
                "auto_coral_F1_L2": 0,
                "auto_coral_F2_L2": 1,
                "auto_coral_F3_L2": 1,
                "auto_coral_F4_L2": 0,
                "auto_coral_F5_L2": 0,
                "auto_coral_F6_L2": 0,
                "auto_coral_F1_L3": 1,
                "auto_coral_F2_L3": 1,
                "auto_coral_F3_L3": 1,
                "auto_coral_F4_L3": 0,
                "auto_coral_F5_L3": 0,
                "auto_coral_F6_L3": 0,
                "auto_coral_F1_L4": 0,
                "auto_coral_F2_L4": 0,
                "auto_coral_F3_L4": 0,
                "auto_coral_F4_L4": 0,
                "auto_coral_F5_L4": 0,
                "auto_coral_F6_L4": 0,
            },
            {
                "team_number": "589",
                "match_number": 2,
                "auto_coral_F1_L2": 0,
                "auto_coral_F2_L2": 0,
                "auto_coral_F3_L2": 0,
                "auto_coral_F4_L2": 0,
                "auto_coral_F5_L2": 0,
                "auto_coral_F6_L2": 0,
                "auto_coral_F1_L3": 0,
                "auto_coral_F2_L3": 0,
                "auto_coral_F3_L3": 0,
                "auto_coral_F4_L3": 0,
                "auto_coral_F5_L3": 0,
                "auto_coral_F6_L3": 0,
                "auto_coral_F1_L4": 1,
                "auto_coral_F2_L4": 0,
                "auto_coral_F3_L4": 1,
                "auto_coral_F4_L4": 1,
                "auto_coral_F5_L4": 1,
                "auto_coral_F6_L4": 1,
            },
            {
                "team_number": "4414",
                "match_number": 2,
                "auto_coral_F1_L2": 1,
                "auto_coral_F2_L2": 0,
                "auto_coral_F3_L2": 0,
                "auto_coral_F4_L2": 0,
                "auto_coral_F5_L2": 0,
                "auto_coral_F6_L2": 0,
                "auto_coral_F1_L3": 0,
                "auto_coral_F2_L3": 0,
                "auto_coral_F3_L3": 0,
                "auto_coral_F4_L3": 0,
                "auto_coral_F5_L3": 0,
                "auto_coral_F6_L3": 0,
                "auto_coral_F1_L4": 1,
                "auto_coral_F2_L4": 1,
                "auto_coral_F3_L4": 0,
                "auto_coral_F4_L4": 1,
                "auto_coral_F5_L4": 0,
                "auto_coral_F6_L4": 1,
            },
        ]

        with patch("doozernet_communicator.check_model_availability", return_value=None):
            self.test_server = server.Server()
        self.test_calc = sim_precision.SimPrecisionCalc(self.test_server)

    def test___init__(self):
        assert self.test_calc.watched_collections == ["unconsolidated_totals"]
        assert self.test_calc.server == self.test_server

    def test_get_scout_tim_score(self, caplog):
        required = self.test_calc.sim_schema["calculations"]["auto_reef_precision"]["requires"]
        self.test_server.local_db.delete_data("unconsolidated_totals")
        self.test_server.local_db.insert_documents("auto_pim", self.auto_pim_test_data)
        self.test_calc.get_scout_tim_score("JELLIFER KENT", 2, required)
        assert ["No data from Scout JELLIFER KENT in Match 2"] == [
            rec.message for rec in caplog.records if rec.levelname == "WARNING"
        ]
        self.test_server.local_db.insert_documents(
            "unconsolidated_totals", self.scout_tim_test_data
        )
        assert self.test_calc.get_scout_tim_score("ALISON LIN", 1, required) == 16
        assert self.test_calc.get_scout_tim_score("AMY SHAN", 1, required) == None
        assert self.test_calc.get_scout_tim_score("NATHAN MILLS", 2, required) == 14

    def test_get_aim_scout_scores(self):
        self.test_server.local_db.delete_data("unconsolidated_totals")
        self.test_server.local_db.insert_documents(
            "unconsolidated_totals", self.scout_tim_test_data
        )
        self.test_server.local_db.delete_data("auto_pim")
        self.test_server.local_db.insert_documents("auto_pim", self.auto_pim_test_data)
        required = self.test_calc.sim_schema["calculations"]["tele_reef_precision"]["requires"]
        assert self.test_calc.get_aim_scout_scores(1, True, required) == {
            "1678": {"ALISON LIN": 7, "NATHAN MILLS": 73},
            "4414": {"KATHY LI": 59},
            "589": {"ALISON YOUNG": 18, "JELLIFER KENT": 14, "SCOTT WOOLLEY": 22},
        }
        assert self.test_calc.get_aim_scout_scores(2, False, required) == {
            "1678": {"NATHAN MILLS": 11},
            "4414": {"KATHY LI": 7},
            "589": {"AMY SHAN": 6},
        }

    def test_get_aim_scout_avg_errors(self, caplog):
        assert not (
            self.test_calc.get_aim_scout_avg_errors(
                {
                    "1678": {"KATHY LI": 31, "JELLIFER KENT": 31},
                    "589": {"AMY SHAN": 23},
                },
                100,
                1,
                True,
            )
        )
        assert ["Missing red alliance scout data for Match 1"] == [
            rec.message for rec in caplog.records if rec.levelname == "WARNING"
        ]
        aim_scout_scores = {
            "1678": {"ALISON LIN": 31, "NATHAN MILLS": 6},
            "4414": {"KATHY LI": 19},
            "589": {"ALISON YOUNG": 23, "AMY SHAN": 23, "JELLIFER KENT": 23},
        }
        assert self.test_calc.get_aim_scout_avg_errors(aim_scout_scores, 73, 1, True) == {
            "ALISON YOUNG": 4.166666666666667,
            "AMY SHAN": 4.166666666666667,
            "JELLIFER KENT": 4.166666666666667,
            "KATHY LI": 4.166666666666667,
            "ALISON LIN": 0.0,
            "NATHAN MILLS": 8.333333333333334,
        }

    def test_update_sim_precision_calcs(self):
        self.test_server.local_db.insert_documents(
            "unconsolidated_totals", self.scout_tim_test_data
        )
        self.test_server.local_db.delete_data("auto_pim")
        self.test_server.local_db.insert_documents("auto_pim", self.auto_pim_test_data)
        expected_updates = [
            {
                "scout_name": "ALISON LIN",
                "match_number": 1,
                "team_number": "1678",
                "alliance_color_is_red": True,
                "auto_reef_precision": np.float64(18.0),
                "tele_reef_precision": np.float64(21.0),
                "processor_precision": np.float64(6.0),
                "net_precision": np.float64(2.6666666666666665),
                "sim_precision": np.float64(47.666666666666664),
            }
        ]
        with patch("tba_communicator.tba_request", return_value=self.tba_test_data):
            updates = self.test_calc.update_sim_precision_calcs(
                [
                    {
                        "scout_name": "ALISON LIN",
                        "match_number": 1,
                        "alliance_color_is_red": True,
                    }
                ]
            )

            # Remove timestamp field since it's difficult to test, figure out later
            updates[0].pop("timestamp")
            assert updates == expected_updates

    def test_get_tba_value(self):
        """Tests get_tba_value, which returns an integer equal to the totals of the datapoints specified"""
        expected_data = {
            "sim_precision": 41,
            "auto_reef_precision": 5,
            "auto_L1_precision": 9,
            "auto_L2_precision": 20,
            "auto_F1_L2_precision": 4,
            "auto_F2_L2_precision": 0,
            "auto_F3_L2_precision": 0,
            "auto_F4_L2_precision": 4,
            "auto_F5_L2_precision": 4,
            "auto_F6_L2_precision": 8,
            "auto_L3_precision": 18,
            "auto_F1_L3_precision": 6,
            "auto_F2_L3_precision": 0,
            "auto_F3_L3_precision": 6,
            "auto_F4_L3_precision": 6,
            "auto_F5_L3_precision": 0,
            "auto_F6_L3_precision": 0,
            "auto_L4_precision": 21,
            "auto_F1_L4_precision": 7,
            "auto_F2_L4_precision": 0,
            "auto_F3_L4_precision": 0,
            "auto_F4_L4_precision": 7,
            "auto_F5_L4_precision": 0,
            "auto_F6_L4_precision": 7,
            "tele_reef_precision": 31,
            "algae_precision": 0,
            "net_precision": 0,
            "processor_precision": 0,
        }
        for calc, schema in self.test_calc.sim_schema["calculations"].items():
            # Checks the returned integer against the value of the calculation name in expected_data
            weight = schema["tba_weight"] if "tba_weight" in schema.keys() else 1
            expected_data[calc] = self.test_calc.get_tba_value(
                self.tba_test_data, schema["tba_datapoints"], 1, False, weight
            )
        assert (
            self.test_calc.get_tba_value(
                self.tba_test_data, schema["tba_datapoints"], 1, False, weight
            )
            == expected_data[calc]
        )

    def test_run(self):
        expected_sim_precision = [
            {
                "scout_name": "ALISON LIN",
                "match_number": 1,
                "team_number": "1678",
                "alliance_color_is_red": True,
                "sim_precision": 47.666666666666664,
            },
            {
                "scout_name": "NATHAN MILLS",
                "match_number": 1,
                "team_number": "1678",
                "alliance_color_is_red": True,
                "sim_precision": 70.0,
            },
            {
                "scout_name": "KATHY LI",
                "match_number": 1,
                "team_number": "4414",
                "alliance_color_is_red": True,
                "sim_precision": 58.83333333333333,
            },
            {
                "scout_name": "SCOTT WOOLLEY",
                "match_number": 1,
                "team_number": "589",
                "alliance_color_is_red": True,
                "sim_precision": 60.166666666666664,
            },
            {
                "scout_name": "JELLIFER KENT",
                "match_number": 1,
                "team_number": "589",
                "alliance_color_is_red": True,
                "sim_precision": 61.49999999999999,
            },
            {
                "scout_name": "ALISON YOUNG",
                "match_number": 1,
                "team_number": "589",
                "alliance_color_is_red": True,
                "sim_precision": 54.833333333333336,
            },
            {
                "scout_name": "NATHAN MILLS",
                "match_number": 2,
                "team_number": "1678",
                "alliance_color_is_red": False,
                "sim_precision": 17.666666666666668,
            },
            {
                "scout_name": "KATHY LI",
                "match_number": 2,
                "team_number": "4414",
                "alliance_color_is_red": False,
                "sim_precision": 17.666666666666668,
            },
            {
                "scout_name": "AMY SHAN",
                "match_number": 2,
                "team_number": "589",
                "alliance_color_is_red": False,
                "sim_precision": 17.666666666666668,
            },
        ]
        self.test_server.local_db.delete_data("unconsolidated_totals")
        self.test_server.local_db.insert_documents(
            "unconsolidated_totals", self.scout_tim_test_data
        )
        self.test_server.local_db.delete_data("auto_pim")
        self.test_server.local_db.insert_documents("auto_pim", self.auto_pim_test_data)
        with patch(
            "tba_communicator.tba_request",
            return_value=self.tba_test_data,
        ):
            self.test_calc.run()
        sim_precision_result = self.test_server.local_db.find("sim_precision")
        fields_to_keep = {
            "sim_precision",
            "scout_name",
            "match_number",
            "team_number",
            "alliance_color_is_red",
        }
        schema = read_schema("schema/calc_sim_precision_schema.yml")
        calculations = schema["calculations"]
        for document in sim_precision_result:
            for calculation in calculations:
                assert calculation in document
            assert "_id" in document
            assert "timestamp" in document
            # Remove fields we are not testing
            for field in list(document.keys()):
                if field not in fields_to_keep:
                    document.pop(field)
        for document in expected_sim_precision:
            assert dict_near_in(document, sim_precision_result)
