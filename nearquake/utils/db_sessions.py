import logging
from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

_logger = logging.getLogger(__name__)


class DbSessionManager:
    """
    Establishes a connection to the database using the provided configuration.

    Example usage:

    conn = DbSessionManager(config=ConnectionConfig())

    with conn :
        item = {"id_event": 'c-jjerh', "longitude": 982.28, "latitude": 129.827}
        row = DimPlace(**item)
        conn.insert(row)

    """

    def __init__(self, config) -> None:
        self.config = config

    def create_engine(self):
        return create_engine(url=self.config.generate_connection_url())

    def connect(self):
        """Establishes a connection to the database using the provided configuration.

        :param config: A configuration object containing the necessary database connection details.
        """

        try:
            self.engine = self.create_engine()
            _logger.info(" Connected to the Database")
            Session = sessionmaker(bind=self.engine)
            self.session = Session()

        except Exception as e:
            _logger.error(f"Failed to connect to the database: {e}")

    def fetch(self, model, column, item):
        """


        :param model: _description_
        :param column: _description_
        :param item: _description_
        :return: _description_
        """
        return self.session.query(model).filter(getattr(model, column) == item).all()

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

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exits the runtime context and closes the database session.

        """
        self.close()
