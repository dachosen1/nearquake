import unittest
from unittest.mock import MagicMock, patch

# Add these patches at the module level to mock OpenAI before it's imported
openai_patcher = patch("openai.OpenAI")
openai_patcher.start()

from datetime import datetime, timedelta

from nearquake.cli.command_handlers import (
    BackfillCommandHandler,
    CommandHandlerFactory,
    DailyCommandHandler,
    FunFactCommandHandler,
    InitializeCommandHandler,
    LiveCommandHandler,
    MonthlyCommandHandler,
    SummaryCommandHandler,
    WeeklyCommandHandler,
)


# Stop the patcher when the module is unloaded
def tearDownModule():
    openai_patcher.stop()


class TestCommandHandlerFactory(unittest.TestCase):
    """Test the CommandHandlerFactory class."""

    def setUp(self):
        self.factory = CommandHandlerFactory()
        self.mock_handler_class = MagicMock()

    def test_register_and_create(self):
        """Test registering and creating a handler."""
        # Register a mock handler
        self.factory.register("test_command", self.mock_handler_class)

        # Create an instance of the handler
        handler = self.factory.create("test_command")

        # Verify the mock class was called to create the handler
        self.mock_handler_class.assert_called_once()

        # Verify a handler was returned
        self.assertIsNotNone(handler)

    def test_create_nonexistent_handler(self):
        """Test creating a handler that hasn't been registered."""
        # Try to create a handler for a command that hasn't been registered
        handler = self.factory.create("nonexistent_command")

        # Verify no handler was returned
        self.assertIsNone(handler)


class TestLiveCommandHandler(unittest.TestCase):
    """Test the LiveCommandHandler class."""

    def setUp(self):
        self.handler = LiveCommandHandler()
        self.mock_db_session = MagicMock()

    @patch("nearquake.cli.command_handlers.UploadEarthQuakeEvents")
    @patch("nearquake.cli.command_handlers.TweetEarthquakeEvents")
    @patch("nearquake.cli.command_handlers.generate_time_period_url")
    def test_execute(self, mock_generate_url, mock_tweet_events, mock_upload_events):
        """Test the execute method."""
        # Set up mocks
        mock_upload_instance = mock_upload_events.return_value
        mock_tweet_instance = mock_tweet_events.return_value
        mock_generate_url.return_value = "http://example.com/hour"

        # Execute the handler
        self.handler.execute(self.mock_db_session)

        # Verify the mocks were called correctly
        mock_upload_events.assert_called_once_with(conn=self.mock_db_session)
        mock_tweet_events.assert_called_once_with(conn=self.mock_db_session)
        mock_upload_instance.upload.assert_called_once_with(
            url="http://example.com/hour"
        )
        mock_tweet_instance.upload.assert_called_once()
        mock_generate_url.assert_called_once_with("hour")


class TestSummaryCommandHandler(unittest.TestCase):
    """Test the SummaryCommandHandler class."""

    @patch("nearquake.cli.command_handlers.TIMESTAMP_NOW")
    def setUp(self, mock_timestamp):
        # Set up a fixed timestamp for testing
        self.today = datetime(2023, 1, 15).date()
        mock_timestamp.date.return_value = self.today

        # Create a concrete subclass for testing the abstract base class
        class ConcreteSummaryHandler(SummaryCommandHandler):
            def __init__(self):
                super().__init__()
                self._period_name = "test_period"
                self._days = 5
                self._start_date = self._today - timedelta(days=self._days)

        self.handler = ConcreteSummaryHandler()
        self.mock_db_session = MagicMock()

    @patch("nearquake.cli.command_handlers.UploadEarthQuakeEvents")
    @patch("nearquake.cli.command_handlers.get_date_range_summary")
    @patch("nearquake.cli.command_handlers.format_earthquake_alert")
    @patch("nearquake.cli.command_handlers.post_and_save_tweet")
    @patch("nearquake.cli.command_handlers.generate_time_period_url")
    def test_execute(
        self,
        mock_generate_url,
        mock_post_tweet,
        mock_format_alert,
        mock_get_summary,
        mock_upload_events,
    ):
        """Test the execute method."""
        # Set up mocks
        mock_upload_instance = mock_upload_events.return_value
        mock_generate_url.return_value = "http://example.com/test_period"

        # Mock earthquake events
        mock_event1 = MagicMock()
        mock_event1.mag = 4.5
        mock_event2 = MagicMock()
        mock_event2.mag = 5.2
        mock_get_summary.return_value = [mock_event1, mock_event2]

        # Mock formatting and posting
        mock_format_alert.return_value = "Formatted tweet text"

        # Execute the handler
        self.handler.execute(self.mock_db_session)

        # Verify the mocks were called correctly
        mock_upload_events.assert_called_once_with(conn=self.mock_db_session)
        mock_upload_instance.upload.assert_called_once_with(
            url="http://example.com/test_period"
        )
        mock_get_summary.assert_called_once()
        mock_format_alert.assert_called_once()
        mock_post_tweet.assert_called_once_with(
            "Formatted tweet text", self.mock_db_session
        )

    def test_generate_message(self):
        """Test the _generate_message method."""
        # Create mock earthquake events
        mock_event1 = MagicMock()
        mock_event1.mag = 4.5
        mock_event2 = MagicMock()
        mock_event2.mag = 5.2
        mock_event3 = MagicMock()
        mock_event3.mag = 6.0
        mock_events = [mock_event1, mock_event2, mock_event3]

        # Test with period_name = "day"
        self.handler._period_name = "day"
        message = self.handler._generate_message(mock_events)
        self.assertIn("Yesterday", message)
        self.assertIn("3", message)  # Total earthquakes
        # There are 2 earthquakes with mag >= 5.0, but we need to check for the actual count in the message
        # The implementation is counting all earthquakes with mag >= EARTHQUAKE_POST_THRESHOLD
        # Let's patch the EARTHQUAKE_POST_THRESHOLD value to ensure our test is accurate
        with patch("nearquake.cli.command_handlers.EARTHQUAKE_POST_THRESHOLD", 5.0):
            message = self.handler._generate_message(mock_events)
            self.assertIn("2", message)  # Earthquakes >= 5.0

        # Test with a different period_name
        self.handler._period_name = "week"
        message = self.handler._generate_message(mock_events)
        self.assertIn("During the past week", message)
        self.assertIn("3", message)  # Total earthquakes


class TestDailyCommandHandler(unittest.TestCase):
    """Test the DailyCommandHandler class."""

    @patch("nearquake.cli.command_handlers.TIMESTAMP_NOW")
    def test_initialization(self, mock_timestamp):
        """Test the initialization of DailyCommandHandler."""
        # Set up a fixed timestamp for testing
        today = datetime(2023, 1, 15).date()
        mock_timestamp.date.return_value = today

        # Create the handler
        handler = DailyCommandHandler()

        # Verify the handler was initialized correctly
        self.assertEqual(handler._period_name, "day")
        self.assertEqual(handler._days, 1)
        self.assertEqual(handler._start_date, today - timedelta(days=1))


class TestWeeklyCommandHandler(unittest.TestCase):
    """Test the WeeklyCommandHandler class."""

    @patch("nearquake.cli.command_handlers.TIMESTAMP_NOW")
    def test_initialization(self, mock_timestamp):
        """Test the initialization of WeeklyCommandHandler."""
        # Set up a fixed timestamp for testing
        today = datetime(2023, 1, 15).date()
        mock_timestamp.date.return_value = today

        # Create the handler
        handler = WeeklyCommandHandler()

        # Verify the handler was initialized correctly
        self.assertEqual(handler._period_name, "week")
        self.assertEqual(handler._days, 7)
        self.assertEqual(handler._start_date, today - timedelta(days=7))


class TestMonthlyCommandHandler(unittest.TestCase):
    """Test the MonthlyCommandHandler class."""

    @patch("nearquake.cli.command_handlers.TIMESTAMP_NOW")
    def test_initialization(self, mock_timestamp):
        """Test the initialization of MonthlyCommandHandler."""
        # Set up a fixed timestamp for testing
        today = datetime(2023, 1, 15).date()
        mock_timestamp.date.return_value = today

        # Create the handler
        handler = MonthlyCommandHandler()

        # Verify the handler was initialized correctly
        self.assertEqual(handler._period_name, "month")
        self.assertEqual(handler._days, 30)
        self.assertEqual(handler._start_date, today - timedelta(days=30))


class TestFunFactCommandHandler(unittest.TestCase):
    """Test the FunFactCommandHandler class."""

    def setUp(self):
        self.handler = FunFactCommandHandler()
        self.mock_db_session = MagicMock()

    @patch("nearquake.cli.command_handlers.random.choice")
    @patch("nearquake.cli.command_handlers.generate_response")
    @patch("nearquake.cli.command_handlers.format_earthquake_alert")
    @patch("nearquake.cli.command_handlers.post_and_save_tweet")
    def test_execute(
        self, mock_post_tweet, mock_format_alert, mock_generate_response, mock_choice
    ):
        """Test the execute method."""
        # Set up mocks
        mock_choice.return_value = "Test prompt"
        mock_generate_response.return_value = "Fun earthquake fact"
        mock_format_alert.return_value = "Formatted tweet text"

        # Execute the handler
        self.handler.execute(self.mock_db_session)

        # Verify the mocks were called correctly
        mock_choice.assert_called_once()
        mock_generate_response.assert_called_once_with(prompt="Test prompt")
        mock_format_alert.assert_called_once_with(
            post_type="fact", message="Fun earthquake fact"
        )
        mock_post_tweet.assert_called_once_with(
            "Formatted tweet text", self.mock_db_session
        )


class TestInitializeCommandHandler(unittest.TestCase):
    """Test the InitializeCommandHandler class."""

    def setUp(self):
        self.handler = InitializeCommandHandler()
        self.mock_db_session = MagicMock()

    @patch("nearquake.cli.command_handlers.create_database")
    @patch("nearquake.cli.command_handlers.POSTGRES_CONNECTION_URL", "test_url")
    def test_execute(self, mock_create_database):
        """Test the execute method."""
        # Execute the handler
        self.handler.execute(self.mock_db_session)

        # Verify the mock was called correctly
        mock_create_database.assert_called_once_with(
            url="test_url", schema=["earthquake", "tweet"]
        )


class TestBackfillCommandHandler(unittest.TestCase):
    """Test the BackfillCommandHandler class."""

    def setUp(self):
        self.handler = BackfillCommandHandler(
            start_date="2023-01-01",
            end_date="2023-01-31", 
            backfill_events=True,
            backfill_locations=True
        )
        self.mock_db_session = MagicMock()

    @patch("nearquake.cli.command_handlers.UploadEarthQuakeEvents")
    @patch("nearquake.cli.command_handlers.UploadEarthQuakeLocation")
    def test_execute_with_both_backfills(
        self, mock_upload_location, mock_upload_events
    ):
        """Test the execute method with both backfills enabled."""
        # Set up mocks
        mock_upload_events_instance = mock_upload_events.return_value
        mock_upload_location_instance = mock_upload_location.return_value

        # Execute the handler
        self.handler.execute(self.mock_db_session)

        # Verify the mocks were called correctly
        mock_upload_events.assert_called_once_with(conn=self.mock_db_session)
        mock_upload_location.assert_called_once_with(conn=self.mock_db_session)
        mock_upload_events_instance.backfill.assert_called_once_with(
            start_date="2023-01-01", end_date="2023-01-31"
        )
        mock_upload_location_instance.backfill.assert_called_once_with(
            start_date="2023-01-01", end_date="2023-01-31"
        )

    @patch("nearquake.cli.command_handlers.UploadEarthQuakeEvents")
    @patch("nearquake.cli.command_handlers.UploadEarthQuakeLocation")
    def test_execute_with_events_only(
        self, mock_upload_location, mock_upload_events
    ):
        """Test the execute method with only event backfill enabled."""
        # Create handler with only events enabled
        handler = BackfillCommandHandler(
            start_date="2023-01-01",
            end_date="2023-01-31", 
            backfill_events=True,
            backfill_locations=False
        )
        mock_upload_events_instance = mock_upload_events.return_value

        # Execute the handler
        handler.execute(self.mock_db_session)

        # Verify the mocks were called correctly
        mock_upload_events.assert_called_once_with(conn=self.mock_db_session)
        mock_upload_events_instance.backfill.assert_called_once_with(
            start_date="2023-01-01", end_date="2023-01-31"
        )
        mock_upload_location.assert_not_called()

    @patch("nearquake.cli.command_handlers.UploadEarthQuakeEvents")
    @patch("nearquake.cli.command_handlers.UploadEarthQuakeLocation")
    def test_execute_with_location_only(
        self, mock_upload_location, mock_upload_events
    ):
        """Test the execute method with only location backfill enabled."""
        # Create handler with only locations enabled
        handler = BackfillCommandHandler(
            start_date="2023-01-01",
            end_date="2023-01-31", 
            backfill_events=False,
            backfill_locations=True
        )
        mock_upload_location_instance = mock_upload_location.return_value

        # Execute the handler
        handler.execute(self.mock_db_session)

        # Verify the mocks were called correctly
        mock_upload_events.assert_not_called()
        mock_upload_location.assert_called_once_with(conn=self.mock_db_session)
        mock_upload_location_instance.backfill.assert_called_once_with(
            start_date="2023-01-01", end_date="2023-01-31"
        )

    def test_execute_missing_dates_raises_error(self):
        """Test that execute raises ValueError when dates are missing."""
        handler = BackfillCommandHandler(
            start_date=None,
            end_date=None, 
            backfill_events=True,
            backfill_locations=True
        )
        
        with self.assertRaises(ValueError) as context:
            handler.execute(self.mock_db_session)
        
        self.assertIn("start_date and end_date are required", str(context.exception))
