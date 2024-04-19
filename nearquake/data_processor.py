import logging
import random
from typing import List, Type

from sqlalchemy import desc, and_
from sqlalchemy.orm import Session, declarative_base

from nearquake.config import (
    generate_time_range_url,
    TIMESTAMP_NOW,
    EVENT_DETAIL_URL,
    TWEET_CONCLUSION,
    REPORTED_SINCE_THRESHOLD,
)
from nearquake.tweet_processor import TweetOperator
from nearquake.app.db import EventDetails, Post
from tqdm import tqdm
from nearquake.utils import (
    fetch_json_data_from_url,
    convert_timestamp_to_utc,
    generate_date_range,
)


_logger = logging.getLogger(__name__)

Base = declarative_base()


class Earthquake:
    """
    The Earthquake class is designed to interact with the earthquake.usgs.gov API to
    retrieve and store earthquake data. It provides functionalities to extract earthquake
    event data and perform backfill operations for a specified date range.
    """

    def __init__(self) -> None:
        self.TIMESTAMP_NOW = TIMESTAMP_NOW.strftime("%Y-%m-%d %H:%M:%S")

    def extract_data_properties(self, url: str, conn: Session) -> None:
        """
        Extracts earthquake data from a given URL, typically from earthquake.usgs.gov, and
        uploads key properties of each earthquake event into a database.

        This method iterates through the earthquake data, extracts relevant properties, and
        inserts them into the database. It also handles duplicate records by skipping insertion
        if an event with the same ID already exists in the database.

        Note: this function only works for a speficific url, since it's expect the JSON api repsonse to follow a specific format.

        Example Usage:
        run = Earthquake()
        run.extract_data_properties("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson")

        :param url: The URL to fetch earthquake data from.
        """
        data = fetch_json_data_from_url(url=url)

        summary = {}

        try:
            # Check for all the records in the api
            event_id_set = {i["id"] for i in data["features"]}

            # Check for records that exists in the database
            fetched_records = conn.fetch_many(
                model=EventDetails, column="id_event", items=event_id_set
            )

            # In case where there are no records in the database it returns a type error and we add all the records in the API fetch
            try:
                exist_id_events_set = {i.id_event for i in fetched_records}
                records_to_add_set = event_id_set - exist_id_events_set
            except TypeError:
                records_to_add_set = event_id_set

            records_to_add = [
                i for i in data["features"] if i["id"] in records_to_add_set
            ]

            if len(records_to_add) > 0:
                records_to_add_list = []
                for i in tqdm(records_to_add):
                    id_event = i["id"]
                    properties = i["properties"]
                    coordinates = i["geometry"]["coordinates"]

                    timestamp_utc = convert_timestamp_to_utc(properties.get("time"))
                    time_stamp_date = timestamp_utc.date().strftime("%Y-%m-%d")

                    quake_entry = EventDetails(
                        id_event=id_event,
                        mag=properties.get("mag"),
                        ts_event_utc=timestamp_utc.strftime("%Y-%m-%d %H:%M:%S"),
                        ts_updated_utc=self.TIMESTAMP_NOW,
                        tz=properties.get("tz"),
                        felt=properties.get("felt"),
                        detail=properties.get("detail"),
                        cdi=properties.get("cdi"),
                        mmi=properties.get("mmi"),
                        status=properties.get("status"),
                        tsunami=properties.get("tsunami"),
                        type=properties.get("type"),
                        title=properties.get("title"),
                        date=time_stamp_date,
                        place=properties.get("place"),
                        longitude=coordinates[0],
                        latitude=coordinates[1],
                    )

                    records_to_add_list.append(quake_entry)

                    # Increments the count by one for each date added to the database. If no record exists, initialize the date at 1
                    summary[time_stamp_date] = summary.get(time_stamp_date, 0) + 1

                conn.insert_many(records_to_add_list)
                _logger.info(
                    f"Added {len(records_to_add)} records and {len(exist_id_events_set)} records were already added."
                )

            else:
                _logger.info("No new records found")

        except Exception as e:
            _logger.error(f" Encountereed an unexpected error: {e}")

    def backfill(self, conn: Session, start_date: str, end_date: str) -> None:
        """
        Performs a backfill operation for earthquake data between specified start and end dates.
        It generates URLs for each day within the date range and calls `extract_data_properties`
        to process and store data for each day.

        This is useful for populating the database with historical earthquake data for analysis

        Example:
        run = Earthquake()
        run.backfill(conn=conn,start_date="2023-01-01", end_date="2023-10-01")

        :param start_date: The start date for the backfill operation, in 'YYYY-MM-DD' format.
        :param end_date: The end date for the backfill operation, in 'YYYY-MM-DD' format.
        """

        date_range = generate_date_range(start_date, end_date)
        _logger.info(
            f"Backfill process started for the range {start_date} to {end_date}. Running in module {__name__}."
        )
        for year, month in date_range:
            for start in [1, 16]:
                end = start + 15
                url = generate_time_range_url(
                    year=f"{year:02}",
                    month=f"{month:02}",
                    start=f"{start:02}",
                    end=f"{end:02}",
                )
                _logger.info(
                    f"Running a backfill for Year: {year} Month: {month}, between {start} and {end} "
                )
                self.extract_data_properties(url=url, conn=conn)

        _logger.info(
            f"Completed the Backfill for {len(date_range)} months!!! Horray :)"
        )


def process_earthquake_data(
    conn: Session, tweet: TweetOperator, threshold: str
) -> None:
    most_recent_date = (
        conn.session.query(EventDetails.ts_updated_utc)
        .order_by(desc(EventDetails.ts_updated_utc))
        .first()
    )

    most_recent_date = most_recent_date[0].strftime("%Y-%m-%d %H:%M:%S")
    _logger.info(f"Most recent upload timestamp is {most_recent_date}")
    most_recent_date_quakes = conn.fetch_single(
        model=EventDetails, column="ts_updated_utc", item=most_recent_date
    )
    eligible_quakes = [
        i for i in most_recent_date_quakes if i.mag is not None and i.mag > threshold
    ]

    if len(eligible_quakes) > 0:
        for i in eligible_quakes:
            duration = TIMESTAMP_NOW - i.ts_event_utc
            if i.mag >= threshold and duration.seconds < REPORTED_SINCE_THRESHOLD:
                TWEET_CONCLUSION_TEXT = TWEET_CONCLUSION[
                    random.randint(0, len(TWEET_CONCLUSION) - 1)
                ]
                earthquake_ts_event = i.ts_event_utc.strftime("%H:%M:%S")

                text = f"Recent #Earthquake: {i.title} reported at {earthquake_ts_event} UTC ({duration.seconds/60:.0f} minutes ago). #EarthquakeAlert. \nSee more details at {EVENT_DETAIL_URL.format(id=i.id_event)}. \n {TWEET_CONCLUSION_TEXT}"
                item = {
                    "post": text,
                    "ts_upload_utc": TIMESTAMP_NOW.strftime("%Y-%m-%d %H:%M:%S"),
                    "id_event": i.id_event,
                }

                record_exist = conn.fetch_single(
                    model=Post, column="id_event", item=i.id_event
                )

                record_count = sum([1 for _ in record_exist])

                if record_count < 1:
                    conn.insert(Post(**item))
                    _logger.info(text)
                    try:
                        tweet.post_tweet(tweet=text)
                        _logger.info(
                            "Recorded recent tweet posted in the database  recent into the Database "
                        )
                    except Exception as e:
                        _logger.error(f"Encountered an unexpected error: {e}")
                else:
                    _logger.info("Tweet already posted")

    else:
        _logger.info(
            f"No recent earthquakes with a magnitude of {threshold} or higher were found. Nothing was posted to the database."
        )


def get_date_range_summary(
    conn: Session, model: Type[Base], start_date: str, end_date: str
) -> List[Base]:
    """
    Retrieves all records from a specified database model within a given date range.

    :param conn: An instance of a database connection, used to interact with the database.
    :param model: The SQLAlchemy model class representing the database table to query.
    :param start_date: The start date of the period for which the data is to be retrieved.
    :param end_date: The end date of the period for which the data is to be retrieved.
    :return: a list of all items meeting the queries criteria.
    """
    query = conn.session.query(model).filter(
        and_(
            model.ts_event_utc.between(start_date, end_date),
            model.mag > 0,
            model.type == "earthquake",
        )
    )

    return query.all()
