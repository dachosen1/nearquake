import logging
import random
from typing import List, Type, TypeVar
from abc import ABC, abstractmethod
from datetime import datetime
from collections import Counter


from sqlalchemy import desc, and_
from sqlalchemy.orm import Session

from nearquake.config import (
    generate_time_range_url,
    TIMESTAMP_NOW,
    EVENT_DETAIL_URL,
    TWEET_CONCLUSION,
    REPORTED_SINCE_THRESHOLD,
    generate_coordinate_lookup_detail_url,
)
from nearquake.tweet_processor import TweetOperator
from nearquake.app.db import EventDetails, Post, Base, LocationDetails
from tqdm import tqdm
from nearquake.utils import (
    fetch_json_data_from_url,
    convert_timestamp_to_utc,
    generate_date_range,
)


_logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseDataUploader(ABC):
    def __init__(self, conn: Session):
        self.conn = conn
        self.TIMESTAMP_NOW = TIMESTAMP_NOW.strftime("%Y-%m-%d %H:%M:%S")

    @abstractmethod
    def _extract(self):
        pass

    @abstractmethod
    def upload(self):
        pass


class UploadEarthQuakeEvents(BaseDataUploader):
    """
    Designed to interact with the earthquake.usgs.gov API to retrieve and store earthquake data. It provides functionalities to extract earthquake
    event data and perform backfill operations for a specified date range.
    """

    def _extract(self, url) -> List:
        """
        Extracts earthquake data from earthquake.usgs.gov, and returns a list of events that are not in the current database

        Note: this function only works for earthquake.usgs.gov urls , since it's expect the JSON api repsonse to follow a specific format.

        :param url: earthquake.usgs.gov api url
        :return: a list of earthquake events
        """

        data = fetch_json_data_from_url(url=url)
        try:
            event_ids_from_api = {i["id"] for i in data["features"]}
            existing_event_records = self.conn.fetch_many(
                model=EventDetails, column="id_event", items=event_ids_from_api
            )
            self.existing_event_ids = [
                record.id_event for record in existing_event_records
            ]

            new_events = [
                i for i in data["features"] if i["id"] not in self.existing_event_ids
            ]
        except TypeError:
            new_events = data["features"]
        except Exception as e:
            _logger.error(f"Encountered an unexpected error: {e}")
        return new_events

    def _fetch_event_details(self, event) -> EventDetails:
        id_event = event["id"]
        properties = event["properties"]
        coordinates = event["geometry"]["coordinates"]
        timestamp_utc = convert_timestamp_to_utc(properties.get("time"))
        time_stamp_date = timestamp_utc.date().strftime("%Y-%m-%d")

        return EventDetails(
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

    def upload(self, url: str) -> None:
        """_summary_

        :param url: earthquake.usgs.gov api url
        """
        new_event = self._extract(url=url)

        if len(new_event) > 0:
            new_event_list = [
                self._fetch_event_details(event=event) for event in new_event
            ]

            self.conn.insert_many(new_event_list)
            summary = Counter(
                event.date.strftime("%Y-%m-%d") for event in new_event_list
            )
            _logger.info(
                f"Added {len(new_event_list)} records and {len(self.existing_event_ids)} records were already added. {dict(summary)}"
            )
        else:
            _logger.info("No new records found")

    def backfill(self, start_date: str, end_date: str) -> None:
        """
        Performs a backfill operation for earthquake data between specified start and end dates.

        :param start_date: The start date for the backfill operation, in 'YYYY-MM-DD' format.
        :param end_date: The end date for the backfill operation, in 'YYYY-MM-DD' format.
        """
        try:
            datetime.strptime(start_date, "%Y-%m-%d").date()
            datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")

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
                self.upload(url=url)

        _logger.info(
            f"Completed the Backfill for {len(date_range)} months!!! Horray :)"
        )


class UploadEarthQuakeLocation(BaseDataUploader):
    def _extract(self, date) -> list:

        query = (
            self.conn.session.query(
                EventDetails.id_event, EventDetails.latitude, EventDetails.longitude
            )
            .join(
                LocationDetails,
                LocationDetails.id_event == EventDetails.id_event,
                isouter=True,
            )
            .filter(LocationDetails.id_event == None, EventDetails.date == date)
        )
        results = query.all()
        return results

    def _fetch_location_detail(self, event) -> LocationDetails:
        id_event, long, lat = event
        url = generate_coordinate_lookup_detail_url(lat=lat, long=long)
        content = fetch_json_data_from_url(url=url)

        if content.get("error") != "Unable to geocode":
            return LocationDetails(
                id_event=id_event,
                id_place=content.get("place_id"),
                category=content.get("category"),
                place_rank=content.get("place_rank"),
                address_type=content.get("addresstype"),
                place_importance=content.get("importance"),
                name=content.get("name"),
                display_name=content.get("display_name"),
                country=content["address"].get("country"),
                state=content["address"].get("state"),
                region=content["address"].get("region"),
                country_code=content["address"].get("country_code").upper(),
                boundingbox=content.get("boundingbox"),
            )
        else:
            return LocationDetails(id_event=id_event)

    def upload(self, date):
        new_events = self._extract(date=date)
        location_details = [
            self._fetch_location_detail(event=event) for event in new_events
        ]
        conn.insert_many(model=location_details)
        return None


class TweetEarthquakeEvents(BaseDataUploader):
    pass


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
    conn: Session, model: Type[ModelType], start_date: str, end_date: str
) -> List[ModelType]:
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


def extract_coordinate_details():
    pass


if __name__ == "__main__":

    from nearquake.config import ConnectionConfig
    from nearquake.utils.db_sessions import DbSessionManager

    conn = DbSessionManager(config=ConnectionConfig())
    run = UploadEarthQuakeLocation(conn=conn)

    with conn:
        run._extract(date="2023-12-01")
