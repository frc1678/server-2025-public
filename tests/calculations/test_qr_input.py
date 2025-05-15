from unittest import mock
from unittest.mock import patch

import logging

import server

import pytest
from pyfakefs.fake_filesystem_unittest import Patcher
import utils


class TestQRInput:
    def setup_method(self, fs):
        with mock.patch("doozernet_communicator.check_model_availability", return_value=None):
            self.test_server = server.Server()
        with mock.patch("builtins.open", mock.mock_open(read_data="1,1,1")), mock.patch(
            "json.load", return_value={}
        ), mock.patch("pandas.read_json", return_value=[]):
            from calculations import qr_input

            self.test_calc = qr_input.QRInput(self.test_server)

    def test_run(self, caplog):
        with patch("adb_communicator.pull_pit_data", return_value=[]), patch(
            "adb_communicator.pull_ss_data", return_value=[]
        ), patch("adb_communicator.pull_qrs", return_value=[]):

            self.test_calc.run(["*test"])
            assert (query := self.test_server.local_db.find("raw_qr"))
            assert "data" in query[0].keys() and query[0]["data"] == "*test"
            assert isinstance(query[0]["ulid"], str)
            assert isinstance(query[0]["readable_time"], str)

            self.test_calc.run(["*test", "test"])
            assert [
                'Invalid QR code not uploaded: "test"',
                "1 duplicate QR codes not uploaded.",
            ] == [rec.message for rec in caplog.records if rec.levelname == "WARNING"]

            self.test_calc.run(["*test2", "+test3", "*test4"])
            assert (query := self.test_server.local_db.find("raw_qr")) and len(query) == 4
