import random
from abc import ABC, abstractmethod
from datetime import timedelta

from nearquake.app.db import EventDetails, create_database
from nearquake.config import (
    CHAT_PROMPT,
    POSTGRES_CONNECTION_URL,
    TIMESTAMP_NOW,
    generate_time_period_url,
)
from nearquake.data_processor import (
    TweetEarthquakeEvents,
    UploadEarthQuakeEvents,
    UploadEarthQuakeLocation,
    get_date_range_summary,
)
from nearquake.open_ai_client import generate_response
from nearquake.post_manager import post_and_save_tweet
from nearquake.utils import format_earthquake_alert


class CommandHandler(ABC):
    """Base class for all command handlers."""

    @abstractmethod
    def execute(self, db_session):
        """Execute the command with the provided database session."""
        pass


class LiveCommandHandler(CommandHandler):
    """Handles live earthquake monitoring."""

    def __init__(self):
        self._days = 1
        self._today = TIMESTAMP_NOW.date()
        self._start_date = self._today - timedelta(days=self._days)

    def execute(self, db_session):
        run = UploadEarthQuakeEvents(conn=db_session)
        tweet = TweetEarthquakeEvents(conn=db_session)

        run.upload(url=generate_time_period_url("hour"))
        tweet.upload()


class SummaryCommandHandler(CommandHandler):
    """Base class for handlers that generate and post earthquake summaries."""

    def __init__(self):
        self._uploader = None
        self._period_name = None
        self._days = 0
        self._today = TIMESTAMP_NOW.date()
        self._start_date = self._today - timedelta(days=self._days)

    def execute(self, db_session):
        # Upload earthquake event data
        run = UploadEarthQuakeEvents(conn=db_session)
        run.upload(url=generate_time_period_url(self._period_name))

        # Get earthquake data for summary
        content = get_date_range_summary(
            conn=db_session,
            model=EventDetails,
            start_date=self._start_date,
            end_date=self._today,
        )

        # Upload location data for events in the date range
        loc = UploadEarthQuakeLocation(conn=db_session)
        loc.upload(
            start_date=self._start_date.strftime("%Y-%m-%d"),
            end_date=self._today.strftime("%Y-%m-%d"),
        )

        # Generate and post summary message
        message = self._generate_message(content)
        tweet_text = format_earthquake_alert(post_type="fact", message=message)

        if tweet_text:
            post_and_save_tweet(tweet_text, db_session)

    def _generate_message(self, content):
        """Generate the summary message with largest earthquake details."""
        if not content:
            return None

        # Find the largest earthquake
        largest_quake = max(content, key=lambda x: x.mag if x.mag else 0)

        # Format timestamp
        if largest_quake.ts_event_utc:
            time_str = largest_quake.ts_event_utc.strftime("%H:%M UTC")
        else:
            time_str = "unknown time"

        # Create the message
        if self._period_name == "day":
            period_text = "Over the last 24 hours"
        elif self._period_name == "week":
            period_text = "Over the last week"
        elif self._period_name == "month":
            period_text = "Over the last month"
        else:
            period_text = f"During the past {self._period_name}"

        message = (
            f"{period_text} there were {len(content):,} earthquakes detected and the largest being "
            f"M{largest_quake.mag:.1f} - {largest_quake.place} reported in at {time_str}\n\n"
            f"#Earthquake #SeismicActivity\n"
            f"Data: http://earthquake.usgs.gov"
        )

        return message


class DailyCommandHandler(SummaryCommandHandler):
    """Handles daily earthquake summary."""

    def __init__(self):
        super().__init__()
        self._period_name = "day"
        self._days = 1
        self._start_date = self._today - timedelta(days=self._days)

    def execute(self, db_session):
        """Execute daily summary with graphics."""
        # First run the standard summary (data upload + text tweet)
        super().execute(db_session)

        # Then post the daily summary graphic
        from nearquake.data_processor import TweetDailySummary

        daily_graphic = TweetDailySummary(conn=db_session)
        daily_graphic.upload()


class WeeklyCommandHandler(SummaryCommandHandler):
    """Handles weekly earthquake summary."""

    def __init__(self):
        super().__init__()
        self._period_name = "week"
        self._days = 7
        self._start_date = self._today - timedelta(days=self._days)

    def execute(self, db_session):
        """Execute weekly summary with graphics."""
        # First run the standard summary (data upload + text tweet)
        super().execute(db_session)

        # Then post the weekly summary graphic
        from nearquake.data_processor import TweetWeeklySummary

        weekly_graphic = TweetWeeklySummary(conn=db_session)
        weekly_graphic.upload()


class MonthlyCommandHandler(SummaryCommandHandler):
    """Handles monthly earthquake summary."""

    def __init__(self):
        super().__init__()
        self._period_name = "month"
        self._days = 30
        self._start_date = self._today - timedelta(days=self._days)


class FunFactCommandHandler(CommandHandler):
    """Handles sharing fun earthquake facts."""

    def execute(self, db_session):
        prompt = random.choice(CHAT_PROMPT)
        message = generate_response(prompt=prompt)

        tweet_text = format_earthquake_alert(post_type="fact", message=message)
        post_and_save_tweet(tweet_text, db_session)


class BackfillCommandHandler(CommandHandler):
    """Handles backfilling earthquake data."""

    def execute(self, db_session):
        start_date = input("Type Start Date:")
        end_date = input("Type End Date:")

        backfill_event = input("Backfill earthquake.fct__event_detail: True or Blank ")
        backfill_location = input(
            "Backfill earthquake.dim__event_location: True or Blank "
        )

        if backfill_event == "True":
            run = UploadEarthQuakeEvents(conn=db_session)
            run.backfill(start_date=start_date, end_date=end_date)

        if backfill_location == "True":
            loc = UploadEarthQuakeLocation(conn=db_session)
            loc.backfill(start_date=start_date, end_date=end_date)


class CommandHandlerFactory:
    """Factory for creating command handlers."""

    def __init__(self):
        self._handlers = {}

    def register(self, command_name, handler_class):
        """Register a handler class for a command."""
        self._handlers[command_name] = handler_class

    def create(self, command_name):
        """Create a handler instance for the given command."""
        handler_class = self._handlers.get(command_name)
        if handler_class:
            return handler_class()
        return None


class InitializeCommandHandler(CommandHandler):
    """Handles database initialization."""

    def execute(self, db_session):
        create_database(url=POSTGRES_CONNECTION_URL, schema=["earthquake", "tweet"])
