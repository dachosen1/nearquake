import pytest
from sqlalchemy import create_engine, MetaData
import sqlalchemy.orm
from nearquake.app.db import EventDetails, Base, Post

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


def test_twiiter_schema_tables():
    assert Post.__tablename__ == "fct__post"


def test_schema():
    assert EventDetails.__table_args__["schema"] == "earthquake"


def test_event_details_columns():
    columns = EventDetails.__table__.columns
    assert "id_event" in columns
    assert columns["id_event"].primary_key is True
