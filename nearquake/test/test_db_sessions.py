import logging
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine

from nearquake.utils.db_sessions import DbSessionManager

# Configure logging for tests
logging.basicConfig(level=logging.INFO)


# Mock SQLAlchemy model for testing
class MockModel:
    id = 1
    name = "test"


@pytest.fixture
def mock_engine():
    return Mock(spec=create_engine)


@pytest.fixture
def mock_session():
    session = Mock()
    session.query.return_value = session
    session.filter.return_value = session
    session.all.return_value = [MockModel()]
    return session


@pytest.fixture
def mock_scoped_session(mock_session):
    return Mock(return_value=mock_session)


@pytest.fixture
def db_manager(mock_engine, mock_scoped_session):
    with patch("nearquake.utils.db_sessions.create_engine", return_value=mock_engine):
        with patch(
            "nearquake.utils.db_sessions.scoped_session",
            return_value=mock_scoped_session,
        ):
            manager = DbSessionManager(url="sqlite:///test.db")
            yield manager


def test_init_success(db_manager):
    assert db_manager.url == "sqlite:///test.db"
    assert db_manager.engine is not None


def test_init_failure():
    with patch(
        "nearquake.utils.db_sessions.create_engine",
        side_effect=Exception("Connection failed"),
    ):
        manager = DbSessionManager(url="invalid://url")
        assert not hasattr(manager, "Session")  # Session should not be created
        assert manager.url == "invalid://url"  # URL should still be set


def test_fetch_single(db_manager, mock_session):
    # Setup
    db_manager.session = mock_session

    # Execute
    result = db_manager.fetch_single(MockModel, "name", "test")

    # Assert
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 1
    mock_session.query.assert_called_once_with(MockModel)


def test_fetch_many(db_manager, mock_session):
    # Setup
    db_manager.session = mock_session
    items = ["test1", "test2"]

    # Create a mock column with in_ method
    mock_column = Mock()
    mock_column.in_.return_value = True

    # Mock getattr to return our mock column
    with patch("nearquake.utils.db_sessions.getattr", return_value=mock_column):
        # Execute
        result = db_manager.fetch_many(MockModel, "name", items)

        # Assert
        assert result is not None
        assert isinstance(result, list)
        mock_session.query.assert_called_once_with(MockModel)
        mock_column.in_.assert_called_once_with(items)


def test_insert(db_manager, mock_session):
    # Setup
    db_manager.session = mock_session
    model = MockModel()

    # Execute
    db_manager.insert(model)

    # Assert
    mock_session.add.assert_called_once_with(model)
    mock_session.commit.assert_called_once()


def test_insert_many(db_manager, mock_session):
    # Setup
    db_manager.session = mock_session
    models = [MockModel(), MockModel()]

    # Execute
    db_manager.insert_many(models)

    # Assert
    assert mock_session.add.call_count == 2
    mock_session.commit.assert_called_once()


def test_insert_many_failure(db_manager, mock_session):
    # Setup
    db_manager.session = mock_session
    mock_session.commit.side_effect = Exception("Commit failed")
    models = [MockModel(), MockModel()]

    # Execute
    db_manager.insert_many(models)

    # Assert
    mock_session.rollback.assert_called_once()


def test_close(db_manager, mock_session):
    # Setup
    db_manager.session = mock_session

    # Execute
    db_manager.close()

    # Assert
    mock_session.close.assert_called_once()


def test_context_manager(db_manager, mock_scoped_session):
    with db_manager as session:
        assert session is not None
        mock_scoped_session.assert_called_once()
