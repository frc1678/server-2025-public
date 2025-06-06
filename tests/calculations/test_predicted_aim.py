from calculations import predicted_aim
from unittest.mock import patch
import server
import pytest
import pandas as pd
import utils


class TestPredictedAimCalc:
    def setup_method(self):
        with patch("doozernet_communicator.check_model_availability", return_value=None):
            self.test_server = server.Server()
        self.test_calc = predicted_aim.PredictedAimCalc(self.test_server)
        self.teams_list = ["1678", "254", "4414", "125", "1323", "5940"]
        self.aims_list = [
            {
                "match_number": 1,
                "alliance_color": "R",
                "team_list": ["1678", "254", "4414"],
            },
            {
                "match_number": 1,
                "alliance_color": "B",
                "team_list": ["125", "1323", "5940"],
            },
            {
                "match_number": 2,
                "alliance_color": "R",
                "team_list": ["1678", "1323", "125"],
            },
            {
                "match_number": 2,
                "alliance_color": "B",
                "team_list": ["254", "4414", "5940"],
            },
            {
                "match_number": 3,
                "alliance_color": "R",
                "team_list": ["1678", "5940", "4414"],
            },
            {
                "match_number": 3,
                "alliance_color": "B",
                "team_list": ["1323", "254", "125"],
            },
        ]
        self.filtered_aims_list = [
            {
                "match_number": 1,
                "alliance_color": "R",
                "team_list": ["1678", "254", "4414"],
            },
            {
                "match_number": 1,
                "alliance_color": "B",
                "team_list": ["125", "1323", "5940"],
            },
            {
                "match_number": 2,
                "alliance_color": "R",
                "team_list": ["1678", "1323", "125"],
            },
            {
                "match_number": 2,
                "alliance_color": "B",
                "team_list": ["254", "4414", "5940"],
            },
            {
                "match_number": 3,
                "alliance_color": "R",
                "team_list": ["1678", "5940", "4414"],
            },
            {
                "match_number": 3,
                "alliance_color": "B",
                "team_list": ["1323", "254", "125"],
            },
        ]
        self.expected_updates = [
            {
                "match_number": 1,
                "alliance_color_is_red": True,
                "has_tim_data": False,
                "full_tim_data": False,
                "has_tba_data": True,
                "_auto_net": 9,
                "_auto_processor": 12,
                "_auto_coral_L1": 3,
                "_auto_coral_L2": 3,
                "_auto_coral_L3": 3,
                "_auto_coral_L4": 3,
                "_auto_leave": 2.4,
                "_tele_net": 6,
                "_tele_processor": 6,
                "_tele_coral_L1": 3,
                "_tele_coral_L2": 3,
                "_tele_coral_L3": 3,
                "_tele_coral_L4": 3,
                "_endgame_park": 0.99,
                "_endgame_shallow": 1.7999999999999998,
                "_endgame_deep": 2.7,
                "predicted_score": 262.62,
                "predicted_auto_score": 135.35999999999999,
                "predicted_tele_score": 82.08,
                "predicted_endgame_score": 45.18000000000001,
                "predicted_barge_rp": 1,
                "predicted_coral_rp": 0,
                "predicted_auto_rp": 0.0,
                "win_chance": 0.5,
                "actual_score": 320,
                "actual_barge_rp": 0.0,
                "actual_coral_rp": 1.0,
                "actual_auto_rp": 1.0,
                "won_match": True,
                "actual_score_auto": 12,
                "actual_score_endgame": 10,
                "actual_score_tele": 244,
                "actual_foul_points": 2,
                "cooperated": True,
                "team_numbers": ["1678", "254", "4414"],
            },
            {
                "match_number": 1,
                "alliance_color_is_red": False,
                "has_tim_data": True,
                "full_tim_data": True,
                "has_tba_data": True,
                "_auto_net": 9,
                "_auto_processor": 12,
                "_auto_coral_L1": 3,
                "_auto_coral_L2": 3,
                "_auto_coral_L3": 3,
                "_auto_coral_L4": 3,
                "_auto_leave": 1.4000000000000001,
                "_tele_net": 6,
                "_tele_processor": 6,
                "_tele_coral_L1": 3,
                "_tele_coral_L2": 3,
                "_tele_coral_L3": 3,
                "_tele_coral_L4": 3,
                "_endgame_park": 0.99,
                "_endgame_shallow": 1.7999999999999998,
                "_endgame_deep": 2.7,
                "predicted_score": 259.62,
                "predicted_auto_score": 132.35999999999999,
                "predicted_tele_score": 82.08,
                "predicted_endgame_score": 45.18000000000001,
                "predicted_barge_rp": 1,
                "predicted_coral_rp": 0,
                "predicted_auto_rp": 0.0,
                "win_chance": 0.5,
                "actual_score": 278,
                "actual_barge_rp": 1.0,
                "actual_coral_rp": 1.0,
                "actual_auto_rp": 1.0,
                "won_match": False,
                "actual_score_auto": 12,
                "actual_score_endgame": 10,
                "actual_score_tele": 244,
                "actual_foul_points": 2,
                "cooperated": True,
                "team_numbers": ["125", "1323", "5940"],
            },
            {
                "match_number": 2,
                "alliance_color_is_red": True,
                "has_tim_data": False,
                "full_tim_data": False,
                "has_tba_data": False,
                "_auto_net": 9,
                "_auto_processor": 12,
                "_auto_coral_L1": 3,
                "_auto_coral_L2": 3,
                "_auto_coral_L3": 3,
                "_auto_coral_L4": 3,
                "_auto_leave": 2.2,
                "_tele_net": 6,
                "_tele_processor": 6,
                "_tele_coral_L1": 3,
                "_tele_coral_L2": 3,
                "_tele_coral_L3": 3,
                "_tele_coral_L4": 3,
                "_endgame_park": 0.99,
                "_endgame_shallow": 1.7999999999999998,
                "_endgame_deep": 2.7,
                "predicted_score": 262.02,
                "predicted_auto_score": 134.76,
                "predicted_tele_score": 82.08,
                "predicted_endgame_score": 45.18000000000001,
                "predicted_barge_rp": 1,
                "predicted_coral_rp": 0,
                "predicted_auto_rp": 0.0,
                "win_chance": 0.5,
                "actual_score": 0,
                "actual_barge_rp": 0.0,
                "actual_coral_rp": 0.0,
                "actual_auto_rp": 0.0,
                "won_match": False,
                "team_numbers": ["1678", "1323", "125"],
            },
            {
                "match_number": 2,
                "alliance_color_is_red": False,
                "has_tim_data": True,
                "full_tim_data": True,
                "has_tba_data": False,
                "_auto_net": 9,
                "_auto_processor": 12,
                "_auto_coral_L1": 3,
                "_auto_coral_L2": 3,
                "_auto_coral_L3": 3,
                "_auto_coral_L4": 3,
                "_auto_leave": 1.5999999999999999,
                "_tele_net": 6,
                "_tele_processor": 6,
                "_tele_coral_L1": 3,
                "_tele_coral_L2": 3,
                "_tele_coral_L3": 3,
                "_tele_coral_L4": 3,
                "_endgame_park": 0.99,
                "_endgame_shallow": 1.7999999999999998,
                "_endgame_deep": 2.7,
                "predicted_score": 260.22,
                "predicted_auto_score": 132.96,
                "predicted_tele_score": 82.08,
                "predicted_endgame_score": 45.18000000000001,
                "predicted_barge_rp": 1,
                "predicted_coral_rp": 0,
                "predicted_auto_rp": 0.0,
                "win_chance": 0.5,
                "actual_score": 0,
                "actual_barge_rp": 0.0,
                "actual_coral_rp": 0.0,
                "actual_auto_rp": 0.0,
                "won_match": False,
                "team_numbers": ["254", "4414", "5940"],
            },
            {
                "match_number": 3,
                "alliance_color_is_red": True,
                "has_tim_data": False,
                "full_tim_data": False,
                "has_tba_data": True,
                "_auto_net": 9,
                "_auto_processor": 12,
                "_auto_coral_L1": 3,
                "_auto_coral_L2": 3,
                "_auto_coral_L3": 3,
                "_auto_coral_L4": 3,
                "_auto_leave": 1.8,
                "_tele_net": 6,
                "_tele_processor": 6,
                "_tele_coral_L1": 3,
                "_tele_coral_L2": 3,
                "_tele_coral_L3": 3,
                "_tele_coral_L4": 3,
                "_endgame_park": 0.99,
                "_endgame_shallow": 1.7999999999999998,
                "_endgame_deep": 2.7,
                "predicted_score": 260.82000000000005,
                "predicted_auto_score": 133.56,
                "predicted_tele_score": 82.08,
                "predicted_endgame_score": 45.18000000000001,
                "predicted_barge_rp": 1,
                "predicted_coral_rp": 0,
                "predicted_auto_rp": 0.0,
                "win_chance": 0.5,
                "actual_score": 0,
                "actual_barge_rp": 0.0,
                "actual_coral_rp": 0.0,
                "actual_auto_rp": 0.0,
                "won_match": False,
                "team_numbers": ["1678", "5940", "4414"],
            },
            {
                "match_number": 3,
                "alliance_color_is_red": False,
                "has_tim_data": True,
                "full_tim_data": True,
                "has_tba_data": True,
                "_auto_net": 9,
                "_auto_processor": 12,
                "_auto_coral_L1": 3,
                "_auto_coral_L2": 3,
                "_auto_coral_L3": 3,
                "_auto_coral_L4": 3,
                "_auto_leave": 2.0,
                "_tele_net": 6,
                "_tele_processor": 6,
                "_tele_coral_L1": 3,
                "_tele_coral_L2": 3,
                "_tele_coral_L3": 3,
                "_tele_coral_L4": 3,
                "_endgame_park": 0.99,
                "_endgame_shallow": 1.7999999999999998,
                "_endgame_deep": 2.7,
                "predicted_score": 261.42,
                "predicted_auto_score": 134.16,
                "predicted_tele_score": 82.08,
                "predicted_endgame_score": 45.18000000000001,
                "predicted_barge_rp": 1,
                "predicted_coral_rp": 0,
                "predicted_auto_rp": 0.0,
                "win_chance": 0.5,
                "actual_score": 0,
                "actual_barge_rp": 0.0,
                "actual_coral_rp": 0.0,
                "actual_auto_rp": 0.0,
                "won_match": False,
                "team_numbers": ["1323", "254", "125"],
            },
        ]
        self.expected_playoffs_updates = [
            {"alliance_num": 1, "picks": ["1678", "254", "4414"]},
            {"alliance_num": 2, "picks": ["189", "345", "200", "100"]},
        ]
        self.expected_playoffs_updates_2 = [
            {"alliance_num": 1, "picks": ["1678", "254", "4414"]},
            {"alliance_num": 2, "picks": ["189", "345", "200", "100"]},
        ]
        self.expected_results = [
            {
                "match_number": 1,
                "alliance_color_is_red": True,
                "has_tim_data": False,
                "full_tim_data": False,
                "has_tba_data": True,
                "_auto_net": 9,
                "_auto_processor": 12,
                "_auto_coral_L1": 3,
                "_auto_coral_L2": 3,
                "_auto_coral_L3": 3,
                "_auto_coral_L4": 3,
                "_auto_leave": 2.4,
                "_tele_net": 6,
                "_tele_processor": 6,
                "_tele_coral_L1": 3,
                "_tele_coral_L2": 3,
                "_tele_coral_L3": 3,
                "_tele_coral_L4": 3,
                "_endgame_park": 0.99,
                "_endgame_shallow": 1.7999999999999998,
                "_endgame_deep": 2.7,
                "predicted_score": 262.62,
                "predicted_auto_score": 135.35999999999999,
                "predicted_tele_score": 82.08,
                "predicted_endgame_score": 45.18000000000001,
                "predicted_barge_rp": 1,
                "predicted_coral_rp": 0,
                "predicted_auto_rp": 0.0,
                "win_chance": 0.5,
                "actual_score": 320,
                "actual_barge_rp": 0.0,
                "actual_coral_rp": 1.0,
                "actual_auto_rp": 1.0,
                "won_match": True,
                "actual_score_auto": 12,
                "actual_score_endgame": 10,
                "actual_score_tele": 244,
                "actual_foul_points": 2,
                "cooperated": True,
                "team_numbers": ["1678", "254", "4414"],
            },
            {
                "match_number": 1,
                "alliance_color_is_red": False,
                "has_tim_data": True,
                "full_tim_data": True,
                "has_tba_data": True,
                "_auto_net": 9,
                "_auto_processor": 12,
                "_auto_coral_L1": 3,
                "_auto_coral_L2": 3,
                "_auto_coral_L3": 3,
                "_auto_coral_L4": 3,
                "_auto_leave": 1.4000000000000001,
                "_tele_net": 6,
                "_tele_processor": 6,
                "_tele_coral_L1": 3,
                "_tele_coral_L2": 3,
                "_tele_coral_L3": 3,
                "_tele_coral_L4": 3,
                "_endgame_park": 0.99,
                "_endgame_shallow": 1.7999999999999998,
                "_endgame_deep": 2.7,
                "predicted_score": 259.62,
                "predicted_auto_score": 132.35999999999999,
                "predicted_tele_score": 82.08,
                "predicted_endgame_score": 45.18000000000001,
                "predicted_barge_rp": 1,
                "predicted_coral_rp": 0,
                "predicted_auto_rp": 0.0,
                "win_chance": 0.5,
                "actual_score": 278,
                "actual_barge_rp": 1.0,
                "actual_coral_rp": 1.0,
                "actual_auto_rp": 1.0,
                "won_match": False,
                "actual_score_auto": 12,
                "actual_score_endgame": 10,
                "actual_score_tele": 244,
                "actual_foul_points": 2,
                "cooperated": True,
                "team_numbers": ["125", "1323", "5940"],
            },
            {
                "match_number": 2,
                "alliance_color_is_red": True,
                "has_tim_data": False,
                "full_tim_data": False,
                "has_tba_data": False,
                "_auto_net": 9,
                "_auto_processor": 12,
                "_auto_coral_L1": 3,
                "_auto_coral_L2": 3,
                "_auto_coral_L3": 3,
                "_auto_coral_L4": 3,
                "_auto_leave": 2.2,
                "_tele_net": 6,
                "_tele_processor": 6,
                "_tele_coral_L1": 3,
                "_tele_coral_L2": 3,
                "_tele_coral_L3": 3,
                "_tele_coral_L4": 3,
                "_endgame_park": 0.99,
                "_endgame_shallow": 1.7999999999999998,
                "_endgame_deep": 2.7,
                "predicted_score": 262.02,
                "predicted_auto_score": 134.76,
                "predicted_tele_score": 82.08,
                "predicted_endgame_score": 45.18000000000001,
                "predicted_barge_rp": 1,
                "predicted_coral_rp": 0,
                "predicted_auto_rp": 0.0,
                "win_chance": 0.5,
                "actual_score": 0,
                "actual_barge_rp": 0.0,
                "actual_coral_rp": 0.0,
                "actual_auto_rp": 0.0,
                "won_match": False,
                "team_numbers": ["1678", "1323", "125"],
            },
            {
                "match_number": 2,
                "alliance_color_is_red": False,
                "has_tim_data": True,
                "full_tim_data": True,
                "has_tba_data": False,
                "_auto_net": 9,
                "_auto_processor": 12,
                "_auto_coral_L1": 3,
                "_auto_coral_L2": 3,
                "_auto_coral_L3": 3,
                "_auto_coral_L4": 3,
                "_auto_leave": 1.5999999999999999,
                "_tele_net": 6,
                "_tele_processor": 6,
                "_tele_coral_L1": 3,
                "_tele_coral_L2": 3,
                "_tele_coral_L3": 3,
                "_tele_coral_L4": 3,
                "_endgame_park": 0.99,
                "_endgame_shallow": 1.7999999999999998,
                "_endgame_deep": 2.7,
                "predicted_score": 260.22,
                "predicted_auto_score": 132.96,
                "predicted_tele_score": 82.08,
                "predicted_endgame_score": 45.18000000000001,
                "predicted_barge_rp": 1,
                "predicted_coral_rp": 0,
                "predicted_auto_rp": 0.0,
                "win_chance": 0.5,
                "actual_score": 0,
                "actual_barge_rp": 0.0,
                "actual_coral_rp": 0.0,
                "actual_auto_rp": 0.0,
                "won_match": False,
                "team_numbers": ["254", "4414", "5940"],
            },
            {
                "match_number": 3,
                "alliance_color_is_red": True,
                "has_tim_data": False,
                "full_tim_data": False,
                "has_tba_data": True,
                "_auto_net": 9,
                "_auto_processor": 12,
                "_auto_coral_L1": 3,
                "_auto_coral_L2": 3,
                "_auto_coral_L3": 3,
                "_auto_coral_L4": 3,
                "_auto_leave": 1.8,
                "_tele_net": 6,
                "_tele_processor": 6,
                "_tele_coral_L1": 3,
                "_tele_coral_L2": 3,
                "_tele_coral_L3": 3,
                "_tele_coral_L4": 3,
                "_endgame_park": 0.99,
                "_endgame_shallow": 1.7999999999999998,
                "_endgame_deep": 2.7,
                "predicted_score": 260.82000000000005,
                "predicted_auto_score": 133.56,
                "predicted_tele_score": 82.08,
                "predicted_endgame_score": 45.18000000000001,
                "predicted_barge_rp": 1,
                "predicted_coral_rp": 0,
                "predicted_auto_rp": 0.0,
                "win_chance": 0.5,
                "actual_score": 0,
                "actual_barge_rp": 0.0,
                "actual_coral_rp": 0.0,
                "actual_auto_rp": 0.0,
                "won_match": False,
                "team_numbers": ["1678", "5940", "4414"],
            },
            {
                "match_number": 3,
                "alliance_color_is_red": False,
                "has_tim_data": True,
                "full_tim_data": True,
                "has_tba_data": True,
                "_auto_net": 9,
                "_auto_processor": 12,
                "_auto_coral_L1": 3,
                "_auto_coral_L2": 3,
                "_auto_coral_L3": 3,
                "_auto_coral_L4": 3,
                "_auto_leave": 2.0,
                "_tele_net": 6,
                "_tele_processor": 6,
                "_tele_coral_L1": 3,
                "_tele_coral_L2": 3,
                "_tele_coral_L3": 3,
                "_tele_coral_L4": 3,
                "_endgame_park": 0.99,
                "_endgame_shallow": 1.7999999999999998,
                "_endgame_deep": 2.7,
                "predicted_score": 261.42,
                "predicted_auto_score": 134.16,
                "predicted_tele_score": 82.08,
                "predicted_endgame_score": 45.18000000000001,
                "predicted_barge_rp": 1,
                "predicted_coral_rp": 0,
                "predicted_auto_rp": 0.0,
                "win_chance": 0.5,
                "actual_score": 0,
                "actual_barge_rp": 0.0,
                "actual_coral_rp": 0.0,
                "actual_auto_rp": 0.0,
                "won_match": False,
                "team_numbers": ["1323", "254", "125"],
            },
        ]
        self.expected_playoffs_alliances = [
            {"alliance_num": 1, "picks": ["1678", "254", "4414"]},
            {"alliance_num": 2, "picks": ["189", "345", "200", "100"]},
        ]
        self.obj_team = [
            {
                "team_number": "1678",
                "matches_played": 5,
                "auto_avg_coral_L1": 1,
                "auto_sd_coral_L1": 0,
                "auto_avg_coral_L2": 1,
                "auto_sd_coral_L2": 0,
                "auto_avg_coral_L3": 1,
                "auto_sd_coral_L3": 0,
                "auto_avg_coral_L4": 1,
                "auto_sd_coral_L4": 0,
                "auto_avg_net": 3,
                "auto_sd_net": 1,
                "auto_avg_processor": 4,
                "auto_sd_processor": 2,
                "tele_avg_net": 2,
                "tele_avg_processor": 2,
                "tele_avg_coral_L1": 1,
                "tele_sd_coral_L1": 0,
                "tele_avg_coral_L2": 1,
                "tele_sd_coral_L2": 0,
                "tele_avg_coral_L3": 1,
                "tele_sd_coral_L3": 0,
                "tele_avg_coral_L4": 1,
                "tele_sd_coral_L4": 0,
                "tele_sd_net": 2,
                "tele_sd_processor": 2,
                "cage_percent_success_all": 1,
                "park_percent": 0.33,
                "endgame_avg_total_points": 5,
                "endgame_sd_total_points": 1.14,
                "climb_after_percent_success": 0,
                "avg_expected_cycles": 1.2332,
                "avg_expected_cycle_time": 3.25,
                "cage_percent_success_deep": 0.9,
                "cage_percent_success_shallow": 0.6,
            },
            {
                "team_number": "254",
                "matches_played": 5,
                "auto_avg_coral_L1": 1,
                "auto_sd_coral_L1": 0,
                "auto_avg_coral_L2": 1,
                "auto_sd_coral_L2": 0,
                "auto_avg_coral_L3": 1,
                "auto_sd_coral_L3": 0,
                "auto_avg_coral_L4": 1,
                "auto_sd_coral_L4": 0,
                "auto_avg_net": 3,
                "auto_sd_net": 1,
                "auto_avg_processor": 4,
                "auto_sd_processor": 2,
                "tele_avg_net": 2,
                "tele_avg_processor": 2,
                "tele_avg_coral_L1": 1,
                "tele_sd_coral_L1": 0,
                "tele_avg_coral_L2": 1,
                "tele_sd_coral_L2": 0,
                "tele_avg_coral_L3": 1,
                "tele_sd_coral_L3": 0,
                "tele_avg_coral_L4": 1,
                "tele_sd_coral_L4": 0,
                "tele_sd_net": 2,
                "tele_sd_processor": 2,
                "cage_percent_success_all": 1,
                "park_percent": 0.33,
                "endgame_avg_total_points": 5,
                "endgame_sd_total_points": 1.14,
                "climb_after_percent_success": 0,
                "avg_expected_cycles": 1.2332,
                "avg_expected_cycle_time": 3.25,
                "cage_percent_success_deep": 0.9,
                "cage_percent_success_shallow": 0.6,
            },
            {
                "team_number": "4414",
                "matches_played": 5,
                "auto_avg_coral_L1": 1,
                "auto_sd_coral_L1": 0,
                "auto_avg_coral_L2": 1,
                "auto_sd_coral_L2": 0,
                "auto_avg_coral_L3": 1,
                "auto_sd_coral_L3": 0,
                "auto_avg_coral_L4": 1,
                "auto_sd_coral_L4": 0,
                "auto_avg_net": 3,
                "auto_sd_net": 1,
                "auto_avg_processor": 4,
                "auto_sd_processor": 2,
                "tele_avg_net": 2,
                "tele_avg_processor": 2,
                "tele_avg_coral_L1": 1,
                "tele_sd_coral_L1": 0,
                "tele_avg_coral_L2": 1,
                "tele_sd_coral_L2": 0,
                "tele_avg_coral_L3": 1,
                "tele_sd_coral_L3": 0,
                "tele_avg_coral_L4": 1,
                "tele_sd_coral_L4": 0,
                "tele_sd_net": 2,
                "tele_sd_processor": 2,
                "cage_percent_success_all": 1,
                "park_percent": 0.33,
                "endgame_avg_total_points": 5,
                "endgame_sd_total_points": 1.14,
                "climb_after_percent_success": 0,
                "avg_expected_cycles": 1.2332,
                "avg_expected_cycle_time": 3.25,
                "cage_percent_success_deep": 0.9,
                "cage_percent_success_shallow": 0.6,
            },
            {
                "team_number": "125",
                "matches_played": 5,
                "auto_avg_coral_L1": 1,
                "auto_sd_coral_L1": 0,
                "auto_avg_coral_L2": 1,
                "auto_sd_coral_L2": 0,
                "auto_avg_coral_L3": 1,
                "auto_sd_coral_L3": 0,
                "auto_avg_coral_L4": 1,
                "auto_sd_coral_L4": 0,
                "auto_avg_net": 3,
                "auto_sd_net": 1,
                "auto_avg_processor": 4,
                "auto_sd_processor": 2,
                "tele_avg_net": 2,
                "tele_avg_processor": 2,
                "tele_avg_coral_L1": 1,
                "tele_sd_coral_L1": 0,
                "tele_avg_coral_L2": 1,
                "tele_sd_coral_L2": 0,
                "tele_avg_coral_L3": 1,
                "tele_sd_coral_L3": 0,
                "tele_avg_coral_L4": 1,
                "tele_sd_coral_L4": 0,
                "tele_sd_net": 2,
                "tele_sd_processor": 2,
                "cage_percent_success_all": 1,
                "park_percent": 0.33,
                "endgame_avg_total_points": 5,
                "endgame_sd_total_points": 1.14,
                "climb_after_percent_success": 0,
                "avg_expected_cycles": 1.2332,
                "avg_expected_cycle_time": 3.25,
                "cage_percent_success_deep": 0.9,
                "cage_percent_success_shallow": 0.6,
            },
            {
                "team_number": "5940",
                "matches_played": 5,
                "auto_avg_coral_L1": 1,
                "auto_sd_coral_L1": 0,
                "auto_avg_coral_L2": 1,
                "auto_sd_coral_L2": 0,
                "auto_avg_coral_L3": 1,
                "auto_sd_coral_L3": 0,
                "auto_avg_coral_L4": 1,
                "auto_sd_coral_L4": 0,
                "auto_avg_net": 3,
                "auto_sd_net": 1,
                "auto_avg_processor": 4,
                "auto_sd_processor": 2,
                "tele_avg_net": 2,
                "tele_avg_processor": 2,
                "tele_avg_coral_L1": 1,
                "tele_sd_coral_L1": 0,
                "tele_avg_coral_L2": 1,
                "tele_sd_coral_L2": 0,
                "tele_avg_coral_L3": 1,
                "tele_sd_coral_L3": 0,
                "tele_avg_coral_L4": 1,
                "tele_sd_coral_L4": 0,
                "tele_sd_net": 2,
                "tele_sd_processor": 2,
                "cage_percent_success_all": 1,
                "park_percent": 0.33,
                "endgame_avg_total_points": 5,
                "endgame_sd_total_points": 1.14,
                "climb_after_percent_success": 0,
                "avg_expected_cycles": 1.2332,
                "avg_expected_cycle_time": 3.25,
                "cage_percent_success_deep": 0.9,
                "cage_percent_success_shallow": 0.6,
            },
            {
                "team_number": "1323",
                "matches_played": 5,
                "auto_avg_coral_L1": 1,
                "auto_sd_coral_L1": 0,
                "auto_avg_coral_L2": 1,
                "auto_sd_coral_L2": 0,
                "auto_avg_coral_L3": 1,
                "auto_sd_coral_L3": 0,
                "auto_avg_coral_L4": 1,
                "auto_sd_coral_L4": 0,
                "auto_avg_net": 3,
                "auto_sd_net": 1,
                "auto_avg_processor": 4,
                "auto_sd_processor": 2,
                "tele_avg_net": 2,
                "tele_avg_processor": 2,
                "tele_avg_coral_L1": 1,
                "tele_sd_coral_L1": 0,
                "tele_avg_coral_L2": 1,
                "tele_sd_coral_L2": 0,
                "tele_avg_coral_L3": 1,
                "tele_sd_coral_L3": 0,
                "tele_avg_coral_L4": 1,
                "tele_sd_coral_L4": 0,
                "tele_sd_net": 2,
                "tele_sd_processor": 2,
                "cage_percent_success_all": 1,
                "park_percent": 0.33,
                "endgame_avg_total_points": 5,
                "endgame_sd_total_points": 1.14,
                "climb_after_percent_success": 0,
                "avg_expected_cycles": 1.2332,
                "avg_expected_cycle_time": 3.25,
                "cage_percent_success_deep": 0.9,
                "cage_percent_success_shallow": 0.6,
            },
        ]
        self.tba_team = [
            {
                "team_number": "1678",
                "leave_successes": 5,
                "matches_played": 5,
                "leave_success_rate": 1.0,
            },
            {
                "team_number": "254",
                "leave_successes": 4,
                "matches_played": 5,
                "leave_success_rate": 0.8,
            },
            {
                "team_number": "4414",
                "leave_successes": 3,
                "matches_played": 5,
                "leave_success_rate": 0.6,
            },
            {
                "team_number": "125",
                "leave_successes": 2,
                "matches_played": 5,
                "leave_success_rate": 0.4,
            },
            {
                "team_number": "5940",
                "leave_successes": 1,
                "matches_played": 5,
                "leave_success_rate": 0.2,
            },
            {
                "team_number": "1323",
                "leave_successes": 4,
                "matches_played": 5,
                "leave_success_rate": 0.8,
            },
        ]
        self.tba_match_data = [
            {
                "match_number": 1,
                "comp_level": "qm",
                "key": "2025cmptx_qm1",
                "score_breakdown": {
                    "blue": {
                        "bargeBonusAchieved": True,
                        "coralBonusAchieved": True,
                        "autoBonusAchieved": True,
                        "totalPoints": 278,
                        "autoPoints": 12,
                        "endGameBargePoints": 10,
                        "teleopPoints": 254,
                        "foulPoints": 2,
                        "coopertitionCriteriaMet": True,
                    },
                    "red": {
                        "bargeBonusAchieved": False,
                        "coralBonusAchieved": True,
                        "autoBonusAchieved": True,
                        "totalPoints": 320,
                        "autoPoints": 12,
                        "endGameBargePoints": 10,
                        "teleopPoints": 254,
                        "foulPoints": 2,
                        "coopertitionCriteriaMet": True,
                    },
                },
                "post_result_time": 182,
                "winning_alliance": "red",
            },
            {
                "match_number": 1,
                "comp_level": "qf",
                "key": "2025cmptx_qf1",
                "score_breakdown": {
                    "blue": {
                        "melodyBonusAchieved": True,
                        "ensembleBonusAchieved": True,
                        "totalPoints": 300,
                        "autoPoints": 12,
                        "endGameBargePoints": 10,
                        "teleopPoints": 254,
                        "foulPoints": 2,
                        "coopertitionCriteriaMet": True,
                    },
                    "red": {
                        "melodyBonusAchieved": True,
                        "ensembleBonusAchieved": True,
                        "totalPoints": 400,
                        "autoPoints": 12,
                        "endGameBargePoints": 10,
                        "teleopPoints": 254,
                        "foulPoints": 2,
                        "coopertitionCriteriaMet": True,
                    },
                },
                "post_result_time": 182,
                "winning_alliance": "red",
            },
            {
                "match_number": 3,
                "comp_level": "qm",
                "key": "2025cmptx_qm3",
                "score_breakdown": None,
                "post_result_time": None,
                "winning_alliance": "",
            },
        ]
        self.tba_playoffs_data = [
            {
                "name": "Alliance 1",
                "decines": [],
                "picks": ["frc1678", "frc254", "frc4414"],
                "status": {
                    "playoff_average": None,
                    "level": "f",
                    "record": {"losses": 2, "wins": 6, "ties": 1},
                    "status": "won",
                },
            },
            {
                "name": "Alliance 2",
                "decines": [],
                "picks": ["frc189", "frc345", "frc200", "frc100"],
                "status": {
                    "playoff_average": None,
                    "level": "f",
                    "record": {"losses": 2, "wins": 6, "ties": 1},
                    "status": "won",
                },
            },
        ]
        self.test_server.local_db.insert_documents("obj_team", self.obj_team)
        self.test_server.local_db.insert_documents("tba_team", self.tba_team)

    def test__init_(self):
        """Test if attributes are set correctly"""
        assert self.test_calc.watched_collections == ["obj_team", "tba_team"]
        assert self.test_calc.server == self.test_server

    def test_get_playoffs_alliances(self):
        # TODO: need more tests for this, might break
        with patch("tba_communicator.tba_request", return_value=self.tba_playoffs_data):
            assert self.test_calc.get_playoffs_alliances() == self.expected_playoffs_alliances

    def test_get_actual_values(self):
        """Test getting actual values from TBA"""
        assert self.test_calc.get_actual_values(
            {
                "match_number": 1,
                "alliance_color": "R",
                "team_list": ["1678", "1533", "7229"],
            },
            self.tba_match_data,
        ) == {
            "actual_score": 320,
            "actual_barge_rp": 0.0,
            "actual_coral_rp": 1.0,
            "actual_auto_rp": 1.0,
            "won_match": True,
            "actual_score_auto": 12,
            "actual_score_endgame": 10,
            "actual_score_tele": 244,
            "actual_foul_points": 2,
            "cooperated": True,
        }

        assert self.test_calc.get_actual_values(
            {
                "match_number": 1,
                "alliance_color": "B",
                "team_list": ["1678", "1533", "2468"],
            },
            self.tba_match_data,
        ) == {
            "actual_score": 278,
            "actual_barge_rp": 1.0,
            "actual_coral_rp": 1.0,
            "actual_auto_rp": 1.0,
            "won_match": False,
            "actual_score_auto": 12,
            "actual_score_endgame": 10,
            "actual_score_tele": 244,
            "actual_foul_points": 2,
            "cooperated": True,
        }

        assert self.test_calc.get_actual_values(
            {
                "match_number": 3,
                "alliance_color": "B",
                "team_list": ["1678", "1533", "7229"],
            },
            self.tba_match_data,
        ) == {
            "actual_barge_rp": 0.0,
            "actual_coral_rp": 0.0,
            "actual_auto_rp": 0.0,
            "actual_score": 0,
            "won_match": False,
        }

        assert self.test_calc.get_actual_values(
            {
                "match_number": 3,
                "alliance_color": "R",
                "team_list": ["1678", "1533", "2468"],
            },
            self.tba_match_data,
        ) == {
            "actual_barge_rp": 0.0,
            "actual_coral_rp": 0.0,
            "actual_auto_rp": 0.0,
            "actual_score": 0,
            "won_match": False,
        }

    def test_filter_aims_list(self):
        assert (
            self.test_calc.filter_aims_list(self.obj_team, self.tba_team, self.aims_list)
            == self.filtered_aims_list
        )

    def test_update_predicted_aim(self):
        self.test_server.local_db.delete_data("predicted_aim")
        with patch(
            "tba_communicator.tba_request",
            return_value=self.tba_match_data,
        ):
            assert self.test_calc.update_predicted_aim(self.aims_list) == self.expected_updates

    def test_update_playoffs_alliances(self):
        """Test that we correctly calculate data for each of the playoff alliances"""
        self.test_server.local_db.delete_data("predicted_aim")
        with patch(
            "calculations.predicted_aim.PredictedAimCalc.get_playoffs_alliances",
            return_value=self.expected_playoffs_alliances,
        ):
            assert self.test_calc.update_playoffs_alliances() == self.expected_playoffs_updates_2

    def test_run(self):
        self.test_server.local_db.delete_data("obj_team")
        self.test_server.local_db.delete_data("tba_team")
        self.test_server.local_db.delete_data("predicted_aim")
        self.test_server.local_db.insert_documents("obj_team", self.obj_team)
        self.test_server.local_db.insert_documents("tba_team", self.tba_team)

        with patch(
            "calculations.predicted_aim.PredictedAimCalc.get_aim_list",
            return_value=self.aims_list,
        ), patch(
            "calculations.predicted_aim.PredictedAimCalc.get_teams_list",
            return_value=self.teams_list,
        ), patch(
            "tba_communicator.tba_request",
            side_effect=[{}, self.tba_match_data, self.tba_playoffs_data],
        ):
            self.test_calc.run()

        result = self.test_server.local_db.find("predicted_aim")
        assert len(result) == 6

        for document in result:
            del document["_id"]

        assert result == self.expected_results

        result2 = self.test_server.local_db.find("predicted_alliances")
        for document in result2:
            del document["_id"]

        assert result2 == self.expected_playoffs_updates
