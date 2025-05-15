#!/usr/bin/env python3

"""Holds functions for database communication.

All communication with the MongoDB local database go through this file.
"""
import os
import collections as collections_module
from typing import Any, Optional, Union, List, Dict
import pymongo
import start_mongod
import utils
import logging
import re
import json
import pandas as pd
import shutil

log = logging.getLogger("database")

# Load collection names
COLLECTION_SCHEMA = utils.read_schema("schema/collection_schema.yml")
COLLECTION_NAMES = [collection for collection in COLLECTION_SCHEMA["collections"].keys()]
VALID_COLLECTIONS = [
    "auto_paths",
    "auto_pim",
    "obj_team",
    "obj_team_precision",
    "obj_tim",
    "obj_tim_precision",
    "subj_team",
    "subj_tim",
    "tba_team",
    "tba_tim",
    "raw_qr",
    "predicted_aim",
    "predicted_alliances",
    "predicted_team",
    "predicted_dbl_elim",
    "predicted_elims",
    "pickability",
    "raw_obj_pit",
    "ss_tim",
    "ss_team",
    "scout_precision",
    "sim_precision",
    "data_validation",
    "unconsolidated_totals",
    "unconsolidated_obj_tim",
    "unconsolidated_ss_team",
]

# Start mongod and initialize replica set
start_mongod.start_mongod()


def check_collection_name(collection_name: str) -> None:
    """Checks if a collection name exists, prints a warning if it doesn't"""
    if collection_name not in COLLECTION_NAMES:
        log.warning(f'Unexpected collection name: "{collection_name}"')


class Database:
    """Utility class for the database, performs CRUD functions on local and cloud databases"""

    def __init__(
        self,
        tba_event_key: str = utils.load_tba_event_key_file(utils._TBA_EVENT_KEY_FILE),
        connection: str = "localhost",
        port: int = start_mongod.PORT,
    ) -> None:
        self.connection = connection
        self.port = port
        self.client = pymongo.MongoClient(connection, port)
        production_mode: bool = os.environ.get("SCOUTING_SERVER_ENV") == "production"
        self.name = tba_event_key if production_mode else f"test{tba_event_key}"
        self.db = self.client[self.name]

    def setup_db(self):
        self.set_indexes()
        # All document names and their files
        coll_to_path = self._get_all_schema_names()
        for entry in coll_to_path.keys():
            self._enable_validation(entry, coll_to_path[entry])

    def set_indexes(self) -> None:
        """Adds indexes into competition collections"""
        for collection in COLLECTION_SCHEMA["collections"]:
            collection_dict = COLLECTION_SCHEMA["collections"][collection]
            if collection_dict["indexes"] is not None:
                for index in collection_dict["indexes"]:
                    self.db[collection].create_index(
                        [(field, pymongo.ASCENDING) for field in index["fields"]],
                        unique=index["unique"],
                    )

    def find(self, collection: str, query: dict = {}) -> list:
        """Finds documents in 'collection', filtering by 'filters'"""
        check_collection_name(collection)
        return list(self.db[collection].find(query))

    def get_tba_cache(self, api_url: str) -> Optional[dict]:
        """Gets the TBA Cache of 'api_url'"""
        return self.db.tba_cache.find_one({"api_url": api_url})

    def update_tba_cache(self, data: Any, api_url: str, etag: Optional[str] = None) -> None:
        """Updates one TBA Cache at 'api_url'"""
        write_object = {"data": data}
        if etag is not None:
            write_object["etag"] = etag
        self.db.tba_cache.update_one({"api_url": api_url}, {"$set": write_object}, upsert=True)

    def delete_data(self, collection: str, query: dict = None, bypass: bool = False) -> None:
        """Deletes data in 'collection' according to 'filters'"""
        check_collection_name(collection)
        if "raw" in collection:
            if not bypass:
                log.warning(
                    f"A file attempted to delete raw data from {collection=}, was blocked because {bypass=}."
                )
                return
            else:
                log.warning(f"Deleted raw data from {collection}")
        if query is None:
            self.db[collection].delete_many({})
        else:
            self.db[collection].delete_many(query)

    def insert_documents(self, collection: str, data: Union[list, dict]) -> None:
        """Inserts documents from 'data' list in 'collection'"""
        check_collection_name(collection)

        try:
            if isinstance(data, list) and data:
                self.db[collection].insert_many(data)
            elif data and isinstance(data, dict):
                self.db[collection].insert_one(data)
            else:
                log.warning(
                    f'Data for insertion to "{collection}" is not a list or dictionary, or is empty'
                )
        except Exception as err:
            log.critical(f"Unable to insert some documents into collection {collection}: {err}")

    def update_document(
        self, collection: str, new_data: dict, query: dict, many: bool = False, upsert: bool = False
    ) -> None:
        """Updates one document that matches 'query' with 'new_data', uses upsert"""
        check_collection_name(collection)
        if collection == "raw_qr":
            log.warning(f"Attempted to modify raw qr data")
            return
        if not many:
            return self.db[collection].update_one(query, {"$set": new_data}, upsert)
        else:
            return self.db[collection].update_many(query, {"$set": new_data}, upsert)

    def update_many(
        self,
        collection: str,
        new_data: dict,
        query: dict,
    ) -> None:
        """Updates many documents that match 'query' with 'new_data', uses upsert"""
        check_collection_name(collection)
        if collection == "raw_qr":
            log.warning(f"Attempted to modify raw qr data")
            return
        self.db[collection].update_many(query, {"$set": new_data}, upsert=True)

    def update_qr_blocklist_status(self, query, blocklist=True) -> None:
        """Changes the status of a raw qr matching 'query' from blocklisted: true to blocklisted: false
        Lowers risk of data loss from using normal update."""
        self.db["raw_qr"].update_one(query, {"$set": {"blocklisted": blocklist}})

    def update_qr_data_override(self, query, datapoint, new_value, clear=False) -> None:
        """Changes the override of a datapoint of a raw qr matching 'query' to new_value
        Lowers risk of data loss from using normal update."""
        if clear:
            self.db["raw_qr"].update_one(query, {"$set": {f"override": {}}})
        else:
            self.db["raw_qr"].update_one(query, {"$set": {f"override.{datapoint}": new_value}})

    def _enable_validation(self, collection: str, file: str):
        sch = utils.read_schema("schema/" + file)
        sch = mongo_convert(sch, collection)
        cmd = collections_module.OrderedDict(
            [
                ("collMod", collection),
                ("validator", {"$jsonSchema": sch}),
                ("validationLevel", "moderate"),
            ]
        )
        self.db.command(cmd)

    def _get_all_schema_names(self) -> dict:
        out = {}
        for entry in COLLECTION_SCHEMA["collections"].keys():
            out[entry] = COLLECTION_SCHEMA["collections"][entry]["schema"]
            if out[entry] == None:
                out.pop(entry)
            elif utils.read_schema("schema/" + out[entry]) is None:
                out.pop(entry)
        return out

    def bulk_write(self, collection: str, actions: list) -> pymongo.results.BulkWriteResult:
        """Bulk write `actions` into `collection` in order of `actions`"""
        check_collection_name(collection)
        if collection in VALID_COLLECTIONS:
            return self.db[collection].bulk_write(actions)
        else:
            log.warning(f'py: Invalid collection name: "{collection}"')


class CloudDBUpdater:

    BASE_CONNECTION_STRING = "mongodb+srv://server:{}@scouting-system-3das1.gcp.mongodb.net/test?authSource=admin&replicaSet=scouting-system-shard-0&w=majority&readPreference=primary&appname=MongoDB%20Compass&retryWrites=true&ssl=true"
    OPERATION_MAP = {"i": pymongo.InsertOne, "u": pymongo.UpdateOne, "d": pymongo.DeleteOne}

    def __init__(self):
        self.cloud_db = self.get_cloud_db()
        self.db = Database()
        self.db_pattern = re.compile(r"^{}\..*".format(self.db.name))
        self.oplog = self.db.client.local.oplog.rs
        # Get an initial timestamp
        self.update_timestamp()

    def entries_since_last(self) -> List[dict]:
        """Returns the oplog entries since the last update

        These updates are filtered to only include Update, Insert, and Delete operations
        """
        return list(
            self.oplog.find({"ts": {"$gt": self.last_timestamp}, "op": {"$in": ["d", "i", "u"]}})
        )

    def create_db_changes(self) -> collections_module.defaultdict:
        """Creates bulk write operations from oplog"""
        changes = collections_module.defaultdict(list)
        for entry in self.entries_since_last():
            # 'ns' in the entry is of the format <database>.<collection> and shows where the changes
            # were written
            location: str = entry["ns"]
            # Ignore writes to a database other than the current local database
            if not self.db_pattern.match(location):
                continue
            # Get collection name from full location
            collection = location[location.index(".") + 1 :]
            if (bulk_op := self.create_bulk_operation(entry)) is None:
                continue
            else:
                changes[collection].append(bulk_op)
        return changes

    def write_db_changes(self) -> Dict[str, pymongo.results.BulkWriteResult]:
        """Writes oplog changes to cloud database"""
        # Try connecting to cloud db if connection does not exist
        if self.cloud_db is None:
            self.cloud_db = self.get_cloud_db()
            # Don't try to continue if above connection failed
            if self.cloud_db is None:
                return {}
        results = {}
        for collection, bulk_ops in self.create_db_changes().items():
            try:
                results[collection] = self.cloud_db.bulk_write(collection, bulk_ops)
            except pymongo.errors.BulkWriteError as bulk_errmsg:
                bulk_errmsg = str(bulk_errmsg)
                if "E11000 duplicate key error" in bulk_errmsg:
                    log.info(
                        f"Skipped upload of {len(bulk_ops)} duplicate documents in {collection}"
                    )
                else:
                    log.error(f"{collection}: {bulk_errmsg}")
                    current_documents = self.db.find(collection)
                    self.cloud_db.delete_data(collection)
                    self.cloud_db.insert_documents(collection, current_documents)
            except pymongo.errors.ServerSelectionTimeoutError:
                log.critical(
                    f"unable to write {len(bulk_ops)} documents to {collection} due to poor internet (ServerSelectionTimeoutError). Make sure you're not connected to DJUSD Wi-Fi (use a hotspot or different Wi-Fi)"
                )
                break  # Don't delay server cycle with more operations without internet
            # Catches validation errors
            except pymongo.errors.CollectionInvalid:
                log.error(f"{len(bulk_ops)} documents failed validation in {collection}")
            # Catches errors when updating to the cloud DB on non-server computers
            except TypeError as type_e:
                log.critical(f"error writing {len(bulk_ops)} documents to {collection}: {type_e}")
        # Update timestamp if loop exited properly
        else:
            self.update_timestamp()
        return results

    def update_timestamp(self):
        """Updates the timestamp to the most recent oplog entry timestamp"""
        last_op = self.oplog.find({}).sort("ts", pymongo.DESCENDING).limit(1)
        self.last_timestamp = last_op.next()["ts"]

    def create_bulk_operation(
        self, entry: Dict[str, Any]
    ) -> Optional[Union[pymongo.DeleteOne, pymongo.InsertOne, pymongo.UpdateOne]]:
        """Creates a pymongo bulk write operation for the entry.

        Note: this does not handle the collection that is written to, and the operations need to be
        applied to a specific collection to work.
        """
        operation = self.OPERATION_MAP.get(entry["op"])

        if operation is None:
            return None
        if "o" in entry and "$v" in entry["o"]:
            entry["o"].pop("$v")

        if entry["op"] == "u" and "$set" not in entry["o"]:
            return None

        if "o2" in entry:
            try:
                return operation(entry["o2"], entry["o"])
            # Tries to InsertOne with an o2
            except:
                return operation(entry["o"])

        return operation(entry["o"])

    @classmethod
    def get_cloud_db(cls) -> Optional[Database]:
        """Connects to the cloud database and returns a database object.

        This function mainly exists to facilitate testing by mocking the function return
        """
        try:
            return Database(connection=cls.get_connection_string())
        except pymongo.errors.ConfigurationError:
            # Raised when DNS operation times out, effectively means no internet
            log.error("cannot connect to Cloud DB")
            return None

    @classmethod
    def get_connection_string(cls) -> str:
        """Adds the password to the class connection string"""
        try:
            with open(utils.create_file_path("data/api_keys/cloud_password.txt")) as f:
                password = f.read().rstrip()
        except FileNotFoundError:
            raise FileNotFoundError(
                "Missing Cloud DB password file (data/api_keys/cloud_password.txt)"
            )
        return cls.BASE_CONNECTION_STRING.format(password)


class BetterDatabase:
    "A streamlined, user-friendly utility class to communicate with both the cloud and local databases"
    EMPTY_CLOUD_CONN_STR = "mongodb+srv://server:{}@scouting-system-3das1.gcp.mongodb.net/test?authSource=admin&replicaSet=scouting-system-shard-0&w=majority&readPreference=primary&appname=MongoDB%20Compass&retryWrites=true&ssl=true"

    def __init__(self, db_name: str, cloud: bool, port: int = 1678):
        "Initializes an instance of one database inside either the cloud or local connection."
        self.db_name = db_name
        self.cloud = cloud

        if cloud:
            with open("data/api_keys/cloud_password.txt") as f:
                self.connection = "mongodb+srv://server:{}@scouting-system-3das1.gcp.mongodb.net/test?authSource=admin&replicaSet=scouting-system-shard-0&w=majority&readPreference=primary&appname=MongoDB%20Compass&retryWrites=true&ssl=true".format(
                    f.read().rstrip()
                )
        else:
            self.connection = "localhost"

        self.client = pymongo.MongoClient(self.connection, port)
        self.db = self.client[self.db_name]

    def check_collection(self, collection: str) -> bool:
        "Checks if a given collection exists within the database"
        if collection not in self.get_collections():
            log.warning(f"Collection {collection} does not exist.")
            return False
        return True

    def get_collections(self) -> List[str]:
        "Returns a list of all existing collections within the"
        return list(map(lambda col: col["name"], self.db.list_collections()))

    def get_documents(
        self, collection: str, query: dict = dict(), include_obj_id: bool = False
    ) -> List[dict]:
        "Returns documents from a given collection filtered by `query`. If `query` is empty, returns all documents within the collection."
        if not self.check_collection(collection):
            log.warning(f"Attempted to get documents from nonexistent collection '{collection}'")
            return []
        documents = list(self.db[collection].find(query))

        if include_obj_id:
            return documents
        else:
            filtered = []
            for document in documents:
                document.pop("_id")
                filtered.append(document)
            return filtered

    def update_document(
        self,
        collection: str,
        updates: dict,
        query: dict,
        bypass_raw: bool = False,
        update_many: bool = False,
    ) -> pymongo.results.UpdateResult:
        "Updates documents matching `query` in a given collection with new datapoints in `updates`."
        if not self.check_collection(collection):
            log.warning(f"Invalid {collection=}")
            return None

        if "raw" in collection:
            if not bypass_raw:
                log.warning(
                    f"Careful! Attempted to modify raw data from {collection=}. This was blocked because the bypass option was set to {bypass_raw}."
                )
                return
            else:
                log.warning(f"Modified raw data from {collection=}")

        if not update_many:
            return self.db[collection].update_one(query, {"$set": updates})
        else:
            return self.db[collection].update_many(query, {"$set": updates})

    def insert_documents(
        self, collection: str, data: Union[List[dict], dict]
    ) -> pymongo.results.InsertManyResult:
        "Inserts new documents into the given collection."
        if not self.check_collection(collection):
            return []

        if type(data) == list:
            return self.db[collection].insert_many(data)
        elif type(data) == dict:
            return self.db[collection].insert_one(data)
        else:
            log.warning(f"Attempted to insert invalid data type ({type(data)}) into {collection=}")

    def delete_documents(
        self, collection: str, query: dict, bypass_raw: bool = False
    ) -> pymongo.results.DeleteResult:
        "Deletes documents matching `query` within a collection."
        if not self.check_collection(collection):
            return []
        if "raw" in collection:
            if not bypass_raw:
                log.warning(
                    f"Careful! Attempted to delete raw data from {collection=}. This was blocked because the bypass option was set to {bypass_raw}."
                )
                return
            else:
                log.warning(f"Deleted raw data from {collection=}")

        if not query:
            return self.db[collection].delete_many({})
        else:
            return self.db[collection].delete_many(query)

    def export_collection(self, collection: str, out_file: str) -> None:
        "Exports one collection to `<out_file>` as a JSON or CSV."
        filtered_documents = []
        file_type = out_file.split(".")[-1]

        for document in self.get_documents(collection):
            filtered_document = dict()
            for key, val in document.items():
                if type(key) in [str, int, float, list, dict] and type(val) in [
                    str,
                    int,
                    float,
                    list,
                    dict,
                ]:
                    filtered_document[key] = val
            filtered_documents.append(filtered_document)

        if file_type == "json":
            with open(out_file, "w") as f:
                f.write(json.dumps(filtered_documents, indent=4))
        elif file_type == "csv":
            pd.DataFrame(filtered_documents).to_csv(out_file, index=False)
        else:
            log.error("Invalid out file type")
            return

        log.info(f"Exported {self.db_name}.{collection} to {out_file}")

    def export_database(self, out_folder: str, file_type: str = "json", zip: bool = True) -> None:
        "Exports the entire database (all collections) to `data/<out_folder>` as JSONs or CSVs."
        log.info(f"Exporting {self.db_name} database to data/{out_folder}/...")

        if os.path.isdir(f"data/{out_folder}"):
            shutil.rmtree(f"data/{out_folder}")
        os.mkdir(f"data/{out_folder}")

        for collection in self.get_collections():
            if collection == "pit_images":
                continue

            log.info(f"Exporting {collection}...")

            filtered_documents = []
            for document in self.get_documents(collection):
                filtered_document = dict()
                for key, val in document.items():
                    if type(key) in [str, int, float, list, dict] and type(val) in [
                        str,
                        int,
                        float,
                        list,
                        dict,
                    ]:
                        filtered_document[key] = val
                filtered_documents.append(filtered_document)

            if file_type == "json":
                with open(f"data/{out_folder}/{collection}.json", "w") as f:
                    f.write(json.dumps(filtered_documents, indent=4))
            elif file_type == "csv":
                pd.DataFrame(filtered_documents).to_csv(
                    f"data/{out_folder}/{collection}.csv", index=False
                )
            else:
                log.error("Invalid out file type")
                return

        if zip:
            log.info("Zipping data...")
            shutil.make_archive(out_folder, "zip", f"data/{out_folder}")
            shutil.move(f"{out_folder}.zip", f"data/{out_folder}/{out_folder}.zip")

        log.info(f"Finished export of {self.db_name} database to {out_folder}/")

    def delete_duplicates(self, collection: str) -> int:
        "Deletes duplicate-index documents from a specified collection. Indexes by the `indexes` field in `collection_schema.yml`. If no index exists, considers every field as an index."
        data = self.get_documents(collection)
        if not data:
            return 0

        indexes = COLLECTION_SCHEMA["collections"][collection]["indexes"]
        if indexes:
            indexes = indexes[0]["fields"]

        used_indexes = []
        filtered_data = []
        duplicate_count = 0

        for document in data:
            if indexes:
                if collection == "raw_qr":
                    index = utils.get_qr_identifiers(document["data"])
                else:
                    index = [document[variable] for variable in indexes]

                if index not in used_indexes:
                    used_indexes.append(index)
                    filtered_data.append(document)
                    continue
            else:
                if document not in filtered_data:
                    filtered_data.append(document)
                    continue

        if duplicate_count > 0:
            self.delete_documents(collection, dict(), True)
            self.insert_documents(collection, filtered_data)

        log.info(f"Deleted {duplicate_count} duplicate documents from collection '{collection}'.")
        return duplicate_count


def cloud_db_connector():
    """Connects to the cloud database and returns a database object."""
    for attempt in range(3):
        # Tries to connect 3 times before raising an error
        cloud_db = CloudDBUpdater.get_cloud_db()
        if cloud_db is not None:
            return cloud_db
    raise IOError("Three connection attempts failed to the CloudDB")


def mongo_convert(sch, collection):
    """Converts a schema dictionary into a mongo-usable form."""
    # dictionary for translating data types in schema to recognized BSON types
    type_to_bson = {
        "int": "int",
        "float": "number",
        "str": "string",
        "bool": "bool",
        "list": "array",
    }
    out = {}
    out["bsonType"] = "object"
    out["required"] = COLLECTION_SCHEMA["collections"][collection]["indexes"][0]["fields"]
    out["properties"] = {}
    for section, datapoints in sch.items():
        # These sections aren't stored in the database; ignore them
        if section in ["schema_file", "enums"] or section[:2] == "--":
            continue
        for datapoint, info in datapoints.items():
            datapoint_dict = {}
            # Enums include their data type in brackets. Ex: Enum[int] is int.
            datapoint_dict["bsonType"] = [
                type_to_bson[t[5:-1] if "Enum" in (t := info["type"]) else t],
                "null",
            ]
            out["properties"].update({datapoint: datapoint_dict})
    return out
