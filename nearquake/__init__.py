import json
import logging
import logging.handlers
import os
import sys

import colorlog
from logtail import LogtailHandler

from nearquake.config import TIMESTAMP_NOW
from nearquake.utils import create_dir

TIMESTAMP_NOW = TIMESTAMP_NOW.strftime("%Y%m%d")

logtail_handler = LogtailHandler(
    source_token=os.environ.get("LOGS_SOURCE_TOKEN"),
    host=os.environ.get("LOGS_SOURCE_HOST"),
)

# ANSI color codes
COLORS = {
    "RESET": "\033[0m",
    "BLACK": "\033[30m",
    "RED": "\033[31m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "BLUE": "\033[34m",
    "MAGENTA": "\033[35m",
    "CYAN": "\033[36m",
    "WHITE": "\033[37m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
}

# Color mapping for log levels
LEVEL_COLORS = {
    "DEBUG": COLORS["BLUE"],
    "INFO": COLORS["GREEN"],
    "WARNING": COLORS["YELLOW"],
    "ERROR": COLORS["RED"],
    "CRITICAL": COLORS["BOLD"] + COLORS["RED"],
}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "funcName": record.funcName,
            "fileName": record.filename,
            "message": record.getMessage(),
        }
        # Include exception info if available
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


# Colorful formatter for console output
class ColorfulFormatter(logging.Formatter):
    def format(self, record):
        level_color = LEVEL_COLORS.get(record.levelname, COLORS["RESET"])
        module_color = COLORS["CYAN"]
        message_color = COLORS["RESET"]

        # Format: timestamp - colored level - colored module - message
        return (
            f"{self.formatTime(record, self.datefmt)} — "
            f"{level_color}{record.levelname}{COLORS['RESET']} - "
            f"{module_color}{record.name}{COLORS['RESET']} — "
            f"{message_color}{record.getMessage()}{COLORS['RESET']}"
        )


# Filter for determining the output target
class FilterForHandler(logging.Filter):
    def __init__(self, handler_type):
        self.handler_type = handler_type

    def filter(self, record):
        if self.handler_type == "console":
            record._formatted_record = ColorfulFormatter().format(record)
        elif self.handler_type == "file":
            record._formatted_record = JsonFormatter().format(record)
        return True


# Custom formatter to use the filtered record
class CustomFormatter(logging.Formatter):
    def format(self, record):
        return record._formatted_record


# Logging Configuration
def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO if not DEBUG_MODE else logging.DEBUG)
    # Create directory path to save logs
    create_dir("logs")

    # Console Handler with Colorful Formatter
    console_handler = logging.StreamHandler(sys.stdout)

    # Create a colorlog formatter
    color_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s — %(levelname)s - %(name)s — %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
        style="%",
    )

    console_handler.setFormatter(color_formatter)
    logger.addHandler(console_handler)

    # File Handler with Log Rotation and JSON Formatter
    file_handler = logging.handlers.RotatingFileHandler(
        f"logs/{TIMESTAMP_NOW}-nearquake.log", maxBytes=1048576, backupCount=5
    )
    file_handler.setFormatter(JsonFormatter())
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(logtail_handler)


# Initialize logging
DEBUG_MODE = os.environ.get("DEBUG_MODE")
setup_logging()
