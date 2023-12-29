import logging
import logging.handlers
import json
import sys


# JSON Formatter
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            # Add more fields if necessary
        }
        return json.dumps(log_record)


# Logging Configuration
def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO if not DEBUG_MODE else logging.DEBUG)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s — %(levelname)s — %(message)s")
    )
    logger.addHandler(console_handler)

    # File Handler with Log Rotation
    file_handler = logging.handlers.RotatingFileHandler(
        "nearquake.log", maxBytes=1048576, backupCount=5
    )
    file_handler.setFormatter(JsonFormatter())
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    logger.propagate = False


# Initialize logging
DEBUG_MODE = True  # Set to False in production

setup_logging()
logger = logging.getLogger(__name__)
