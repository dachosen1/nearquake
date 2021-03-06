import os

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


def connect_db():
    conn = connect(host=NEARQUAKE_HOST, user=NEARQUAKE_USERNAME, password=NEARQUAKE_PASSWORD, dbname=NEARQUAKE_DATABASE)
    return conn
