import logging
import os
import sys

from psycopg2 import connect

import models

PACKAGE_ROOT = os.path.dirname(models.__file__)

#  -------------------------------------------------------------------------------- Twitter API
CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')

# --------------------------------------------------------------------------------- Postgres
NEARQUAKE_HOST = os.getenv('NEARQUAKE_HOST')
NEARQUAKE_USERNAME = os.getenv('NEARQUAKE_USERNAME')
NEARQUAKE_PASSWORD = os.getenv('NEARQUAKE_PASSWORD')
NEARQUAKE_DATABASE = os.getenv('NEARQUAKE_DATABASE')

# --------------------------------------------------------------------------------- Logging

FORMATTER = logging.Formatter(
)

FORMATTER = logging.Formatter(
    "%(asctime)s — %(name)s — %(levelname)s —" "%(funcName)s:%(lineno)d — %(message)s"
)


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def connect_db():
    conn = connect(host=NEARQUAKE_HOST, user=NEARQUAKE_USERNAME, password=NEARQUAKE_PASSWORD, dbname=NEARQUAKE_DATABASE,port=5432)
    return conn


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(get_console_handler())

logger.propagate = False
