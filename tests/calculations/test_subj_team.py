#!/usr/bin/env python3

import pytest
from unittest.mock import patch
from calculations import subj_team
from server import Server
from utils import dict_near


@pytest.mark.clouddb
class TestSubjTeamCalcs:
    def setup_method(self, method):
        with patch("doozernet_communicator.check_model_availability", return_value=None):
            self.test_server = Server()
        self.test_calcs = subj_team.SubjTeamCalcs(self.test_server)

    def test___init__(self):
        """Test if attributes are set correctly"""
        assert self.test_calcs.watched_collections == ["subj_tim"]
        assert self.test_calcs.server == self.test_server

    def test_teams_played_with(self):
        tims = [
            {
                "match_number": 1,
                "team_number": "1678",
                "alliance_color_is_red": True,
            },
            {
                "match_number": 1,
                "team_number": "4414",
                "alliance_color_is_red": True,
            },
            {
                "match_number": 1,
                "team_number": "1323",
                "alliance_color_is_red": True,
            },
            {
                "match_number": 1,
                "team_number": "3",
                "alliance_color_is_red": False,
            },
            {
                "match_number": 2,
                "team_number": "4",
                "alliance_color_is_red": True,
            },
            {
                "match_number": 3,
                "team_number": "1678",
                "alliance_color_is_red": False,
            },
            {
                "match_number": 3,
                "team_number": "2910",
                "alliance_color_is_red": False,
            },
        ]
        self.test_server.local_db.insert_documents("subj_tim", tims)
        assert self.test_calcs.teams_played_with("1678") == [
            "1678",
            "4414",
            "1323",
            "1678",
            "2910",
        ]

    def test_all_calcs(self):
        tims = [
            {
                "match_number": 1,
                "team_number": "118",
                "agility_score": 2,
                "field_awareness_score": 1,
                "alliance_color_is_red": True,
                "died": False,
                "can_cross_barge": True,
                "high_level_inaccuracy": False,
                "hp_from_team": True,
                "was_tippy": True,
                "time_left_to_climb": 10.0,
            },
            {
                "match_number": 1,
                "team_number": "1678",
                "agility_score": 1,
                "field_awareness_score": 2,
                "alliance_color_is_red": True,
                "died": True,
                "can_cross_barge": True,
                "high_level_inaccuracy": False,
                "hp_from_team": False,
                "was_tippy": True,
                "time_left_to_climb": 0.0,
            },
            {
                "match_number": 1,
                "team_number": "254",
                "agility_score": 3,
                "field_awareness_score": 3,
                "alliance_color_is_red": True,
                "died": True,
                "can_cross_barge": True,
                "high_level_inaccuracy": False,
                "hp_from_team": False,
                "was_tippy": True,
                "time_left_to_climb": 10.0,
            },
            {
                "match_number": 2,
                "team_number": "118",
                "agility_score": 2,
                "field_awareness_score": 1,
                "alliance_color_is_red": True,
                "died": True,
                "can_cross_barge": False,
                "high_level_inaccuracy": True,
                "hp_from_team": True,
                "was_tippy": True,
                "time_left_to_climb": 20.0,
            },
            {
                "match_number": 2,
                "team_number": "1678",
                "agility_score": 3,
                "field_awareness_score": 3,
                "alliance_color_is_red": True,
                "died": True,
                "can_cross_barge": False,
                "high_level_inaccuracy": False,
                "hp_from_team": False,
                "was_tippy": True,
                "time_left_to_climb": 30.0,
            },
            {
                "match_number": 2,
                "team_number": "254",
                "agility_score": 1,
                "field_awareness_score": 2,
                "alliance_color_is_red": True,
                "died": False,
                "can_cross_barge": True,
                "high_level_inaccuracy": True,
                "hp_from_team": False,
                "was_tippy": False,
                "time_left_to_climb": 0.0,
            },
            {
                "match_number": 3,
                "team_number": "118",
                "agility_score": 1,
                "field_awareness_score": 3,
                "alliance_color_is_red": False,
                "died": True,
                "can_cross_barge": True,
                "high_level_inaccuracy": True,
                "hp_from_team": True,
                "was_tippy": False,
                "time_left_to_climb": 10.0,
            },
            {
                "match_number": 3,
                "team_number": "1678",
                "agility_score": 2,
                "field_awareness_score": 2,
                "alliance_color_is_red": False,
                "died": False,
                "can_cross_barge": False,
                "high_level_inaccuracy": True,
                "hp_from_team": True,
                "was_tippy": True,
                "time_left_to_climb": 30.0,
            },
            {
                "match_number": 3,
                "team_number": "254",
                "agility_score": 1,
                "field_awareness_score": 3,
                "alliance_color_is_red": False,
                "died": True,
                "can_cross_barge": True,
                "high_level_inaccuracy": False,
                "hp_from_team": True,
                "was_tippy": True,
                "time_left_to_climb": 20.0,
            },
        ]
        self.test_server.local_db.delete_data("subj_tim")
        self.test_server.local_db.insert_documents("subj_tim", tims)
        with patch(
            "calculations.base_calculations.BaseCalculations.get_teams_list",
            return_value=["118", "254", "1678"],
        ):
            self.test_calcs.run()
        robonauts = self.test_server.local_db.find("subj_team", {"team_number": "118"})[0]
        citrus = self.test_server.local_db.find("subj_team", {"team_number": "1678"})[0]
        chezy = self.test_server.local_db.find("subj_team", {"team_number": "254"})[0]

        for team in [robonauts, citrus, chezy]:
            for datapoint in [
                "_id",
                "unadjusted_field_awareness",
                "unadjusted_agility",
                "test_driver_ability",
            ]:
                team.pop(datapoint)
        expected_robonauts = {
            "team_number": "118",
            "can_cross_barge": True,
            "matches_died": 2,
            "matches_tippy": 2,
            "avg_time_left_to_climb": 10.0,
            "driver_agility": 1.3333333333333333,
            "driver_field_awareness": 0.6666666666666666,
            "defensive_driver_ability": 0.593069989375975,
            "driver_ability": -0.5767216272847042,
            "proxy_driver_ability": 2.7678770283415557,
        }
        assert dict_near(expected_robonauts, robonauts, 0.01)
        expected_citrus = {
            "team_number": "1678",
            "can_cross_barge": False,
            "matches_died": 2,
            "matches_tippy": 3,
            "avg_time_left_to_climb": 30.0,
            "driver_agility": 1.3333333333333333,
            "driver_field_awareness": 1.3333333333333333,
            "defensive_driver_ability": 2.8276058886023683,
            "driver_ability": 1.4066381153285503,
            "proxy_driver_ability": 16.557126948755332,
        }
        assert dict_near(expected_citrus, citrus, 0.01)
        expected_chezy = {
            "team_number": "254",
            "can_cross_barge": True,
            "matches_died": 2,
            "matches_tippy": 2,
            "avg_time_left_to_climb": None,
            "driver_agility": 0.6666666666666666,
            "driver_field_awareness": 1.3333333333333333,
            "defensive_driver_ability": 2.579324122021658,
            "driver_ability": -0.8299164880438433,
            "proxy_driver_ability": 10.674996022903127,
        }
        assert dict_near(expected_chezy, chezy, 0.01)
