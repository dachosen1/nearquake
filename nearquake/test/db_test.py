import pytest
from sqlalchemy import create_engine, MetaData
import sqlalchemy.orm
from nearquake.app.db import EventDetails, Base, DimAlert, DimPlace, DimTime, Post

DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def engine():
    return create_engine(DATABASE_URL)


@pytest.fixture(scope="module")
def connection(engine):
    return engine.connect()


@pytest.fixture(scope="module")
def metadata():
    return MetaData()


@pytest.fixture(scope="module")
def session(connection, metadata):
    Session = sqlalchemy.orm.sessionmaker(bind=connection)
    session = Session()
    metadata.create_all(bind=connection, tables=[EventDetails.__table__])
    yield session
    session.close()
    

def test_earquake_schema_tables():
    assert EventDetails.__tablename__ == "fct__event_details"
    assert DimAlert.__tablename__ == "dim__alert"
    assert DimPlace.__tablename__ == "dim__place"
    assert DimTime.__tablename__ == "dim__time"


def test_twiiter_schema_tables():
    assert Post.__tablename__ == "fct__post"


def test_schema():
    assert EventDetails.__table_args__["schema"] == "earthquake"
    assert DimAlert.__table_args__["schema"] == "earthquake"
    assert DimPlace.__table_args__["schema"] == "earthquake"
    assert DimTime.__table_args__["schema"] == "earthquake"


def test_event_details_columns():
    columns = EventDetails.__table__.columns
    assert "id_event" in columns
    assert columns["id_event"].primary_key is True


def test_dim_alerts_columns():
    columns = DimAlert.__table__.columns
    assert "id_alert" in columns
    assert columns["id_alert"].primary_key is True


def test_dim_time_columns():
    columns = DimTime.__table__.columns
    assert "id_time" in columns
    assert columns["id_time"].primary_key is True


def test_dim_place_columns():
    columns = DimPlace.__table__.columns
    assert "id_place" in columns
    assert columns["id_place"].primary_key is True


def test_relationships():
    assert hasattr(EventDetails, "place")
    assert hasattr(EventDetails, "time")
    assert hasattr(EventDetails, "alert")

    # Test relationships
    assert "event_details" in EventDetails.place.property.back_populates
    assert "event_details" in EventDetails.time.property.back_populates
    assert "event_details" in EventDetails.alert.property.back_populates
