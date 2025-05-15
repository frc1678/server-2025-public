"""
This file is responsible for setting up and configuring the logging system for the program.
The logging system is used to log messages during the program's execution, including errors and important events.
The messages are logged to both the console and a log file.
"""

from rich.console import Console
import logging
from rich.logging import RichHandler
from rich.theme import Theme
import time
import os

custom_theme = Theme(
    {
        "logging.level.info": "bold blue",
        "logging.level.warning": "bold yellow",
        "logging.level.error": "bold red",
        "logging.level.critical": "bold red reverse",
    }
)
# Initialize the console for logging
console = Console(theme=custom_theme)

# Set the format for the log messages
FORMAT = "%(message)s"

# Create the logs directory if it doesn't exist
os.makedirs("data/logs", exist_ok=True)

# Configure the logging system
logging.basicConfig(
    level="INFO",
    format=FORMAT,
    handlers=[
        RichHandler(console=console, rich_tracebacks=True, show_time=False),
    ],
)
