import os
import re
import subprocess

import pytest
from unittest.mock import patch
import logging

with patch("logging.getLogger", side_effect=logging.getLogger):
    import utils


def test_constants():
    # Check main directory
    assert __file__.startswith(str(utils.MAIN_DIRECTORY))
    assert re.search(r"server(-\d+)?[/\\]?$", str(utils.MAIN_DIRECTORY))
    assert os.path.exists(utils.MAIN_DIRECTORY)


def test_create_file_path():
    # Test that it creates path by default
    path = utils.create_file_path("test_file_path")
    assert path == os.path.join(utils.MAIN_DIRECTORY, "test_file_path")
    assert os.path.exists(path)

    # Test that it does not create if create_directories=False
    os.rmdir(path)
    path_not_created = utils.create_file_path("test_file_path", False)
    assert path == path_not_created
    assert not os.path.exists(path_not_created)


# Test logging functions

# capsys.readouterr() captures print statements
# caplog.records captures log level


@patch("logging.Logger.error", logging.getLogger(__name__).error)
def test_catch_function_errors(capsys, caplog):
    # Test function
    def test_fun():
        raise ValueError("smth")

    assert utils.catch_function_errors(test_fun) == None
    for record in caplog.records:
        assert record.levelname == "ERROR"
    assert utils.catch_function_errors(int, "1") == 1
    assert utils.catch_function_errors(int, "a") is None


def test_load_tba_event_key_file():
    with open(utils.create_file_path("data/competition.txt")) as file:
        event_key = file.read().rstrip("\n")

    # Test that the function returns what's in the correct file
    assert event_key == utils.load_tba_event_key_file("data/competition.txt")

    # Test that the function returns None when the file path is not found
    assert utils.load_tba_event_key_file("documents/downloads/desktop.txt") is None


def test_run_command():
    with pytest.raises(Exception) as expected_error:
        utils.run_command("foo")  # Should error
    # If 'foo' is in the message it's a useful diagnostic because we know what errored.
    assert "foo" in str(expected_error)

    assert utils.run_command("echo foo", return_output=True) == "foo\n"


def test_get_schema_filenames():
    schema_names = utils.get_schema_filenames()
    assert isinstance(schema_names, list)
    assert "obj_pit_collection_schema.yml" in schema_names


def test_unprefix_schema_dict():
    assert utils.unprefix_schema_dict({"a.b": {"c.d": "e", "f.g": {"h.i": "j"}}}) == {
        "b": {"d": "e", "g": {"i": "j"}}
    }


def test_near():
    assert utils.near(1e-13, 5e-14)
    assert not utils.near(0.000005, 0.0)


def test_dict_near():
    dict1 = {"a": 1e-13, "b": "Something", "d": [1e-13, 2e-13]}
    dict2 = {"a": 1e-14, "b": "Something", "d": [1e-14, 2e-14]}
    dict3 = {"a": 1e-13, "c": "Something", "d": [1e-13, 2e-13]}
    dict4 = {"a": 1e-13, "b": "Something", "c": "Something Else", "d": [1e-13, 2e-13]}
    assert utils.dict_near(dict1, dict2)
    assert not utils.dict_near(dict1, dict3)
    assert not utils.dict_near(dict1, dict4)


def test_dict_near_in():
    dict1 = {"a": 1e-13, "b": "Something"}
    list_of_dicts1 = [
        {"a": 1e-14, "b": "Something"},
        {"a": 1e-13, "c": "Something"},
        {"a": 1e-13, "b": "Something", "c": "Something Else"},
    ]
    list_of_dicts2 = [
        {"a": 1e-13, "c": "Something"},
        {"a": 1e-13, "b": "Something", "c": "Something Else"},
    ]
    assert utils.dict_near_in(dict1, list_of_dicts1)
    assert not utils.dict_near_in(dict1, list_of_dicts2)


def test_near_in():
    float1 = 1e-10
    list_of_floats1 = [1234, 31, 1e-11, 1, "something"]
    list_of_floats2 = [1234, 31, 1e-8, 1, "something"]
    assert utils.near_in(float1, list_of_floats1)
    assert not utils.near_in(float1, list_of_floats2)


def test_find_dict_near_index():
    dict1 = {"a": 1e-13, "b": "Something"}
    list_of_dicts1 = [
        {"a": 1e-13, "c": "Something"},
        {"a": 1e-14, "b": "Something"},
        {"a": 1e-13, "b": "Something", "c": "Something Else"},
    ]
    list_of_dicts2 = [
        {"a": 1e-13, "c": "Something"},
        {"a": 1e-13, "b": "Something", "c": "Something Else"},
    ]
    assert utils.find_dict_near_index(dict1, list_of_dicts1) == 1
    try:
        utils.find_dict_near_index(dict1, list_of_dicts2)
        assert False
    except ValueError:
        assert True
