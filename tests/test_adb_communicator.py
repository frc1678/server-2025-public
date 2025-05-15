import pytest
import unittest
from unittest.mock import *
from calculations import decompressor
import os
import utils
import logging
import logging
import json
import re
from unittest import mock
import database
from pyfakefs.fake_filesystem_unittest import Patcher

with mock.patch("builtins.input", return_value=""):
    import qr_code_uploader

with Patcher() as patcher:
    with patch("calculations.decompressor.Decompressor"):
        with patch("json.load", return_value={"A1B2C3D4": "Test Lenovo Tab 1"}):
            with patch("pandas.read_json", return_value=["Aunish", "Mehul"]):
                with patch("builtins.input", return_value=""):
                    with patch("logging.getLogger", logging.getLogger):
                        with patch("builtins.open", mock_open(read_data="2024arc")):
                            patcher.fs.create_file(
                                utils.create_file_path("data/tablet_serials.json")
                            )
                            import adb_communicator


def return_input(val):
    # used to make qr_code_uploader.upload_qr_codes do nothing
    return val


def test_delete_tablet_downloads():
    real_get_attached_devices = adb_communicator.get_attached_devices
    real_run_command = utils.run_command

    fake_serials = [["A1B2C3D4", "device"], ["E5F6G7H8", "device"], ["I9J1K2L3", "device"]]
    adb_communicator.get_attached_devices = MagicMock(return_value=fake_serials)
    utils.run_command = MagicMock()
    adb_communicator.DEVICE_SERIAL_NUMBERS = {
        "A1B2C3D4": "Fake Lenovo Tab 1",
        "E5F6G7H8": "Fake Lenovo Tab 2",
        "I9J1K2L3": "Fake Lenovo Tab 3",
    }
    adb_communicator.delete_tablet_downloads()
    for i in fake_serials:
        utils.run_command.assert_any_call(f"adb -s {i[0]} shell rm -r /storage/emulated/0/Download")

    adb_communicator.get_attached_devices = real_get_attached_devices
    utils.run_command = real_run_command


def test_get_attached_devices():
    fake_attached_devices = (
        "List of devices attached\nA1B2C3D4\tdevice\nE5F6G7H8\tdevice\nI9J1K2L3\tdevice"
    )
    expected_output = [["A1B2C3D4", "device"], ["E5F6G7H8", "device"], ["I9J1K2L3", "device"]]

    with patch("utils.run_command", return_value=fake_attached_devices):
        assert adb_communicator.get_attached_devices() == expected_output


def test_push_file():
    real_run_command = utils.run_command

    with Patcher() as patcher:
        fake_serial = "A1B2C3D4"
        fake_local_path = "fakepath/path"
        patcher.fs.create_file(fake_local_path)
        fake_tablet_path = "fakedata/fakefile"
        expected_push_command = "adb -s A1B2C3D4 push fakepath/path fakedata/fakefile"
        utils.run_command = MagicMock()

        adb_communicator.push_file(fake_serial, fake_local_path, fake_tablet_path)
        utils.run_command.assert_called_once_with(expected_push_command)

    utils.run_command = real_run_command


def test_uninstall_app():
    real_run_command = utils.run_command

    with Patcher() as patcher:
        # returns app name so that the app to uninstall is in installed_apps
        utils.run_command = MagicMock(return_value="com.frc1678.match_collection")
        fake_serial = "A1B2C3D4"

        adb_communicator.uninstall_app(fake_serial)
        utils.run_command.assert_any_call(
            "adb -s A1B2C3D4 shell pm list packages -3", return_output=True
        )
        utils.run_command.assert_any_call("adb -s A1B2C3D4 uninstall com.frc1678.match_collection")

    utils.run_command = real_run_command


def test_pull_device_files():
    real_get_attached_devices = adb_communicator.get_attached_devices
    real_run_command = utils.run_command

    with Patcher() as patcher:
        fake_serials = [["A1B2C3D4", "device"], ["E5F6G7H8", "device"], ["I9J1K2L3", "device"]]
        adb_communicator.get_attached_devices = MagicMock(return_value=fake_serials)
        utils.run_command = MagicMock()
        fake_tablet_path = "fakedata/fakefile"
        fake_local_path = "fakepath/path"
        patcher.fs.create_dir(fake_local_path)

        for i in fake_serials:
            adb_communicator.pull_device_files(fake_local_path, fake_tablet_path, devices=[i[0]])
            utils.run_command.assert_called_with(
                f"adb -s {i[0]} pull fakedata/fakefile fakepath/path/{i[0]}"
            )

    adb_communicator.get_attached_devices = real_get_attached_devices
    utils.run_command = real_run_command


def test_adb_remove_files():
    real_get_attached_devices = adb_communicator.get_attached_devices
    real_run_command = utils.run_command

    fake_serials = [["A1B2C3D4", "device"], ["E5F6G7H8", "device"], ["I9J1K2L3", "device"]]
    adb_communicator.get_attached_devices = MagicMock(return_value=fake_serials)
    utils.run_command = MagicMock()
    fake_tablet_path = "fakedata/fakefile"

    adb_communicator.adb_remove_files(fake_tablet_path)
    for i in fake_serials:
        utils.run_command.assert_any_call(f"adb -s {i[0]} shell rm -r fakedata/fakefile")

    adb_communicator.get_attached_devices = real_get_attached_devices
    utils.run_command = real_run_command


def test_pull_device_data():
    real_pull_device_files = adb_communicator.pull_device_files
    real_upload_qr_codes = qr_code_uploader.upload_qr_codes
    real_get_attached_devices = adb_communicator.get_attached_devices

    with Patcher() as patcher:
        adb_communicator.pull_device_files = Mock()
        fake_serials = ["A1B2C3D4", "E5F6G7H8", "I9J1K2L3", "RABCDEFG"]
        fake_qr_data = [
            "+A1$B66$C4711453624$D8.1.10$ETom$FFALSE%UTrue$VPARKED$W151AA135AU098AO088AN066AN048AP047AO039AO033AO031AO028AQ$X1$Y21$Z766",
            "+A1$B44$C7978641999$D3.6.7$EAnn$FFALSE%UFalse$VNONE$W135AU126BE103AN090AO077AO076AQ060AO051AO046AP045AO033AN028AP$X1$Y29$Z253",
            "+A1$B59$C6574274972$D10.6.6$ESusan$FFALSE%UTrue$VPARKED$W144BD143AJ135AU134AP129AO094AP093AP092AQ086AO084AP076AP070AQ067AN066AN058AO050AP043AQ042AN035AO034AN028AO017AN$X4$Y11$Z5419insertqr3here",
        ]
        qr_code_uploader.upload_qr_codes = MagicMock(side_effect=return_input)
        fake_dir_path = utils.create_file_path("data/devices")
        adb_communicator.DEVICE_SERIAL_NUMBERS = {
            "A1B2C3D4": "Fake Lenovo Tab 1",
            "E5F6G7H8": "Fake Lenovo Tab 2",
            "I9J1K2L3": "Fake Lenovo Tab 3",
            "RABCDEFG": "Fake Lenovo Tab 4",
        }
        adb_communicator.get_attached_devices = Mock(return_value=fake_serials)
        for i in range(3):
            fake_tablet_dir = utils.create_file_path(f"data/devices/{fake_serials[i]}")
            patcher.fs.create_file(f"{fake_tablet_dir}/qrdatathing.txt", contents=fake_qr_data[i])

        # this stuff is for fixing a bug with pyfakefs breaking os.listdir
        def listdirfix(path):
            if path == fake_dir_path:
                return fake_serials
            elif path == f"{fake_dir_path}/{fake_serials[3]}":
                return ["Mehul"]
            else:
                return ["qrdatathing.txt"]

        test_ss_tims_data = [
            {
                "team_number": "1678",
                "username": "Mehul",
                "match_number": 1,
                "played_defense": True,
                "defense_rating": 5,
            },
            {
                "team_number": "1678",
                "username": "Mehul",
                "match_number": 2,
                "played_defense": True,
                "defense_rating": 4,
            },
            {
                "team_number": "1678",
                "username": "Mehul",
                "match_number": 3,
                "played_defense": True,
                "defense_rating": 9,
            },
            {
                "team_number": "254",
                "username": "Mehul",
                "match_number": 1,
                "played_defense": False,
                "defense_rating": -1,
            },
            {
                "team_number": "254",
                "username": "Mehul",
                "match_number": 2,
                "played_defense": False,
                "defense_rating": -1,
            },
            {
                "team_number": "254",
                "username": "Mehul",
                "match_number": 3,
                "played_defense": True,
                "defense_rating": 6,
            },
        ]
        test_team_data = {
            "1678": {
                "strengths": "testwow",
            },
            "254": {
                "strengths": "testwow",
            },
        }
        expected_ss_team = [
            {
                "team_number": "1678",
                "auto_strategies_team": None,
                "avg_defense_rating": 6.0,
                "avg_defense_rating_squared": 36.0,
                "can_intake_ground": None,
                "strengths": "testwow",
                "team_notes": None,
                "weaknesses": None,
            },
            {
                "team_number": "254",
                "auto_strategies_team": None,
                "avg_defense_rating": 6.0,
                "avg_defense_rating_squared": 36.0,
                "can_intake_ground": None,
                "strengths": "testwow",
                "team_notes": None,
                "weaknesses": None,
            },
        ]
        test_db = database.Database()
        test_db.insert_documents("ss_tim", test_ss_tims_data)
        real_db = database.Database
        database.Database = MagicMock(return_value=test_db)
        patcher.fs.create_file(
            f"{fake_dir_path}/RABCDEFG/Mehul/team_data.json",
            contents=json.dumps(test_team_data),
        )
        patcher.fs.create_file(f"{fake_dir_path}/RABCDEFG/Mehul/tim_data.json", contents="{}")
        patcher.fs.add_real_file(utils.create_file_path("schema/calc_ss_team.yml"))

        with patch(
            "pyfakefs.fake_filesystem_unittest.fake_os.FakeOsModule.listdir", side_effect=listdirfix
        ):
            with patch("re.fullmatch", return_value=True):
                test_data = adb_communicator.pull_device_data()
        assert test_data == {"qr": fake_qr_data, "raw_obj_pit": []}
        result_ss_team = test_db.find("ss_team")
        inserted_documents = False
        for document in result_ss_team:
            document.pop("_id")
            document.pop("username")
            inserted_documents = True
            if document["team_number"] == "254":
                assert document == expected_ss_team[1]
            else:
                assert document == expected_ss_team[0]
        assert inserted_documents
    database.Database = real_db
    adb_communicator.pull_device_files = real_pull_device_files
    qr_code_uploader.upload_qr_codes = real_upload_qr_codes
    adb_communicator.get_attached_devices = real_get_attached_devices


def test_pull_qr_data():
    real_db = database.Database
    real_pull_device_files = adb_communicator.pull_device_files
    real_upload_qr_codes = qr_code_uploader.upload_qr_codes
    real_get_attached_devices = adb_communicator.get_attached_devices
    with Patcher() as patcher:
        adb_communicator.pull_device_files = Mock()
        fake_serials = ["A1B2C3D4", "E5F6G7H8", "I9J1K2L3"]
        fake_qr_data = [
            "+A1$B66$C4711453624$D8.1.10$EJelly$FFALSE%UTrue$VPARKED$W151AA135AU098AO088AN066AN048AP047AO039AO033AO031AO028AQ$X1$Y21$Z766",
            "+A1$B44$C7978641999$D3.6.7$EAlison$FFALSE%UFalse$VNONE$W135AU126BE103AN090AO077AO076AQ060AO051AO046AP045AO033AN028AP$X1$Y29$Z253",
            "+A1$B59$C6574274972$D10.6.6$EScoutingisbest$FFALSE%UTrue$VPARKED$W144BD143AJ135AU134AP129AO094AP093AP092AQ086AO084AP076AP070AQ067AN066AN058AO050AP043AQ042AN035AO034AN028AO017AN$X4$Y11$Z5419insertqr3here",
        ]
        qr_code_uploader.upload_qr_codes = MagicMock(side_effect=return_input)
        fake_dir_path = utils.create_file_path("data/devices")
        adb_communicator.DEVICE_SERIAL_NUMBERS = {
            "A1B2C3D4": "Fake Lenovo Tab 1",
            "E5F6G7H8": "Fake Lenovo Tab 2",
            "I9J1K2L3": "Fake Lenovo Tab 3",
        }
        adb_communicator.get_attached_devices = Mock(return_value=fake_serials)
        # Create the fake qr file
        for i in range(3):
            fake_tablet_dir = utils.create_file_path(f"data/devices/{fake_serials[i]}")
            patcher.fs.create_file(f"{fake_tablet_dir}/qrdatathing.txt", contents=fake_qr_data[i])

        # this stuff is for fixing a bug with pyfakefs breaking os.listdir
        def listdirfix(path):
            if path == fake_dir_path:
                return fake_serials
            else:
                return ["qrdatathing.txt"]

        test_db = database.Database()
        database.Database = MagicMock(return_value=test_db)
        with patch(
            "pyfakefs.fake_filesystem_unittest.fake_os.FakeOsModule.listdir", side_effect=listdirfix
        ):
            with patch("re.fullmatch", return_value=True):
                test_data = adb_communicator.pull_qr_data()
    database.Database = real_db
    adb_communicator.pull_device_files = real_pull_device_files
    qr_code_uploader.upload_qr_codes = real_upload_qr_codes
    adb_communicator.get_attached_devices = real_get_attached_devices
    assert test_data == {"qr": fake_qr_data, "raw_obj_pit": []}


def test_pull_pit_data():
    real_db = database.Database
    real_pull_device_files = adb_communicator.pull_device_files
    real_upload_qr_codes = qr_code_uploader.upload_qr_codes
    real_get_attached_devices = adb_communicator.get_attached_devices
    with Patcher() as patcher:
        adb_communicator.pull_device_files = Mock()
        fake_serials = ["A1B2C3D4", "E5F6G7H8", "I9J1K2L3"]
        fake_dir_path = utils.create_file_path("data/devices/")
        fake_device_paths = []
        for i in range(3):
            fake_device_paths.append(utils.create_file_path(f"data/devices/{fake_serials[i]}"))
        adb_communicator.DEVICE_SERIAL_NUMBERS = {
            "A1B2C3D4": "Fake Lenovo Tab 1",
            "E5F6G7H8": "Fake Lenovo Tab 2",
            "I9J1K2L3": "Fake Lenovo Tab 3",
        }
        fake_pit_data = [
            {
                "1678": {
                    "drivetrain": 3,
                    "algae_score_mech": 2,
                    "algae_intake_mech": 2,
                    "reef_score_ability": 4,
                    "can_leave": True,
                    "has_processor_mech": True,
                    "weight": 100.0,
                }
            },
            {
                "1679": {
                    "drivetrain": 3,
                    "algae_score_mech": 2,
                    "algae_intake_mech": 2,
                    "reef_score_ability": 4,
                    "can_leave": True,
                    "has_processor_mech": True,
                    "weight": 100.0,
                }
            },
            {
                "1680": {
                    "drivetrain": 3,
                    "algae_score_mech": 2,
                    "algae_intake_mech": 2,
                    "reef_score_ability": 4,
                    "can_leave": True,
                    "has_processor_mech": True,
                    "weight": 100.0,
                }
            },
        ]
        expected_pit = [
            {
                "team_number": "1678",
                "can_leave": True,
                "drivetrain": "swerve",
                "algae_score_mech": "processor",
                "algae_intake_mech": "reef",
                "reef_score_ability": 4,
                "has_processor_mech": True,
                "weight": 100.0,
                "coral_intake_mech": None,
                "max_climb": None,
            },
            {
                "team_number": "1679",
                "can_leave": True,
                "drivetrain": "swerve",
                "algae_score_mech": "processor",
                "algae_intake_mech": "reef",
                "reef_score_ability": 4,
                "has_processor_mech": True,
                "weight": 100.0,
                "coral_intake_mech": None,
                "max_climb": None,
            },
            {
                "team_number": "1680",
                "can_leave": True,
                "drivetrain": "swerve",
                "algae_score_mech": "processor",
                "algae_intake_mech": "reef",
                "reef_score_ability": 4,
                "has_processor_mech": True,
                "weight": 100.0,
                "coral_intake_mech": None,
                "max_climb": None,
            },
        ]
        adb_communicator.get_attached_devices = Mock(return_value=fake_serials)
        try:
            patcher.fs.create_dir(fake_dir_path)
        except FileExistsError:
            print("Directory already exists!!!!")
            print(fake_dir_path)
            print(os.listdir(fake_dir_path))
        for i in range(3):
            fake_tablet_dir = utils.create_file_path(f"data/devices/{fake_serials[i]}/pit_data")
            patcher.fs.create_file(
                f"{fake_tablet_dir}/pit_data.json",
                contents=str(fake_pit_data[i]).replace("'", '"').replace("True", "true"),
                encoding="utf-8",
            )

        test_db = database.Database()
        database.Database = MagicMock(return_value=test_db)
        with patch("re.fullmatch", return_value=True):
            with patch(
                "pyfakefs.fake_filesystem_unittest.fake_os.FakeOsModule.listdir",
                side_effect=os.listdir,
            ):
                adb_communicator.pull_pit_data()
                test_data = test_db.find("raw_obj_pit")
                for team in test_data:
                    team.pop("_id")
    database.Database = real_db
    adb_communicator.pull_device_files = real_pull_device_files
    qr_code_uploader.upload_qr_codes = real_upload_qr_codes
    adb_communicator.get_attached_devices = real_get_attached_devices
    assert test_data == expected_pit


def test_pull_ss_data():
    real_db = database.Database
    real_pull_device_files = adb_communicator.pull_device_files
    real_upload_qr_codes = qr_code_uploader.upload_qr_codes
    real_get_attached_devices = adb_communicator.get_attached_devices
    with Patcher() as patcher:
        adb_communicator.pull_device_files = Mock()
        fake_serials = ["A1B2C3D4", "E5F6G7H8", "I9J1K2L3", "RABCDEFG"]
        fake_dir_path = utils.create_file_path("data/devices")
        adb_communicator.DEVICE_SERIAL_NUMBERS = {
            "A1B2C3D4": "Fake Lenovo Tab 1",
            "E5F6G7H8": "Fake Lenovo Tab 2",
            "I9J1K2L3": "Fake Lenovo Tab 3",
            "RABCDEFG": "Fake Lenovo Tab 4",
        }
        test_ss_tims_data = [
            {
                "team_number": "1678",
                "username": "Mehul",
                "match_number": 1,
                "played_defense": True,
                "defense_rating": 5,
                "tim_auto_strategies": "test1",
            },
            {
                "team_number": "1678",
                "username": "Mehul",
                "match_number": 2,
                "played_defense": True,
                "defense_rating": 4,
                "tim_auto_strategies": "test2",
            },
            {
                "team_number": "1678",
                "username": "Mehul",
                "match_number": 3,
                "played_defense": True,
                "defense_rating": 9,
                "tim_auto_strategies": "test3",
            },
            {
                "team_number": "254",
                "username": "Mehul",
                "match_number": 1,
                "played_defense": False,
                "defense_rating": -1,
                "tim_auto_strategies": "test4",
            },
            {
                "team_number": "254",
                "username": "Mehul",
                "match_number": 2,
                "played_defense": False,
                "defense_rating": -1,
                "tim_auto_strategies": "test5",
            },
            {
                "team_number": "254",
                "username": "Mehul",
                "match_number": 3,
                "played_defense": True,
                "defense_rating": 6,
                "tim_auto_strategies": "test6",
            },
        ]
        test_team_data = {
            "1678": {
                "team_notes": "abcd",
            },
            "254": {
                "team_notes": "efgh",
            },
        }
        expected_ss_team = [
            {
                "team_number": "1678",
                "auto_strategies_team": "MATCH 1:\ntest1\n\nMATCH 2:\ntest2\n\nMATCH 3:\ntest3\n\n",
                "avg_defense_rating": 6.0,
                "avg_defense_rating_squared": 36.0,
                "can_intake_ground": None,
                "strengths": None,
                "team_notes": "abcd",
                "weaknesses": None,
            },
            {
                "team_number": "254",
                "auto_strategies_team": "MATCH 1:\ntest4\n\nMATCH 2:\ntest5\n\nMATCH 3:\ntest6\n\n",
                "avg_defense_rating": 6.0,
                "avg_defense_rating_squared": 36.0,
                "can_intake_ground": None,
                "strengths": None,
                "team_notes": "efgh",
                "weaknesses": None,
            },
        ]
        adb_communicator.get_attached_devices = Mock(return_value=fake_serials)

        # this stuff is for fixing a bug with pyfakefs breaking os.listdir
        def listdirfix(path):
            if path == fake_dir_path:
                return fake_serials
            elif path == f"{fake_dir_path}/{fake_serials[3]}":
                return ["Mehul"]

        test_db = database.Database()
        test_db.insert_documents("ss_tim", test_ss_tims_data)
        database.Database = MagicMock(return_value=test_db)
        patcher.fs.create_file(
            f"{fake_dir_path}/RABCDEFG/Mehul/team_data.json",
            contents=json.dumps(test_team_data),
        )
        patcher.fs.create_file(f"{fake_dir_path}/RABCDEFG/Mehul/tim_data.json", contents="{}")
        patcher.fs.add_real_file(utils.create_file_path("schema/calc_ss_team.yml"))

        with patch(
            "pyfakefs.fake_filesystem_unittest.fake_os.FakeOsModule.listdir", side_effect=listdirfix
        ):
            with patch("re.fullmatch", return_value=True):
                with patch("utils.get_team_list", return_value=["1678", "254"]):
                    test_data = adb_communicator.pull_ss_data(test_db)
        result_ss_team = test_db.find("ss_team")
        inserted_documents = False
        for document in result_ss_team:
            document.pop("_id")
            document.pop("username")
            inserted_documents = True
            if document["team_number"] == "254":
                assert document == expected_ss_team[1]
            else:
                assert document == expected_ss_team[0]
        assert inserted_documents
    database.Database = real_db
    adb_communicator.pull_device_files = real_pull_device_files
    qr_code_uploader.upload_qr_codes = real_upload_qr_codes
    adb_communicator.get_attached_devices = real_get_attached_devices


def test_validate_apk():
    real_run_command = utils.run_command

    utils.run_command = MagicMock()
    fake_serial = "A1B2C3D4"
    fake_local_path = "fakedir/fakeapk.apk"
    adb_communicator.validate_apk(fake_serial, fake_local_path)
    utils.run_command.assert_any_call(
        "adb -s A1B2C3D4 install -r fakedir/fakeapk.apk", return_output=True
    )

    utils.run_command = real_run_command


def test_adb_font_size_enforcer():
    real_get_attached_devices = adb_communicator.get_attached_devices
    real_run_command = utils.run_command

    fake_serials = [["A1B2C3D4", "device"], ["E5F6G7H8", "device"], ["I9J1K2L3", "device"]]
    adb_communicator.get_attached_devices = MagicMock(return_value=fake_serials)
    utils.run_command = MagicMock()

    adb_communicator.adb_font_size_enforcer()
    for i in fake_serials:
        utils.run_command.assert_any_call(
            f"adb -s {i[0]} shell settings put system font_scale 1.30", return_output=False
        )

    adb_communicator.get_attached_devices = real_get_attached_devices
    utils.run_command = real_run_command


def test_get_tablet_file_path_hash():
    real_run_command = utils.run_command

    with Patcher() as patcher:
        utils.run_command = MagicMock(return_value="mocked!")
        fake_serial = "A1B2C3D4"
        fake_tablet_path = "fakedir/fakefile"

        assert (
            adb_communicator.get_tablet_file_path_hash(fake_serial, fake_tablet_path) == "mocked!"
        )
        utils.run_command.assert_called_once_with(
            f"adb -s A1B2C3D4 shell sha256sum -b fakedir/fakefile", return_output=True
        )

    utils.run_command = real_run_command
