import argparse
import random
from datetime import datetime, timedelta

from nearquake.app.db import EventDetails, create_database
from nearquake.config import (
    CHAT_PROMPT,
    EARTHQUAKE_POST_THRESHOLD,
    POSTGRES_CONNECTION_URL,
    generate_time_period_url,
    tweet_conclusion_text,
)
from nearquake.data_processor import (
    TweetEarthquakeEvents,
    UploadEarthQuakeEvents,
    UploadEarthQuakeLocation,
    get_date_range_summary,
)
from nearquake.post_manager import post_to_all_platforms, save_tweet_to_db
from nearquake.open_ai_client import generate_response
from nearquake.utils import convert_datetime, format_earthquake_alert
from nearquake.utils.db_sessions import DbSessionManager

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

    conn = DbSessionManager(url=POSTGRES_CONNECTION_URL)

    with conn:
        run = UploadEarthQuakeEvents(conn=conn)
        tweet = TweetEarthquakeEvents(conn=conn)
        loc = UploadEarthQuakeLocation(conn=conn)

        if args.live:
            for time in ["hour", "day", "week"]:
                run.upload(url=generate_time_period_url(time))
                tweet.upload()

            start_date = datetime.now().date() - timedelta(days=30)
            end_date = datetime.now().date()
            loc.backfill(
                start_date=convert_datetime(start_date, format_type="date"),
                end_date=convert_datetime(end_date, format_type="date"),
            )

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

            tweet_text = format_earthquake_alert(
                post_type="fact",
                message=message,
            )
            post_to_all_platforms(text=tweet_text.get("post"))
            save_tweet_to_db(tweet_text, conn)

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

            tweet_text = format_earthquake_alert(
                post_type="fact",
                message=message,
            )
            post_to_all_platforms(text=tweet_text.get("post"))
            save_tweet_to_db(tweet_text, conn)

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

            tweet_text = format_earthquake_alert(
                post_type="fact",
                message=message,
            )
            post_to_all_platforms(text=tweet_text.get("post"))
            save_tweet_to_db(tweet_text, conn)

        if args.initialize:
            create_database(url=POSTGRES_CONNECTION_URL, schema=["earthquake", "tweet"])

        if args.fun:
            prompt = random.choice(CHAT_PROMPT)
            message = generate_response(prompt=prompt)

            tweet_text = format_earthquake_alert(post_type="fact", message=message)

            post_to_all_platforms(text=tweet_text.get("post"))
            save_tweet_to_db(tweet_text, conn)

        if args.backfill:
            start_date = input("Type Start Date:")
            end_date = input("Type End Date:")

            backfill_event = input(
                "Backfill earthquake.fct__event_detail: True or Blank "
            )
            backfill_location = input(
                "Backfill earthquake.dim__event_location: True or Blank "
            )

            if backfill_event == "True":
                run.backfill(start_date=start_date, end_date=end_date)

            if backfill_location == "True":
                loc.backfill(start_date=start_date, end_date=end_date)
