#!/usr/bin/env python3

"""Sets up a machine for use or testing of the server.

To be run for every new clone of server.
"""

import os
import subprocess
import venv
import logging

import utils

log = logging.getLogger("setup_environment")

# Creates data folder
utils.create_file_path("data/")

# Creates path by joining the base directory and the target directory
TARGET_PATH = utils.create_file_path(".venv", False)

# Only run if file is directly called
if __name__ == "__main__":
    log_file = open(utils.create_file_path("data/setup_environment.log"), "w")
    # Create virtual environment
    log.info("Creating Virtual Environment...")
    # Clear any existing environments with clear=True
    # Install pip directly into installation
    # Set prompt to 'venv' instead of '.venv'
    venv.create(TARGET_PATH, clear=True, with_pip=True, prompt="venv")
    log.info("Virtual Environment Created")

    # Install pip packages
    # Set create_directories to false to avoid trying to create directory for pip
    if os.name == str("nt"):
        # Windows uses a Scripts directory instead of a bin directory
        PIP_PATH = utils.create_file_path(".venv/Scripts/pip", False)
    else:
        PIP_PATH = utils.create_file_path(".venv/bin/pip", False)
    REQUIREMENTS_PATH = utils.create_file_path("requirements.txt")
    log.info("Installing PyPI Packages...")
    # Runs /path/to/pip install -r /path/to/requirements.txt
    # Sets check to True to force check that pip exited without errors
    # Pipes pip output to /dev/null to avoid cluttering the terminal
    # All pip warnings/errors still print to terminal because stderr is not redirected
    install_wheel = subprocess.run(
        [PIP_PATH, "install", "wheel"],
        check=True,
        stdout=log_file,
        stderr=log_file,
    )
    install_reqs = subprocess.run(
        [PIP_PATH, "install", "-r", REQUIREMENTS_PATH],
        check=True,
        stdout=log_file,
        stderr=log_file,
    )
    log.info("Environment Setup Complete")
