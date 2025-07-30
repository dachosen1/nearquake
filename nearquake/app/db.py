import logging
from typing import List, Optional

from nearquake.app import DatabaseCreationError
from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import text

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
    location = relationship("LocationDetails", back_populates="event_detail")


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
    id_event = Column(
        String(50),
        ForeignKey("earthquake.fct__event_details.id_event"),
        unique=True,
        comment="Earthquake event id",
    )
    post_type = Column(String(50), nullable=True, comment="Type of post event, or fact")
    prompt = Column(String(50), nullable=True, comment="Generative AI Prompt")
    ts_upload_utc = Column(
        TIMESTAMP, nullable=True, comment="Timestamp tweet was posted "
    )


class LocationDetails(Base):
    __tablename__ = "dim__location_details"
    __table_args__ = {"schema": "earthquake"}

    id_event = Column(
        String(50),
        ForeignKey("earthquake.fct__event_details.id_event"),
        primary_key=True,
    )
    continent = Column(String(50), comment="The continent where the event occurred")
    continentCode = Column(String(10), comment="The code representing the continent")
    countryName = Column(
        String(100), comment="The name of the country where the event occurred"
    )
    countryCode = Column(String(10), comment="The ISO country code")
    principalSubdivision = Column(
        String(100),
        comment="The principal subdivision (e.g., state or province) where the event occurred",
    )
    principalSubdivisionCode = Column(
        String(10), comment="The code for the principal subdivision"
    )
    city = Column(String(100), comment="The city where the event occurred")
    event_detail = relationship("EventDetails", back_populates="location")


def create_schema(engine, schema_names):
    with engine.begin() as connection:
        for schema_name in schema_names:
            sql = text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            connection.execute(sql)
            _logger.info(f"Created a new schema: {schema_name}")


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
        if schema:
            create_schema(engine, schema)
        Base.metadata.create_all(engine)
        return engine
    except Exception as e:
        # Handle potential errors during database/schema creation
        raise DatabaseCreationError(f"Failed to create database: {str(e)}") from e
