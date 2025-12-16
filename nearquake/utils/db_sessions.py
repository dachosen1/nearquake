import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from nearquake.utils.logging_utils import (get_logger, log_db_operation,
                                           log_error, log_info)

_logger = get_logger(__name__)


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
        self.url = url

        try:
            self.engine = create_engine(url)
            self.Session = scoped_session(sessionmaker(bind=self.engine))
            log_info(_logger, "Successfully established connection to the database.")

        except Exception as e:
            log_error(_logger, "Failed to connect to the database", exc=e)

    def fetch_single(self, model, column, item):
        """
        Fetches records from a single item  from the database based on the model and filter conditions.

        :param model: SQLAlchemy ORM model class.
        :param column: The column name to apply the filter on.
        :param item: The value to filter by
        """
        try:
            table_name = getattr(model, "__tablename__", model.__name__)
            log_db_operation(
                _logger,
                operation="SELECT",
                table=table_name,
                details=f"Fetching single record where {column}={item}",
            )

            result = (
                self.session.query(model).filter(getattr(model, column) == item).all()
            )
            return result

        except Exception as e:
            log_error(
                _logger,
                f"Failed to execute fetch query on {getattr(model, '__tablename__', model.__name__)}",
                exc=e,
            )
            return None

    def fetch_many(self, model, column, items):
        """
        Fetches records from multiple items from the database based on the model and filter conditions.

        :param model: SQLAlchemy ORM model class.
        :param column: The column name to apply the filter on.
        :param item: The value to filter by
        """
        try:
            table_name = getattr(model, "__tablename__", model.__name__)
            log_db_operation(
                _logger,
                operation="SELECT",
                table=table_name,
                details=f"Fetching multiple records where {column} in list of {len(items)} items",
            )

            result = (
                self.session.query(model)
                .filter(getattr(model, column).in_(items))
                .all()
            )
            return result

        except Exception as e:
            log_error(
                _logger,
                f"Failed to execute fetch_many query on {getattr(model, '__tablename__', model.__name__)}",
                exc=e,
            )
            return None

    def insert(self, model):
        """
        Inserts a given model instance into the database.

        :param model: An instance of an SQLAlchemy ORM model to be inserted into the database.
        """
        try:
            table_name = getattr(model, "__tablename__", model.__class__.__name__)
            log_db_operation(
                _logger,
                operation="INSERT",
                table=table_name,
                details=f"Inserting single record",
            )

            self.session.add(model)
            self.session.commit()

        except Exception as e:
            log_error(
                _logger,
                f"Failed to execute insert query on {getattr(model, '__tablename__', model.__class__.__name__)}",
                exc=e,
            )

    def insert_many(self, models):
        """
        Inserts multiple instances of an SQLAlchemy ORM model into the database.

        :param models: A list of model instances to be inserted into the database.
        """
        if not models:
            return

        try:
            table_name = getattr(
                models[0], "__tablename__", models[0].__class__.__name__
            )
            log_db_operation(
                _logger,
                operation="INSERT",
                table=table_name,
                details=f"Inserting {len(models)} records",
            )

            for model in models:
                self.session.add(model)
            self.session.commit()

        except Exception as e:
            log_error(_logger, f"Failed to execute insert_many query", exc=e)
            self.session.rollback()

    def close(self):
        """Closes the database session."""
        try:
            if hasattr(self, "session") and self.session:
                self.session.close()
                log_info(_logger, "Database session closed")

        except Exception as e:
            log_error(
                _logger, "Error occurred while closing the database session", exc=e
            )

    def __enter__(self):
        self.session = self.Session()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exits the runtime context and closes the database session."""
        try:
            if hasattr(self, "session") and self.session:
                if exc_type is None:
                    # No exception, commit any pending transactions
                    self.session.commit()
                else:
                    # Exception occurred, rollback
                    self.session.rollback()
                    log_error(
                        _logger,
                        f"Rolling back transaction due to exception: {exc_value}",
                    )

                self.close()
        except Exception as e:
            log_error(_logger, "Error in context manager exit", exc=e)

        # Return False to propagate any exceptions
        return False
