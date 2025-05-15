#!/usr/bin/env python3
from calculations import subj_team
import pytest
from unittest.mock import patch
from server import Server
import database

db = database.Database()


@pytest.mark.clouddb
class TestSubjTimCalcs:
    def setup_method(self):
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
        ]
        self.test_server.local_db.insert_documents("subj_tim", tims)

    def test_calcs(self):
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
        ]
        expected_unadjusted_ability_calcs = {
            "avg_time_left_to_climb": 10.0,
            "can_cross_barge": True,
            "matches_died": 2,
            "matches_tippy": 2,
            "team_number": "118",
            "unadjusted_agility": 2.0,
            "unadjusted_field_awareness": 1.0,
        }
        self.test_server.local_db.delete_data("subj_tim")
        self.test_server.local_db.insert_documents("subj_tim", tims)
        # test calculation that uses subj_tim data
        assert self.test_calcs.unadjusted_ability_calcs("118") == expected_unadjusted_ability_calcs
