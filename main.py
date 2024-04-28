import argparse
import random
from datetime import datetime, timedelta

from nearquake.data_processor import (
    UploadEarthQuakeEvents,
    TweetEarthquakeEvents,
    UploadEarthQuakeLocation,
    get_date_range_summary,
)
from nearquake.config import (
    generate_time_period_url,
    tweet_conclusion_text,
    ConnectionConfig,
    CHAT_PROMPT,
    EARTHQUAKE_POST_THRESHOLD,
)
from nearquake.app.db import EventDetails
from nearquake.open_ai_client import generate_response
from nearquake.utils.db_sessions import DbSessionManager
from nearquake.app.db import create_database

from nearquake.utils import format_earthquake_alert

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
    parser.add_argument(
        "-b",
        "--backfill",
        action="store_true",
        help="backfill data base using a date range",
    )

    args = parser.parse_args()

    conn = DbSessionManager(config=ConnectionConfig())

    with conn:
        run = UploadEarthQuakeEvents(conn=conn)
        tweet = TweetEarthquakeEvents(conn=conn)
        loc = UploadEarthQuakeLocation(conn=conn)

        if args.live:
            for time in ["hour", "day", "week"]:
                run.upload(url=generate_time_period_url(time))
                tweet.upload()

        if args.daily:
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            start_date = yesterday - timedelta(days=1)
            content = get_date_range_summary(
                conn=conn, model=EventDetails, start_date=start_date, end_date=yesterday
            )

            GREATER_THAN_5 = sum(
                1
                for i in content
                if i.mag is not None and i.mag >= EARTHQUAKE_POST_THRESHOLD
            )
            TWEET_CONCLUSION_TEXT = tweet_conclusion_text()
            message = f"Yesterday, there were {len(content):,} #earthquakes globally, with {GREATER_THAN_5} of them registering a magnitude of 5.0 or higher. {TWEET_CONCLUSION_TEXT}"

            item = format_earthquake_alert(
                post_type="fact",
                message=message,
            )
            tweet.post_tweet(tweet=item, conn=conn)
            loc.upload(date=today.strftime("%Y-%m-%d"))

        if args.weekly:
            run.upload(url=generate_time_period_url("week"))

            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=7)
            content = get_date_range_summary(
                conn=conn, model=EventDetails, start_date=start_date, end_date=end_date
            )

            GREATER_THAN_5 = sum(
                1
                for i in content
                if i.mag is not None and i.mag >= EARTHQUAKE_POST_THRESHOLD
            )
            TWEET_CONCLUSION_TEXT = tweet_conclusion_text()

            message = f"During the past week, there were {len(content):,} #earthquakes globally, with {GREATER_THAN_5} of them registering a magnitude of 5.0 or higher. {TWEET_CONCLUSION_TEXT}"

            item = format_earthquake_alert(
                post_type="fact",
                message=message,
            )
            tweet.post_tweet(item=item, conn=conn)

        if args.monthly:
            run.upload(url=generate_time_period_url("month"))

            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            content = get_date_range_summary(
                conn=conn, model=EventDetails, start_date=start_date, end_date=end_date
            )

            GREATER_THAN_5 = sum(
                1
                for i in content
                if i.mag is not None and i.mag >= EARTHQUAKE_POST_THRESHOLD
            )
            TWEET_CONCLUSION_TEXT = tweet_conclusion_text()

            message = f"During the past month, there were {len(content):,} #earthquakes globally, with {GREATER_THAN_5} of them registering a magnitude of 5.0 or higher. {TWEET_CONCLUSION_TEXT}"

            item = format_earthquake_alert(
                post_type="fact",
                message=message,
            )
            tweet.post_tweet(item=item, conn=conn)

        if args.initialize:
            url = ConnectionConfig()
            create_database(
                url.generate_connection_url(), schema=["earthquake", "tweet"]
            )

        if args.fun:
            prompt = random.choice(CHAT_PROMPT)
            message = generate_response(prompt=prompt)

            item = format_earthquake_alert(
                post_type="fact", message=message, prompt=prompt
            )

            tweet.post_tweet(item=item, conn=conn)

        if args.backfill:
            start_date = input("Type Start Date:")
            end_date = input("Type End Date:")

            backfill_event = input(
                "Backfill earthquake.fct__event_detail: True or False "
            )
            backfill_location = input(
                "Backfill earthquake.dim__event_location: True or False "
            )

            if backfill_event:
                run.backfill(start_date=start_date, end_date=end_date)

            if backfill_location:
                loc.backfill(start_date=start_date, end_date=end_date)
