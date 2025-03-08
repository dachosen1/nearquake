import datetime
import unittest
from unittest.mock import MagicMock, patch

import pytest
import sqlalchemy.orm
from sqlalchemy import MetaData, create_engine
from sqlalchemy.exc import SQLAlchemyError

from nearquake.app import DatabaseCreationError
from nearquake.app.db import (
    Base,
    EventDetails,
    LocationDetails,
    Post,
    create_database,
)

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


class TestDatabaseModels(unittest.TestCase):
    """Unit tests for database models"""

    def test_event_details_model(self):
        """Test EventDetails model creation and attributes"""
        event = EventDetails(
            id_event="test123",
            mag=5.6,
            ts_updated_utc=datetime.datetime.now(datetime.UTC),
            ts_event_utc=datetime.datetime.now(datetime.UTC),
            tz=-7,
            felt=150,
            longitude=-122.5,
            latitude=37.8,
            detail="Test earthquake details",
            cdi=4.5,
            mmi=5.0,
            status="reviewed",
            tsunami=False,
            type="earthquake",
            title="M 5.6 - Near San Francisco, CA",
            date=datetime.date.today(),
            place="10km W of San Francisco, CA",
        )

        self.assertEqual(event.id_event, "test123")
        self.assertEqual(event.mag, 5.6)
        self.assertEqual(event.tz, -7)
        self.assertEqual(event.felt, 150)
        self.assertEqual(event.longitude, -122.5)
        self.assertEqual(event.latitude, 37.8)
        self.assertEqual(event.status, "reviewed")
        self.assertEqual(event.tsunami, False)
        self.assertEqual(event.type, "earthquake")
        self.assertEqual(event.place, "10km W of San Francisco, CA")

    def test_post_model(self):
        """Test Post model creation and attributes"""
        post = Post(
            id_post="post123",
            post="This is a test earthquake post",
            id_event="test123",
            post_type="event",
            prompt="earthquake_announcement",
            ts_upload_utc=datetime.datetime.now(datetime.UTC),
        )

        self.assertEqual(post.id_post, "post123")
        self.assertEqual(post.post, "This is a test earthquake post")
        self.assertEqual(post.id_event, "test123")
        self.assertEqual(post.post_type, "event")
        self.assertEqual(post.prompt, "earthquake_announcement")

    def test_location_details_model(self):
        """Test LocationDetails model creation and attributes"""
        location = LocationDetails(
            id_event="test123",
            continent="North America",
            continentCode="NA",
            countryName="United States",
            countryCode="US",
            principalSubdivision="California",
            principalSubdivisionCode="CA",
            city="San Francisco",
        )

        self.assertEqual(location.id_event, "test123")
        self.assertEqual(location.continent, "North America")
        self.assertEqual(location.continentCode, "NA")
        self.assertEqual(location.countryName, "United States")
        self.assertEqual(location.countryCode, "US")
        self.assertEqual(location.principalSubdivision, "California")
        self.assertEqual(location.principalSubdivisionCode, "CA")
        self.assertEqual(location.city, "San Francisco")


class TestDatabaseFunctions(unittest.TestCase):
    """Unit tests for database functions"""

    @patch("nearquake.app.db.create_engine")
    def test_create_database_success(self, mock_create_engine):
        """Test successful database creation"""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        # Mock the metadata.create_all method
        with patch.object(Base.metadata, "create_all") as mock_create_all:
            result = create_database("sqlite:///test.db")

            # Verify create_engine was called with the correct URL
            mock_create_engine.assert_called_once_with("sqlite:///test.db")

            # Verify metadata.create_all was called with the engine
            mock_create_all.assert_called_once_with(mock_engine)

            # Verify the function returns the engine
            self.assertEqual(result, mock_engine)

    @patch("nearquake.app.db.create_engine")
    def test_create_database_with_schema(self, mock_create_engine):
        """Test database creation with schema creation"""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        # Mock create_schema function
        with patch("nearquake.app.db.create_schema") as mock_create_schema:
            with patch.object(Base.metadata, "create_all"):
                create_database("sqlite:///test.db", schema=["earthquake", "tweet"])

                # Verify create_schema was called with the engine and schema list
                mock_create_schema.assert_called_once_with(
                    mock_engine, ["earthquake", "tweet"]
                )

    @patch("nearquake.app.db.create_engine")
    def test_create_database_error(self, mock_create_engine):
        """Test error handling during database creation"""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        # Make metadata.create_all raise an exception
        with patch.object(
            Base.metadata, "create_all", side_effect=SQLAlchemyError("Test error")
        ):
            with self.assertRaises(DatabaseCreationError):
                create_database("sqlite:///test.db")


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database operations using an in-memory SQLite database"""

    @pytest.fixture
    def db_engine(self):
        """Create an in-memory SQLite database for testing"""
        # Use the correct import path for declarative_base
        from sqlalchemy import (
            TIMESTAMP,
            Boolean,
            Column,
            Date,
            Float,
            ForeignKey,
            Integer,
            String,
        )
        from sqlalchemy.orm import declarative_base, relationship

        TestBase = declarative_base()

        # Recreate models without schema for SQLite testing
        class TestEventDetails(TestBase):
            __tablename__ = "fct__event_details"

            id_event = Column(String(50), primary_key=True)
            mag = Column(Float)
            ts_updated_utc = Column(TIMESTAMP)
            ts_event_utc = Column(TIMESTAMP)
            tz = Column(Integer)
            felt = Column(Integer)
            longitude = Column(Float)
            latitude = Column(Float)
            detail = Column(String(500))
            cdi = Column(Float)
            mmi = Column(Float)
            status = Column(String(50))
            tsunami = Column(Boolean)
            type = Column(String(50))
            title = Column(String(200))
            date = Column(Date)
            place = Column(String(200))
            location = relationship(
                "TestLocationDetails", back_populates="event_detail", uselist=False
            )

        class TestPost(TestBase):
            __tablename__ = "fct__post"

            id_post = Column(String(50), primary_key=True)
            post = Column(String(2000))
            id_event = Column(
                String(50), ForeignKey("fct__event_details.id_event"), unique=True
            )
            post_type = Column(String(50), nullable=True)
            prompt = Column(String(50), nullable=True)
            ts_upload_utc = Column(TIMESTAMP, nullable=True)

        class TestLocationDetails(TestBase):
            __tablename__ = "dim__location_details"

            id_event = Column(
                String(50), ForeignKey("fct__event_details.id_event"), primary_key=True
            )
            continent = Column(String(50))
            continentCode = Column(String(10))
            countryName = Column(String(100))
            countryCode = Column(String(10))
            principalSubdivision = Column(String(100))
            principalSubdivisionCode = Column(String(10))
            city = Column(String(100))
            event_detail = relationship(
                "TestEventDetails", back_populates="location", uselist=False
            )

        # Store the test models on the class for use in tests
        self.TestEventDetails = TestEventDetails
        self.TestPost = TestPost
        self.TestLocationDetails = TestLocationDetails

        # Create the engine and tables
        engine = create_engine("sqlite:///:memory:")
        TestBase.metadata.create_all(engine)
        return engine

    @pytest.fixture
    def db_session(self, db_engine):
        """Create a new database session for testing"""
        from sqlalchemy.orm import Session

        connection = db_engine.connect()
        transaction = connection.begin()
        session = Session(bind=connection)

        yield session

        session.close()
        transaction.rollback()
        connection.close()

    def test_create_and_query_event(self, db_session):
        """Test creating and querying an earthquake event"""
        import datetime

        # Create a test event using the test model
        event = self.TestEventDetails(
            id_event="test123",
            mag=5.6,
            ts_updated_utc=datetime.datetime.now(datetime.UTC),
            ts_event_utc=datetime.datetime.now(datetime.UTC),
            tz=-7,
            felt=150,
            longitude=-122.5,
            latitude=37.8,
            detail="Test earthquake details",
            status="reviewed",
            tsunami=False,
            type="earthquake",
            title="M 5.6 - Near San Francisco, CA",
            date=datetime.date.today(),
            place="10km W of San Francisco, CA",
        )

        db_session.add(event)
        db_session.commit()

        # Query the event
        queried_event = (
            db_session.query(self.TestEventDetails)
            .filter_by(id_event="test123")
            .first()
        )

        assert queried_event is not None
        assert queried_event.id_event == "test123"
        assert queried_event.mag == 5.6
        assert queried_event.place == "10km W of San Francisco, CA"

    def test_relationship_event_location(self, db_session):
        """Test relationship between EventDetails and LocationDetails"""
        import datetime

        # Create a test event
        event = self.TestEventDetails(
            id_event="test456",
            mag=6.2,
            ts_updated_utc=datetime.datetime.now(datetime.UTC),
            ts_event_utc=datetime.datetime.now(datetime.UTC),
            tz=-7,
            longitude=-122.5,
            latitude=37.8,
            status="reviewed",
            tsunami=False,
            type="earthquake",
            title="M 6.2 - Near Los Angeles, CA",
            date=datetime.date.today(),
            place="15km N of Los Angeles, CA",
        )

        # Create a location for the event
        location = self.TestLocationDetails(
            id_event="test456",
            continent="North America",
            continentCode="NA",
            countryName="United States",
            countryCode="US",
            principalSubdivision="California",
            principalSubdivisionCode="CA",
            city="Los Angeles",
        )

        # Add both to the session and commit
        db_session.add(event)
        db_session.add(location)
        db_session.commit()

        # Query the event and check the relationship
        queried_event = (
            db_session.query(self.TestEventDetails)
            .filter_by(id_event="test456")
            .first()
        )

        assert queried_event is not None
        assert queried_event.location is not None
        assert queried_event.location.city == "Los Angeles"
        assert queried_event.location.countryName == "United States"

        # Query the location and check the relationship
        queried_location = (
            db_session.query(self.TestLocationDetails)
            .filter_by(id_event="test456")
            .first()
        )

        assert queried_location is not None
        assert queried_location.event_detail is not None
        assert queried_location.event_detail.mag == 6.2

    def test_create_and_query_post(self, db_session):
        """Test creating and querying a post related to an event"""
        import datetime

        # Create a test event
        event = self.TestEventDetails(
            id_event="test789",
            mag=4.8,
            ts_updated_utc=datetime.datetime.now(datetime.UTC),
            ts_event_utc=datetime.datetime.now(datetime.UTC),
            tz=-5,
            longitude=-74.0,
            latitude=40.7,
            status="reviewed",
            tsunami=False,
            type="earthquake",
            title="M 4.8 - Near New York, NY",
            date=datetime.date.today(),
            place="5km S of New York, NY",
        )

        # Create a post for the event
        post = self.TestPost(
            id_post="post789",
            post="Earthquake alert: M4.8 earthquake detected near New York City",
            id_event="test789",
            post_type="alert",
            prompt="earthquake_alert",
            ts_upload_utc=datetime.datetime.now(datetime.UTC),
        )

        # Add both to the session and commit
        db_session.add(event)
        db_session.add(post)
        db_session.commit()

        # Query the post
        queried_post = (
            db_session.query(self.TestPost).filter_by(id_post="post789").first()
        )

        assert queried_post is not None
        assert queried_post.id_event == "test789"
        assert queried_post.post_type == "alert"
        assert "M4.8 earthquake" in queried_post.post


# Also, let's add a test for the create_database function
def test_create_database_with_schema(monkeypatch):
    """Test the create_database function with schema creation"""
    from unittest.mock import MagicMock, patch

    from nearquake.app.db import create_database

    # Mock the create_engine function
    mock_engine = MagicMock()
    mock_create_engine = MagicMock(return_value=mock_engine)
    monkeypatch.setattr("nearquake.app.db.create_engine", mock_create_engine)

    # Mock the create_schema function
    mock_create_schema = MagicMock()
    monkeypatch.setattr("nearquake.app.db.create_schema", mock_create_schema)

    # Mock Base.metadata.create_all
    mock_create_all = MagicMock()
    monkeypatch.setattr("nearquake.app.db.Base.metadata.create_all", mock_create_all)

    # Call the function
    result = create_database(
        "postgresql://user:pass@localhost/testdb", schema=["earthquake", "tweet"]
    )

    # Verify create_engine was called with the correct URL
    mock_create_engine.assert_called_once_with(
        "postgresql://user:pass@localhost/testdb"
    )

    # Verify create_schema was called with the engine and schema list
    mock_create_schema.assert_called_once_with(mock_engine, ["earthquake", "tweet"])

    # Verify metadata.create_all was called with the engine
    mock_create_all.assert_called_once_with(mock_engine)

    # Verify the function returns the engine
    assert result == mock_engine
