from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Float,
    Integer,
    String,
    TIMESTAMP,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

import logging

_logger = logging.getLogger(__name__)

Base = declarative_base()


class EventDetails(Base):
    __tablename__ = "fct__event_details"
    __table_args__ = {"schema": "earthquake"}

    id_event = Column(String(50), primary_key=True, comment="Earthquake id Primary key")
    mag = Column(Float, comment="Magnitude of the earthquake")

    ts_updated_utc = Column(TIMESTAMP, comment="Timestamp of the last update")
    ts_event_utc = Column(TIMESTAMP, comment="Timestamp of the earthquake")
    tz = Column(Integer, comment="Time zone")
    felt = Column(
        Integer, comment="Number of people who reported feeling the earthquake"
    )
    longitude = Column(Float, comment="Longitude")
    latitude = Column(Float, comment="Latitude")
    detail = Column(String(500))
    cdi = Column(Float, comment="Community Internet Intensity Map")
    mmi = Column(Float, comment="Modified Mercalli Intensity")
    status = Column(String(50), comment="Status of the earthquake report")
    tsunami = Column(Boolean, comment="Indicates if a tsunami was generated")
    type = Column(String(50), comment="Type of seismic event")
    title = Column(String(200), comment="Title of the earthquake event")
    date = Column(Date, comment="Date of the earthquake")
    place = Column(String(200), comment="Place of the event")


class Post(Base):
    __tablename__ = "fct__post"
    __table_args__ = {"schema": "tweet"}

    id_post = Column(
        String(50),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="Post ID",
    )
    post = Column(String(2000), comment="Content of the tweet")
    ts_upload_utc = Column(TIMESTAMP, comment="Timestamp tweet was posted ")


def create_schema(engine, schema_names):
    connection = engine.connect()

    for schema_name in schema_names:
        create_schema_sql = text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        connection.execute(create_schema_sql)
        _logger.info(
            f"Successfuly created a new schema with the name: {schema_name} in the datase"
        )


def create_database(url: str, schema: Optional[List[str]] = None):
    """
    Creates a database engine and initializes the tables. Optiional parameter to create a scheme if it doesn't exist

    Example Usage:
        create_database(url, schema=["earthquake", "tweet"])

    :param url: The URL for the database, e.g., 'sqlite:///sqlalchemy_example.db'
    :param schema: a list containing the list of schemas to be created
    """
    engine = create_engine(url)

    try:
        Base.metadata.create_all(engine)

    except SQLAlchemyError as e:
        if "InvalidSchemaName" in str(e):
            if schema:
                create_schema(engine, schema)
                Base.metadata.create_all(engine)

            else:
                raise ValueError("Schema name not provided")
        else:
            return SQLAlchemyError

    return engine
