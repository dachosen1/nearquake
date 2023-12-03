from psycopg2 import connect, sql
import logging
from sqlalchemy import create_engine

from nearquake.config import ConnectionConfig
from sqlalchemy.orm import sessionmaker
from nearquake.app.db import DimPlace

_logger = logging.getLogger(__name__)


class DbOperator:
    """
    Establishes a connection to the database using the provided configuration.

    Example usage:

    with DbOperator() as db:
        config = Config()
        db.connect()
        item = {"id": 123, "location": "St. Louis"}
        row = Model(**item)
        item = db.insert(row)
    """

    def connect(self, config):
        """Establishes a connection to the database using the provided configuration.

        :param config: A configuration object containing the necessary database connection details.
        """
        self.config = config
        try:
            self.engine = create_engine(url=self.config.generate_connection_url())
            _logger.info(" Connected to the Database")
            Session = sessionmaker(bind=self.engine)
            self.session = Session()

        except Exception as e:
            _logger.error(f"Failed to connect to the database: {e}")

    def fetch(self):
        # TODO:
        pass

    def insert(self, model):
        """
        Inserts a given model instance into the database.

        :param model: An instance of an SQLAlchemy ORM model to be inserted into the database.
        """
        try:
            self.session.add(model)
            self.session.commit()

        except Exception as e:
            print("Failed to execute insert query: ", e)

    def close(self):
        """
        An instance of an SQLAlchemy ORM model to be inserted into the database.
        """
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exits the runtime context and closes the database session.

        """
        self.close()
