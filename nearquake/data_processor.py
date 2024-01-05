import logging
from datetime import datetime
from sqlalchemy import desc

from nearquake.config import (
    generate_time_range_url,
    ConnectionConfig,
    QuakeFeatures,
    TIMESTAMP_NOW,
    EVENT_DETAIL_URL,
)
from nearquake.tweet_processor import TweetOperator
from nearquake.utils.db_sessions import DbSessionManager
from nearquake.app.db import EventDetails, Post
from tqdm import tqdm
from nearquake.utils import (
    fetch_json_data_from_url,
    convert_timestamp_to_utc,
    generate_date_range,
)


_logger = logging.getLogger(__name__)


class Earthquake:
    """
    The Earthquake class is designed to interact with the earthquake.usgs.gov API to
    retrieve and store earthquake data. It provides functionalities to extract earthquake
    event data and perform backfill operations for a specified date range.
    """

    def __init__(self) -> None:
        self.TIMESTAMP_NOW = TIMESTAMP_NOW.strftime("%Y-%m-%d %H:%M:%S")

    def extract_data_properties(self, url):
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

        conn = DbSessionManager(config=ConnectionConfig())

        added = 0
        skipped = 0
        summary = {}

        with conn:
            try:
                for i in tqdm(data["features"]):
                    id_event = i["id"]
                    properties = i["properties"]
                    coordinates = i["geometry"]["coordinates"]

                    timestamp_utc = convert_timestamp_to_utc(properties.get("time"))
                    time_stamp_date = timestamp_utc.date().strftime("%Y-%m-%d")

                    quake_entry = QuakeFeatures(
                        id_event=id_event,
                        mag=properties.get("mag"),
                        ts_event_utc=timestamp_utc.strftime("%Y-%m-%d %H:%M:%S"),
                        ts_updated_utc=self.TIMESTAMP_NOW,
                        tz=properties.get("tz"),
                        felt=properties.get("felt"),
                        detail=properties.get("felt"),
                        cdi=properties.get("felt"),
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

                    fetched_records = conn.fetch(
                        model=EventDetails, column="id_event", item=id_event
                    )

                    if time_stamp_date in summary:
                        summary[time_stamp_date] += 1
                    else:
                        summary[time_stamp_date] = 1

                    if len(fetched_records) == 0:
                        property_items = EventDetails(**quake_entry.__dict__)
                        conn.insert(property_items)
                        added += 1
                    else:
                        skipped += 1

                log_message = (
                    f"Upload Complete for {time_stamp_date}. "
                    f"Added {added} records, and {skipped} records were already added. "
                    f"Summary of date added: {summary}"
                )
                _logger.info(log_message)

            except Exception as e:
                _logger.error(f" Encountereed an unexpected error: {e}")

    def backfill_data_properties(self, start_date: str, end_date: str):
        """
         Performs a backfill operation for earthquake data between specified start and end dates.
        It generates URLs for each day within the date range and calls `extract_data_properties`
        to process and store data for each day.

        This is useful for populating the database with historical earthquake data for analysis

        Example:
        run = Earthquake()
        run.backfill_data_properties(start_date="2023-01-01", end_date="2023-10-01")

        :param start_date: The start date for the backfill operation, in 'YYYY-MM-DD' format.
        :param end_date: The end date for the backfill operation, in 'YYYY-MM-DD' format.
        """

        date_range = generate_date_range(start_date, end_date)
        for year, month in date_range:
            url = generate_time_range_url(
                year=str(year).zfill(2), month=str(month).zfill(2)
            )
            self.extract_data_properties(url)

        _logger.info(
            f"Completed the Backfill for {len(date_range)} months!!! Horray :)"
        )


def process_earthquake_data(conn, tweet: TweetOperator, threshold: str):
    most_recent_date = (
        conn.session.query(EventDetails.ts_updated_utc)
        .order_by(desc(EventDetails.ts_updated_utc))
        .first()
    )

    most_recent_date = most_recent_date[0].strftime("%Y-%m-%d %H:%M:%S")
    _logger.info(f"Most recent upload timestamp is {most_recent_date}")
    most_recent_date_quakes = conn.fetch(
        model=EventDetails, column="ts_updated_utc", item=most_recent_date
    )
    eligible_quakes = [i for i in most_recent_date_quakes if i.mag > 5]

    if len(eligible_quakes) > 0:
        for i in eligible_quakes:
            if i.mag >= threshold:
                duration = TIMESTAMP_NOW - i.ts_event_utc

                text = f"Recent #Earthquake: {i.title} reported {duration.seconds/60:.0f} minutes ago, felt by {i.felt} people. \nSee more details at {EVENT_DETAIL_URL.format(id=i.id_event)}. \nData provided by https://www.usgs.gov/"
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

    else:
        _logger.info(
            f"No recent earthquakes with a magnitude of {threshold} or higher were found. Nothing was posted to the database."
        )
