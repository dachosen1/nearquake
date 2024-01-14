import argparse

from nearquake.data_processor import (
    Earthquake,
    process_earthquake_data,
    get_date_range_summary,
)
from nearquake.config import (
    generate_time_period_url,
    ConnectionConfig,
    CHAT_PROMPT,
    TWEET_CONCLUSION,
)
from nearquake.app.db import EventDetails

from random import randint
from datetime import datetime, timedelta
from nearquake.open_ai_client import generate_response
from nearquake.tweet_processor import TweetOperator
from nearquake.utils.db_sessions import DbSessionManager
from nearquake.app.db import create_database

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nearquake Data Processor")

    parser.add_argument(
        "-d", "--daily", action="store_true", help="Execute the daily program"
    )

    parser.add_argument(
        "-l",
        "--live",
        action="store_true",
        help=" Periodically check for new earhquakes",
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

    parser.add_argument(
        "-f", "--fun", action="store_true", help="Tells a fun fact about earthquakes"
    )

    args = parser.parse_args()

    tweet = TweetOperator()
    conn = DbSessionManager(config=ConnectionConfig())
    run = Earthquake()

    with conn:
        if args.live:
            run.extract_data_properties(
                url=generate_time_period_url("month"), conn=conn
            )
            process_earthquake_data(conn, tweet, threshold=4)

        if args.daily:
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            start_date = yesterday - timedelta(days=1)
            content = get_date_range_summary(
                conn=conn, model=EventDetails, start_date=start_date, end_date=yesterday
            )

            GREATER_THAN_5 = sum(1 for i in content if i.mag is not None and i.mag >= 5)
            TWEET_CONCLUSION_TEXT = TWEET_CONCLUSION[
                randint(0, len(TWEET_CONCLUSION) - 1)
            ]
            message = f"Yesterday, there were {len(content):,} #earthquakes globally, with {GREATER_THAN_5} of them registering a magnitude of 5.0 or higher. {TWEET_CONCLUSION_TEXT}"
            tweet.post_tweet(tweet=message)

        if args.weekly:
            run.extract_data_properties(url=generate_time_period_url("week"), conn=conn)

            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=7)
            content = get_date_range_summary(
                conn=conn, model=EventDetails, start_date=start_date, end_date=end_date
            )

            GREATER_THAN_5 = sum(1 for i in content if i.mag is not None and i.mag >= 5)
            TWEET_CONCLUSION_TEXT = TWEET_CONCLUSION[
                randint(0, len(TWEET_CONCLUSION) - 1)
            ]

            message = f"During the past week, there were {len(content):,} #earthquakes globally, with {GREATER_THAN_5} of them registering a magnitude of 5.0 or higher. {TWEET_CONCLUSION_TEXT}"
            tweet.post_tweet(tweet=message)

        if args.monthly:
            run.extract_data_properties(
                url=generate_time_period_url("month"), conn=conn
            )

            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            content = get_date_range_summary(
                conn=conn, model=EventDetails, start_date=start_date, end_date=end_date
            )

            GREATER_THAN_5 = sum(1 for i in content if i.mag is not None and i.mag >= 5)
            TWEET_CONCLUSION_TEXT = TWEET_CONCLUSION[
                randint(0, len(TWEET_CONCLUSION) - 1)
            ]
            message = f"During the past month, there were {len(content):,} #earthquakes globally, with {GREATER_THAN_5} of them registering a magnitude of 5.0 or higher. {TWEET_CONCLUSION_TEXT}"
            tweet.post_tweet(tweet=message)

        if args.initialize:
            url = ConnectionConfig()
            create_database(
                url.generate_connection_url(), schema=["earthquake", "tweet"]
            )

        if args.fun:
            content = generate_response(
                prompt=CHAT_PROMPT[randint(0, len(CHAT_PROMPT) - 1)]
            )
            tweet.post_tweet(tweet=content)
