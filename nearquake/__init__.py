import logging
import logging.handlers
import json
import sys

from nearquake.config import TIMESTAMP_NOW
from nearquake.utils import create_dir


TIMESTAMP_NOW = TIMESTAMP_NOW.strftime("%Y%m%d")


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "module": record.module,
            "level": record.levelname,
            "name": record.name,
            "funcName": record.funcName,
            "fileName": record.filename,
            "message": record.getMessage(),
        }
        return json.dumps(log_record)


# Standard Formatter for ConsoleHandler
standard_formatter = logging.Formatter(
    "%(asctime)s — %(levelname)s - %(name)s — %(message)s"
)


# Filter for determining the output target
class FilterForHandler(logging.Filter):
    def __init__(self, handler_type):
        self.handler_type = handler_type

    def filter(self, record):
        if self.handler_type == "console":
            record._formatted_record = standard_formatter.format(record)
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


    # Console Handler with Standard Formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.addFilter(FilterForHandler("console"))
    console_handler.setFormatter(CustomFormatter())
    logger.addHandler(console_handler)

    logger.propagate = False


# Initialize logging
DEBUG_MODE = True  # Set to False in production
setup_logging()
logger = logging.getLogger(__name__)


from nearquake import config, utils, app
