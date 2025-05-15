#!/usr/bin/env python3

"""This file tests the functions provided in tba_team that
don't require the database.
"""

from cmath import exp
from calculations import tba_team
import database
import utils
from server import Server
import pytest
from unittest.mock import patch


@pytest.mark.clouddb
class TestTBATeamCalc:
    test_server: Server
    test_calc: tba_team.TBATeamCalc

    def setup_method(self, method):
        with patch("doozernet_communicator.check_model_availability", return_value=None):
            self.test_server = Server()
        self.test_calc = tba_team.TBATeamCalc(self.test_server)

    def test___init__(self):
        """Test if attributes are set correctly"""
        assert self.test_calc.watched_collections == ["obj_tim", "tba_tim"]
        assert self.test_calc.server == self.test_server

    def test_run(self):
        team_names = {
            "data": [
                {
                    "team_number": "973",
                    "nickname": "Greybots",
                },
                {
                    "team_number": "1678",
                    "nickname": "Citrus Circuits",
                },
                {
                    "team_number": "3478",
                    "nickname": "LamBot",
                },
                {
                    "team_number": "1577",
                    "nickname": "Steampunk",
                },
            ]
        }
        team_list = ["973", "1678", "3478", "1577"]
        tba_cache = [
            {
                "api_url": f"event/{Server.TBA_EVENT_KEY}/teams/simple",
                "data": [
                    {
                        "city": "Atascadero",
                        "country": "USA",
                        "key": "frc973",
                        "nickname": "Greybots",
                        "state_prov": "California",
                        "team_number": "973",
                    },
                    {
                        "city": "Davis",
                        "country": "USA",
                        "key": "frc1678",
                        "nickname": "Citrus Circuits",
                        "state_prov": "California",
                        "team_number": "1678",
                    },
                    {"team_number": "3478", "nickname": "LamBot"},
                    {"team_number": "1577", "nickname": "Steampunk"},
                ],
            },
            # Test data created from TBA blog https://blog.thebluealliance.com/2017/10/05/the-math-behind-opr-an-introduction/
            {
                "api_url": f"event/{Server.TBA_EVENT_KEY}/matches",
                "data": [
                    {
                        "alliances": {
                            "red": {"team_keys": ["frc973", "frc1678"]},
                            "blue": {"team_keys": ["frc973", "frc3478"]},
                        },
                        "score_breakdown": {
                            "red": {"foulPoints": 13},
                            "blue": {"foulPoints": 10},
                        },
                    },
                    {
                        "alliances": {
                            "red": {"team_keys": ["frc1678", "frc3478"]},
                            "blue": {"team_keys": ["frc973", "frc1577"]},
                        },
                        "score_breakdown": {
                            "red": {"foulPoints": 15},
                            "blue": {"foulPoints": 7},
                        },
                    },
                ],
            },
        ]
        obj_tims = [
            {
                "incap": 14,
                "confidence_rating": 30,
                "team_number": "973",
                "match_number": 1,
            },
            {
                "incap": 22,
                "confidence_rating": 68,
                "team_number": "973",
                "match_number": 2,
            },
            {
                "incap": 18,
                "confidence_rating": 2,
                "team_number": "973",
                "match_number": 3,
            },
            {
                "incap": 17,
                "confidence_rating": 31,
                "team_number": "1678",
                "match_number": 1,
            },
            {
                "incap": 93,
                "confidence_rating": 14,
                "team_number": "1678",
                "match_number": 2,
            },
            {
                "incap": 15,
                "confidence_rating": 77,
                "team_number": "1678",
                "match_number": 3,
            },
            {
                "incap": 17,
                "confidence_rating": 31,
                "team_number": "3478",
                "match_number": 1,
            },
            {
                "incap": 93,
                "confidence_rating": 14,
                "team_number": "3478",
                "match_number": 2,
            },
            {
                "incap": 15,
                "confidence_rating": 77,
                "team_number": "3478",
                "match_number": 3,
            },
            {
                "incap": 17,
                "confidence_rating": 31,
                "team_number": "1577",
                "match_number": 1,
            },
            {
                "incap": 93,
                "confidence_rating": 14,
                "team_number": "1577",
                "match_number": 2,
            },
            {
                "incap": 15,
                "confidence_rating": 77,
                "team_number": "1577",
                "match_number": 3,
            },
        ]
        tba_tims = [
            {
                "leave": True,
                "match_number": 1,
                "team_number": "973",
            },
            {
                "leave": True,
                "match_number": 2,
                "team_number": "973",
            },
            {
                "leave": False,
                "match_number": 3,
                "team_number": "973",
            },
            {
                "leave": False,
                "match_number": 4,
                "team_number": "973",
            },
            {
                "leave": True,
                "match_number": 5,
                "team_number": "973",
            },
            {
                "leave": False,
                "match_number": 1,
                "team_number": "1678",
            },
            {
                "leave": True,
                "match_number": 2,
                "team_number": "1678",
            },
            {
                "leave": False,
                "match_number": 3,
                "team_number": "1678",
            },
            {
                "leave": False,
                "match_number": 4,
                "team_number": "1678",
            },
            {
                "leave": False,
                "match_number": 5,
                "team_number": "1678",
            },
            {
                "leave": False,
                "match_number": 1,
                "team_number": "3478",
            },
            {
                "leave": False,
                "match_number": 2,
                "team_number": "3478",
            },
            {
                "leave": True,
                "match_number": 3,
                "team_number": "3478",
            },
            {
                "leave": False,
                "match_number": 4,
                "team_number": "3478",
            },
            {
                "leave": False,
                "match_number": 5,
                "team_number": "3478",
            },
            {
                "leave": False,
                "match_number": 1,
                "team_number": "1577",
            },
            {
                "leave": False,
                "match_number": 2,
                "team_number": "1577",
            },
            {
                "leave": True,
                "match_number": 3,
                "team_number": "1577",
            },
            {
                "leave": True,
                "match_number": 4,
                "team_number": "1577",
            },
            {
                "leave": True,
                "match_number": 5,
                "team_number": "1577",
            },
        ]
        expected_results = [
            # Team A
            {
                "team_number": "973",
                "leave_successes": 3,
                "lfm_leave_successes": 2,
                "leave_success_rate": 0.6,
                "team_name": "Greybots",
            },
            # Team B
            {
                "team_number": "1678",
                "leave_successes": 1,
                "lfm_leave_successes": 1,
                "leave_success_rate": 0.2,
                "team_name": "Citrus Circuits",
            },
            # Team C
            {
                "team_number": "3478",
                "leave_successes": 1,
                "lfm_leave_successes": 1,
                "leave_success_rate": 0.2,
                "team_name": "LamBot",
            },
            # Team D
            {
                "team_number": "1577",
                "leave_successes": 3,
                "lfm_leave_successes": 3,
                "leave_success_rate": 0.6,
                "team_name": "Steampunk",
            },
        ]
        self.test_server.local_db.insert_documents("tba_cache", tba_cache)
        self.test_server.local_db.insert_documents("obj_tim", obj_tims)
        self.test_server.local_db.insert_documents("tba_tim", tba_tims)
        with patch("database.Database.get_tba_cache", return_value=team_names), patch(
            "calculations.base_calculations.BaseCalculations.get_teams_list", return_value=team_list
        ):
            self.test_calc.run()
        result = self.test_server.local_db.find("tba_team")
        assert len(result) == 4
        for document in result:
            del document["_id"]
            assert document in expected_results
