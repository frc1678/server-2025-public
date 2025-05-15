"""Tests database.py"""

import pymongo
import pymongo.collection
import yaml
from unittest.mock import patch
import logging
import pytest
import bson
import time
from unittest import mock
import collections as collections_module

import database
from server import Server

CLIENT = pymongo.MongoClient("localhost", 1678)
TEST_DATABASE_NAME = "test" + Server.TBA_EVENT_KEY
# Helps execute tests
TEST_DB_HELPER = CLIENT[TEST_DATABASE_NAME]
# The actual class to be tested
TEST_DB_ACTUAL = database.Database()


with open("schema/collection_schema.yml", "r") as collection_schema:
    collections = yaml.load(collection_schema, yaml.Loader)


class TestDatabase:
    def test_init(self):
        """Tests if the init method properly assigns properties of the db class"""
        assert TEST_DB_ACTUAL.connection == "localhost"
        assert TEST_DB_ACTUAL.port == 1678
        assert TEST_DB_ACTUAL.db.name == TEST_DATABASE_NAME
        test_db = database.Database(connection="test", port=80)
        assert test_db.connection == "test"
        assert test_db.port == 80
        assert test_db.db.name == TEST_DATABASE_NAME
        assert test_db.name == TEST_DATABASE_NAME

    def test_schema(self):
        """Compares the schema load to the one in the db file"""
        assert collections == database.COLLECTION_SCHEMA

    def test_check_col_name(self, caplog):
        """Checks collection name checker"""
        with patch("logging.Logger.warning", side_effect=logging.getLogger(__name__).warning):
            database.check_collection_name(TEST_DATABASE_NAME)
        assert [f'Unexpected collection name: "{TEST_DATABASE_NAME}"'] == [
            rec.message for rec in caplog.records if rec.levelname == "WARNING"
        ]

    def test_indexes(self):
        """Checks if all indexes are added properly"""
        TEST_DB_ACTUAL.set_indexes()
        for collection in collections["collections"]:
            collection_dict = collections["collections"][collection]
            if collection_dict["indexes"] is not None:
                for index in collection_dict["indexes"]:
                    for db_index in TEST_DB_HELPER[collection].list_indexes():
                        if db_index == "name":
                            db_index_fields = dict(db_index)["name"][0].split("_")
                            for field in index:
                                assert field in db_index_fields

    def test_find(self):
        """Tests database find"""
        TEST_DB_HELPER.test.insert_one({"test": "test"})
        assert TEST_DB_ACTUAL.find("test", {"test": "test"}) == [TEST_DB_HELPER.test.find_one({})]

    def test_get_tba_cache(self):
        """Tests tba cache read"""
        TEST_DB_HELPER.tba_cache.insert_one({"api_url": "test"})
        assert TEST_DB_ACTUAL.get_tba_cache("test") == TEST_DB_HELPER.tba_cache.find_one(
            {"api_url": "test"}
        )

    def test_update_tba_cache(self):
        """Tests updating the tba cache"""
        TEST_DB_ACTUAL.update_tba_cache([{"data": "a"}], "test")
        test_cache = TEST_DB_HELPER.tba_cache.find_one({})
        assert test_cache["api_url"] == "test"
        assert test_cache["data"] == [{"data": "a"}]
        TEST_DB_ACTUAL.update_tba_cache({"data": "b"}, "test")
        test_cache = TEST_DB_HELPER.tba_cache.find_one({})
        assert test_cache["api_url"] == "test"
        assert test_cache["data"] == {"data": "b"}
        TEST_DB_ACTUAL.update_tba_cache({"a": "b"}, "test2", "ETAG")
        test_cache = TEST_DB_HELPER.tba_cache.find_one({"api_url": "test2"})
        del test_cache["_id"]
        assert test_cache == {"data": {"a": "b"}, "etag": "ETAG", "api_url": "test2"}

    def test_delete_data(self):
        """Tests deletion of data"""
        TEST_DB_HELPER.test.insert_many([{"test": "test"}, {"test1": "test1"}])
        TEST_DB_ACTUAL.delete_data("test", {"test": "test"})
        assert TEST_DB_HELPER.test.find_one({})["test1"] == "test1"

    def test_insert_documents(self):
        """Tests insertion of documents"""
        TEST_DB_ACTUAL.insert_documents("test", [{"test": "a"}])
        assert TEST_DB_HELPER.test.find_one({})["test"] == "a"
        TEST_DB_ACTUAL.insert_documents("test", {"test_2": "b"})
        assert TEST_DB_HELPER.test.find_one({"test_2": "b"})

    def test_update_document(self):
        """Tests updating of documents"""
        TEST_DB_HELPER.test.insert_one({"test": "a"})
        TEST_DB_ACTUAL.update_document("test", {"test_1": "b"}, {"test": "a"})
        test_cache = TEST_DB_HELPER.test.find_one({})
        assert test_cache["test"] == "a"
        assert test_cache["test_1"] == "b"
        TEST_DB_ACTUAL.update_document("test", {"test_2": "c"}, {"test": "a"})
        assert TEST_DB_HELPER.test.find_one({"test_2": "c"})["test_2"] == "c"

    def test_update_qr_blocklist_status(self):
        """Tests blocklisting of qrs"""
        TEST_DB_HELPER.raw_qr.insert_one(
            {
                "data": "test_qr_string",
                "blocklisted": False,
                "override": {},
                "epoch_time": 1641525570,
                "readable_time": "Thursday, January 6, 2022 7:19:30 PM",
            }
        )
        TEST_DB_ACTUAL.update_qr_blocklist_status({"data": "test_qr_string"})
        test_qr = TEST_DB_HELPER.raw_qr.find_one({})
        assert test_qr["blocklisted"] == True

    def test_update_qr_data_override(self):
        """Tests data override of qrs"""
        TEST_DB_HELPER.raw_qr.insert_one(
            {
                "data": "test_override_qr_string",
                "blocklisted": False,
                "override": {},
                "epoch_time": 1641525570,
                "readable_time": "Sunday, February 5, 2023 4:31:13 PM",
            }
        )
        TEST_DB_ACTUAL.update_qr_data_override(
            {"data": "test_override_qr_string"}, "test", "something"
        )
        test_qr = TEST_DB_HELPER.raw_qr.find_one({})
        assert test_qr["override"] == {"test": "something"}

    def test_bulk_write(self):
        operations = [
            pymongo.InsertOne({"data": 1}),
            pymongo.UpdateOne({"data": 5}, {"$set": {"data": 2}}),
            pymongo.InsertOne({"data": 2}),
        ]
        TEST_DB_ACTUAL.bulk_write("raw_qr", operations)
        result = TEST_DB_ACTUAL.find("raw_qr")
        assert result[0]["data"] == 1
        assert result[1]["data"] == 2


@pytest.mark.clouddb
class TestCloudDBUpdater:
    def setup_method(self, method):
        self.start_timestamp = bson.Timestamp(int(time.time()) - 1, 1)
        self.CloudDBUpdater = database.CloudDBUpdater()

    def test_init(self):
        assert "database.Database" in str(type(self.CloudDBUpdater.cloud_db))
        assert isinstance(self.CloudDBUpdater.oplog, pymongo.collection.Collection)
        assert self.CloudDBUpdater.oplog.name == "oplog.rs"
        assert isinstance(self.CloudDBUpdater.last_timestamp, bson.Timestamp)

    def test_create_bulk_operation_delete(self):
        entry = {
            "ts": 12345,
            "h": -1232132123123,
            "v": 2,
            "op": "d",
            "ns": "test.testing",
            "o": {"_id": "1234512345134556"},
        }
        expected = pymongo.DeleteOne({"_id": "1234512345134556"})
        assert self.CloudDBUpdater.create_bulk_operation(entry) == expected

    def test_create_bulk_operation_insert(self):
        entry = {
            "ts": 12345,
            "h": -1232132123123,
            "v": 2,
            "op": "i",
            "ns": "test.testing",
            "o": {"_id": "1234512345134556", "t": 42},
        }
        expected = pymongo.InsertOne({"_id": "1234512345134556", "t": 42})
        assert self.CloudDBUpdater.create_bulk_operation(entry) == expected

    def test_create_bulk_operation_update(self):
        entry = {
            "ts": 12345,
            "h": -1232132123123,
            "v": 2,
            "op": "u",
            "ns": "test.testing",
            "o": {"$set": {"test": 42}},
            "o2": {"_id": "1234512345134556"},
        }
        expected = pymongo.UpdateOne({"_id": "1234512345134556"}, {"$set": {"test": 42}})
        assert self.CloudDBUpdater.create_bulk_operation(entry) == expected

    def test_entries_since_last(self):
        self.CloudDBUpdater.db.insert_documents("test.testing", ({"a": 1}, {"a": 2}, {"a": 3}))
        self.CloudDBUpdater.db.delete_data("test.testing", {"a": 1})
        self.CloudDBUpdater.db.update_document("test.testing", {"b": 2}, {"a": 2})
        for entry in self.CloudDBUpdater.entries_since_last():
            assert entry["ts"] > self.start_timestamp
            assert entry["op"] in ["d", "i", "u"]

    def test_create_db_changes(self):
        current_db = self.CloudDBUpdater.db.db.name
        fake_oplog = [
            {"ns": f"{current_db}.test", "op": "u", "o": {"$set": {"v": 1}}, "o2": {"_id": "1234"}},
            {"ns": f"{current_db}test.test", "op": "d", "o": {"_id": "1234567"}},
            {"ns": f"{current_db}.test", "op": "d", "o": {"_id": "4321"}},
            {"ns": f"{current_db}.test2", "op": "i", "o": {"_id": "43210", "b": 1}},
        ]
        expected = collections_module.defaultdict()
        expected["test"] = [
            pymongo.UpdateOne({"_id": "1234"}, {"$set": {"v": 1}}),
            pymongo.DeleteOne({"_id": "4321"}),
        ]
        expected["test2"] = [pymongo.InsertOne({"_id": "43210", "b": 1})]
        with mock.patch.object(
            self.CloudDBUpdater, "entries_since_last", return_value=fake_oplog
        ) as _:
            changes = self.CloudDBUpdater.create_db_changes()
        assert changes == expected

    def test_get_connection_string(self):
        with mock.patch(
            "database.open",
            mock.mock_open(read_data="very_secure_password"),
        ) as mock_open:
            # Make sure that the file contents is inserted and that the correct file path
            # is used.
            result = database.CloudDBUpdater.get_connection_string()
            assert "very_secure_password" in result
            assert mock_open.call_args.args[0].endswith("data/api_keys/cloud_password.txt")

    @mock.patch("database.CloudDBUpdater.update_timestamp")
    def test_write_db_changes(self, mock1):
        changes = collections_module.defaultdict()
        changes["obj_team"] = [
            pymongo.InsertOne({"_id": "1234", "v": 2}),
            pymongo.InsertOne({"_id": "4321", "v": 1}),
            pymongo.UpdateOne({"_id": "1234"}, {"$set": {"v": 1, "c": 2}}),
        ]
        changes["subj_team"] = [pymongo.InsertOne({"_id": "43210", "b": 1})]
        with mock.patch.object(self.CloudDBUpdater, "create_db_changes", return_value=changes) as _:
            result = self.CloudDBUpdater.write_db_changes()
        assert result["obj_team"].inserted_count == 2
        assert result["obj_team"].modified_count == 1
        assert result["subj_team"].inserted_count == 1
        assert result["subj_team"].modified_count == 0
        assert self.CloudDBUpdater.cloud_db.find("obj_team") == [
            {"_id": "1234", "v": 1, "c": 2},
            {"_id": "4321", "v": 1},
        ]
        assert mock1.called

    def test_update_timestamp(self):
        self.CloudDBUpdater.db.insert_documents("test", {"a": 1})
        self.CloudDBUpdater.update_timestamp()
        op = self.CloudDBUpdater.oplog.find_one({"op": "i", "o.a": 1})
        assert self.CloudDBUpdater.last_timestamp >= op["ts"]
