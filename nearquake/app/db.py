from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Float,
    Integer,
    String,
    TIMESTAMP,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import text

Base = declarative_base()


class EventDetails(Base):
    __tablename__ = "fct__event_details"
    __table_args__ = {"schema": "earthquake"}

    id_event = Column(String(50), primary_key=True, comment="Earthquake id Primary key")
    mag = Column(Float, comment="Magnitude of the earthquake")
    id_place = Column(
        Integer, ForeignKey("earthquake.dim__place.id_place"), comment="Place id"
    )
    id_time = Column(
        Integer, ForeignKey("earthquake.dim__time.id_time"), comment="Time id"
    )
    ts_updated_utc = Column(TIMESTAMP, comment="Timestamp of the last update")
    tz = Column(Integer, comment="Time zone")
    felt = Column(
        Integer, comment="Number of people who reported feeling the earthquake"
    )
    detail = Column(String(500))
    cdi = Column(Float, comment="Community Internet Intensity Map")
    mmi = Column(Float, comment="Modified Mercalli Intensity")
    longitude = Column(Float, comment="Longitude")
    latitude = Column(Float, comment="Latitude")
    depth = Column(Float, comment="Depth")
    id_alert = Column(
        Integer, ForeignKey("earthquake.dim__alert.id_alert"), comment="Alert id"
    )
    status = Column(String(50), comment="Status of the earthquake report")
    tsunami = Column(Boolean, comment="Indicates if a tsunami was generated")
    type = Column(String(50), comment="Type of seismic event")
    title = Column(String(200), comment="Title of the earthquake event")
    date = Column(Date, comment="Date of the earthquake")
    place = relationship("DimPlace", back_populates="event_details")
    time = relationship("DimTime", back_populates="event_details")
    alert = relationship("DimAlert", back_populates="event_details")


class DimPlace(Base):
    __tablename__ = "dim__place"
    __table_args__ = {"schema": "earthquake"}

    id_place = Column(Integer, primary_key=True, comment="Primary key")
    place = Column(String(200), comment="Location of the earthquake")
    event_details = relationship("EventDetails", back_populates="place")


class DimAlert(Base):
    __tablename__ = "dim__alert"
    __table_args__ = {"schema": "earthquake"}

    id_alert = Column(Integer, primary_key=True, comment="Alert Id Primary Key")
    alert = Column(String(200), comment="Alert level of the earthquake")
    event_details = relationship("EventDetails", back_populates="alert")


class DimTime(Base):
    __tablename__ = "dim__time"
    __table_args__ = {"schema": "earthquake"}
    id_time = Column(Integer, primary_key=True, comment="Time ID")
    ts_event_utc = Column(TIMESTAMP, comment="Timestamp of the earthquake")
    event_details = relationship("EventDetails", back_populates="time")


class Post(Base):
    __tablename__ = "fct__post"
    __table_args__ = {"schema": "tweet"}

    id_post = Column(String(50), primary_key=True, comment="Post ID")
    post = Column(String(2000), comment="Content of the tweet")
    ts_upload_utc = Column(TIMESTAMP, comment="Timestamp tweet was posted ")


def create_schemas(engine, schema_names):
    connection = engine.connect()

    for schema_name in schema_names:
        create_schema_sql = text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        connection.execute(create_schema_sql)
