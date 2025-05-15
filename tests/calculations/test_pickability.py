import pytest

from unittest import mock

from calculations import pickability
from server import Server


FAKE_SCHEMA = {
    "calculations": {
        "first_pickability": {
            "type": "float",
            "datapoint1": 1,
            "datapoint2": 1,
        },
        "offensive_second_pickability": {
            "type": "float",
            "datapoint2": 1,
            "datapoint1": 4,
        },
        "defensive_second_pickability": {
            "type": "float",
            "datapoint2": 1,
            "datapoint1": 2,
        },
    },
}


@pytest.mark.clouddb
class TestPickability:
    @staticmethod
    def test__init__():
        with mock.patch(
            "doozernet_communicator.check_model_availability", return_value=None
        ), mock.patch("utils.get_match_schedule", return_value=[]), mock.patch(
            "utils.get_team_list", return_value=[]
        ):
            m_server = Server()
        with mock.patch("utils.read_schema", return_value=FAKE_SCHEMA):
            test_calc = pickability.PickabilityCalc(m_server)
        assert test_calc.server == m_server

    @staticmethod
    @mock.patch("utils.read_schema", return_value=FAKE_SCHEMA)
    def test_calculate_pickabilty(mock_):
        with mock.patch(
            "doozernet_communicator.check_model_availability", return_value=None
        ), mock.patch("utils.get_match_schedule", return_value=[]), mock.patch(
            "utils.get_team_list", return_value=[]
        ), mock.patch(
            "utils.read_schema", return_value=FAKE_SCHEMA
        ):
            test_calc = pickability.PickabilityCalc(Server())
        calc_data = {
            "team_number": "0",
            "datapoint1": 2,
            "datapoint2": 1,
            "useless": None,
        }
        assert test_calc.calculate_pickability("first_pickability", calc_data) == 3
        assert test_calc.calculate_pickability("offensive_second_pickability", calc_data) == 9
        assert test_calc.calculate_pickability("defensive_second_pickability", calc_data) == 5
        assert test_calc.calculate_pickability("first_pickability", {}) == 0
        # Check that if the datapoint is missing that it correctly returns None
        calc_data = {
            "team_number": "0",
            "datapoint1": 2,
            "datapoint2": 1,
            "useless": None,
        }
        assert test_calc.calculate_pickability("first_pickability", calc_data) == 3

    @staticmethod
    @mock.patch("utils.read_schema", return_value=FAKE_SCHEMA)
    @mock.patch("tba_communicator.tba_request", return_value={})
    def test_run(schema_mock, tba_mock):
        with mock.patch(
            "doozernet_communicator.check_model_availability", return_value=None
        ), mock.patch("utils.get_match_schedule", return_value=[]), mock.patch(
            "utils.get_team_list", return_value=["0", "1", "2"]
        ):
            server_obj = Server()
        test_calc = pickability.PickabilityCalc(server_obj)

        # This is not enough to do a pickability calc, it needs the test2 datapoint
        server_obj.local_db.insert_documents(
            "obj_team", {"team_number": "0", "datapoint1": 1, "datapoint2": 5}
        )
        with mock.patch(
            "calculations.pickability.PickabilityCalc.calc_offensive_2nd_pickability",
            return_value=(0, 0),
        ):
            test_calc.run()
        assert server_obj.local_db.find("pickability")

        # Insert all the required data
        server_obj.local_db.insert_documents(
            "obj_team", {"team_number": "1", "datapoint1": 1, "datapoint2": 3}
        )
        with mock.patch(
            "calculations.pickability.PickabilityCalc.calc_offensive_2nd_pickability",
            return_value=(0, 0),
        ):
            test_calc.run()
        result = server_obj.local_db.find("pickability", {"team_number": "1"})
        del result[0]["_id"]
        assert result[0] == {
            "team_number": "1",
            "defensive_second_pickability": 5,
            "first_pickability": 4,
            "offensive_second_pickability": 0,
        }

        # Test updating the function
        server_obj.local_db.delete_data("test2")
        server_obj.local_db.insert_documents(
            "obj_team", {"team_number": "2", "datapoint1": 2000000, "datapoint2": 20}
        )
        with mock.patch(
            "calculations.pickability.PickabilityCalc.calc_offensive_2nd_pickability",
            return_value=(0, 0),
        ):
            test_calc.run()
        new_result = server_obj.local_db.find("pickability", {"team_number": "2"})
        del new_result[0]["_id"]
        assert result != new_result
