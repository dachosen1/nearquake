import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_logger = logging.getLogger(__name__)


class DbSessionManager:
    """
    Establishes a connection to the database using the provided configuration.

    Example usage:

    conn = DbSessionManager(url=url))

    with conn :
        item = {"id_event": 'c-jjerh', "longitude": 982.28, "latitude": 129.827}
        row = DimPlace(**item)
        conn.insert(row)
    """

    def __init__(self, url) -> None:
        self.config = url

    def create_engine(self):
        return create_engine(url=self.url)

    def connect(self):
        """Establishes a connection to the database using the provided configuration."""
        try:
            self.engine = self.create_engine()
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            _logger.info("Successfully established connection to the database.")

        except Exception as e:
            _logger.error("Failed to connect to the database: %s", e, exc_info=True)

    def fetch_single(self, model, column, item):
        """
        Fetches records from a single item  from the database based on the model and filter conditions.

        :param model: SQLAlchemy ORM model class.
        :param column: The column name to apply the filter on.
        :param item: The value to filter by
        """
        try:
            result = (
                self.session.query(model).filter(getattr(model, column) == item).all()
            )
            return result

        except Exception as e:
            _logger.error("Failed to execute fetch query: %s", e, exc_info=True)
            return None

    def fetch_many(self, model, column, items):
        """
        Fetches records from multiple items from the database based on the model and filter conditions.

        :param model: SQLAlchemy ORM model class.
        :param column: The column name to apply the filter on.
        :param item: The value to filter by
        """
        try:
            result = (
                self.session.query(model)
                .filter(getattr(model, column).in_(items))
                .all()
            )
            return result

        except Exception as e:
            _logger.error("Failed to execute fetch query: %s", e, exc_info=True)
            return None

    def insert(self, model):
        """
        Inserts a given model instance into the database.

        :param model: An instance of an SQLAlchemy ORM model to be inserted into the database.
        """
        try:
            self.session.add(model)
            self.session.commit()

        except Exception as e:
            _logger.error("Failed to execute insert query: %s", e, exc_info=True)

    def insert_many(self, models):
        """
        Inserts multiple instances of an SQLAlchemy ORM model into the database.

        :param models: A list of model instances to be inserted into the database.
        """
        try:
            for model in models:
                self.session.add(model)
            self.session.commit()

        except Exception as e:
            _logger.error("Failed to execute insert_many query: %s", e, exc_info=True)
            self.session.rollback()

    def close(self):
        """Closes the database session."""
        try:
            self.session.close()
            _logger.info("Database session closed !!!")

        except Exception as e:
            _logger.error(
                "Error occurred while closing the database session: %s",
                e,
                exc_info=True,
            )

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exits the runtime context and closes the database session."""
        self.close()
