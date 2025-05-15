#!/usr/bin/env python3

"""Starts the mongod instance used by database.py, including handling the replica set"""
import subprocess
import sys


import utils
import logging

log = logging.getLogger("start_mongod")

# Replica Set constants
PORT = 1678
DB_PATH = utils.create_file_path("data/db")
REPLICA_SET_NAME = "ScoutingReplica0"
MONGOD_LOG_PATH = utils.create_file_path("data/mongodlogs/mongod.log")


def start_mongod():
    """Start mongod and initialize replica set if not already running

    If cloud db update starts missing things when large amounts of data is added, might need to
    raise the oplog size"""
    start_mongod_result = subprocess.run(
        [
            "mongod",
            "--replSet",
            REPLICA_SET_NAME,
            "--port",
            str(PORT),
            "--bind_ip",
            "localhost",
            "--dbpath",
            DB_PATH,
            "--logpath",
            MONGOD_LOG_PATH,
            "--fork",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if start_mongod_result.returncode == 48:
        log.info("Custom mongod process already started.")
        return
    elif start_mongod_result.returncode > 0:
        log.error("Error starting mongod. Check data/mongod.log for more details")

    init_repl_set_result = subprocess.run(
        ["mongosh", "--eval", "rs.initiate()", "--port", str(PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output = init_repl_set_result.stdout.decode("utf-8")
    if init_repl_set_result.returncode != 0:
        log.error(f"Error initiating Replica Set.\n{output}")
        return

    if '"codeName" : "AlreadyInitialized"' in output:
        log.info("Replica Set already started")
    elif '"codeName" : "NoReplicationEnabled"' in output:
        log.error(f"Replication not enabled on mongod running on localhost:{PORT}")
    elif '"ok" : 0' in output:
        log.warning(f"Unknown problem initializing replica set\n{output}")
    else:
        log.info("Replica set started successfully")


if __name__ == "__main__":
    start_mongod()
