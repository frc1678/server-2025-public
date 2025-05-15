import pytest

from unittest.mock import Mock, mock_open, patch
import logging

with patch("logging.getLogger", side_effect=logging.getLogger):
    from calculations.base_calculations import BaseCalculations
    from server import Server


@pytest.mark.clouddb
class TestBaseCalculations:
    def setup_method(self, method):
        with patch("doozernet_communicator.check_model_availability", return_value=None), patch(
            "utils.get_match_schedule", return_value=[]
        ), patch("utils.get_team_list", return_value=[]):
            self.test_server = Server()
        self.base_calc = BaseCalculations(self.test_server)

    def test__init__(self):
        assert self.base_calc.server == self.test_server
        assert self.base_calc.watched_collections == NotImplemented

    def test_avg(self):
        # Test if there is no input
        assert None == BaseCalculations.avg("")
        # Test average with no weights
        assert 2 == BaseCalculations.avg([1, 2, 3])
        # Test error if there are a different amount of weights than numbers
        with pytest.raises(ValueError) as num_error:
            BaseCalculations.avg([1, 2], [3, 4, 5])
        assert "Weighted average expects one weight for each number." in str(num_error)
        # Test average with weights
        assert 1 == BaseCalculations.avg([1, 3], [2.0, 0.0])

    def test_get_aim_list(self):
        test_json = """
        {
            "1": 
            {
                "teams": [
                    {"number": "88", "color": "blue"}, 
                    {"number": "2342", "color": "blue"},
                    {"number": "157", "color": "blue"}, 
                    {"number": "4041", "color": "red"},
                    {"number": "1153", "color": "red"},
                    {"number": "2370", "color": "red"}
                ]
            }
        }
        """
        expected_aim_list = [
            {
                "match_number": 1,
                "alliance_color": "B",
                "team_list": ["88", "2342", "157"],
            },
            {
                "match_number": 1,
                "alliance_color": "R",
                "team_list": ["4041", "1153", "2370"],
            },
        ]
        with patch("calculations.base_calculations.open", mock_open(read_data=test_json)):
            assert BaseCalculations.get_aim_list() == expected_aim_list

    @patch("logging.Logger.error", logging.getLogger(__name__).error)
    def test_get_teams_list(self, caplog):
        with patch("calculations.base_calculations.open", mock_open(read_data="[1,2,3]")) as _:
            assert BaseCalculations.get_teams_list() == [1, 2, 3]

        def f(*args):
            raise FileNotFoundError

        with patch("calculations.base_calculations.open", Mock(side_effect=f)):
            assert not BaseCalculations.get_teams_list()
            # Assert that the FileNotFoundError was logged
            assert len([rec.message for rec in caplog.records if rec.levelname == "ERROR"]) == 1
