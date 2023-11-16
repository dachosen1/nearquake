import pytest
from sqlalchemy import create_engine, MetaData
import sqlalchemy.orm
from app.db import EventDetails, Base, DimAlert

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


def test_table_name():
    assert EventDetails.__tablename__ == "fct__event_details"
    assert DimAlert.__tablename__ == "dim__alert"


def test_schema():
    assert EventDetails.__table_args__["schema"] == "earthquake"
    assert DimAlert.__table_args__["schema"] == "earthquake"


def test_event_details_columns():
    columns = EventDetails.__table__.columns
    assert "id_event" in columns
    assert columns["id_event"].primary_key == True


def test_relationships():
    assert hasattr(EventDetails, "place")
    assert hasattr(EventDetails, "time")
    assert hasattr(EventDetails, "alert")

    # Test relationships
    assert "event_details" in EventDetails.place.property.back_populates
    assert "event_details" in EventDetails.time.property.back_populates
