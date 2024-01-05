import argparse
import logging
from nearquake.data_processor import Earthquake
from nearquake.config import (
    generate_time_period_url,
    ConnectionConfig,
    TIMESTAMP_NOW,
    EVENT_DETAIL_URL,
)
from nearquake.tweet_processor import TweetOperator
from sqlalchemy import desc
from nearquake.utils.db_sessions import DbSessionManager
from nearquake.app.db import EventDetails, Post, create_database

_logger = logging.getLogger(__name__)


def process_earthquake_data(conn, tweet, threshold):
    most_recent_date = (
        conn.session.query(EventDetails.ts_updated_utc)
        .order_by(desc(EventDetails.ts_updated_utc))
        .first()
    )

    most_recent_date = most_recent_date[0].strftime("%Y-%m-%d %H:%M:%S")
    most_recent_date_quakes = conn.fetch(
        model=EventDetails, column="ts_updated_utc", item=most_recent_date
    )

    try:
        for i in most_recent_date_quakes:
            if i.mag >= threshold:
                duration = TIMESTAMP_NOW - i.ts_event_utc

                text = f"Recent #Earthquake: {i.title} reported {duration.seconds/60:.0f} minutes ago, felt by {i.felt} people. \nSee more details at {EVENT_DETAIL_URL.format(i.id_event)}. \nData provided by https://www.usgs.gov/"
                item = {
                    "post": text,
                    "ts_upload_utc": TIMESTAMP_NOW.strftime("%Y-%m-%d %H:%M:%S"),
                }

                conn.insert(Post(**item))
                _logger.info(text)
                try:
                    tweet.post_tweet(tweet=text)
                    _logger.info(
                        "Recorded recent tweet posted in the database  recent into the Database "
                    )
                except Exception as e:
                    _logger.error(f"Encountered an unexpected error: {e}")
                    pass

    except Exception as e:
        _logger.error(f"Encountered an unexpected error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nearquake Data Processor")

    parser.add_argument(
        "-d", "--daily", action="store_true", help="Execute the daily program"
    )
    parser.add_argument(
        "-i",
        "--initialize",
        action="store_true",
        help="Initialize all required databases",
    )
    parser.add_argument(
        "-w", "--weekly", action="store_true", help="Execute the weekly program"
    )
    parser.add_argument(
        "-m", "--monthly", action="store_true", help="Execute the monthly program"
    )

    args = parser.parse_args()

    tweet = TweetOperator()
    conn = DbSessionManager(config=ConnectionConfig())
    run = Earthquake()

    with conn:
        if args.daily:
            run.extract_data_properties(url=generate_time_period_url("day"))
            process_earthquake_data(conn, tweet, threshold=5)

        if args.weekly:
            run.extract_data_properties(url=generate_time_period_url("week"))

        if args.monthly:
            run.extract_data_properties(url=generate_time_period_url("month"))

        if args.initialize:
            url = ConnectionConfig()
            create_database(
                url.generate_connection_url(), schema=["earthquake", "tweet"]
            )
