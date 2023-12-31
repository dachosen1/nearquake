import logging
import logging.handlers
import json
import sys


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "module": record.module,
            "level": record.levelname,
            "name": record.name,
            "process": record.process,
            "processName": record.processName,
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

    # File Handler with Log Rotation and JSON Formatter
    file_handler = logging.handlers.RotatingFileHandler(
        "nearquake.log", maxBytes=1048576, backupCount=5
    )
    file_handler.addFilter(FilterForHandler("file"))
    file_handler.setFormatter(CustomFormatter())
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    logger.propagate = False


# Initialize logging
DEBUG_MODE = True  # Set to False in production
setup_logging()
logger = logging.getLogger(__name__)
