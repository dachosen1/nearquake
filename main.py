import argparse

from nearquake.data_processor import Earthquake, process_earthquake_data
from nearquake.config import generate_time_period_url, ConnectionConfig, CHAT_PROMPT

from random import randint
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
        if args.daily:
            run.extract_data_properties(url=generate_time_period_url("day"))

            conn = DbSessionManager(config=ConnectionConfig())
            conn.connect()
            process_earthquake_data(conn, tweet, threshold=4)

        if args.weekly:
            run.extract_data_properties(url=generate_time_period_url("week"))

        if args.monthly:
            run.extract_data_properties(url=generate_time_period_url("month"))

        if args.initialize:
            url = ConnectionConfig()
            create_database(
                url.generate_connection_url(), schema=["earthquake", "tweet"]
            )

        if args.fun:
            content = generate_response(
                prompt=CHAT_PROMPT[randint(0, len(CHAT_PROMPT) - 0)]
            )
            tweet.post_tweet(tweet=content)
