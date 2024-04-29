import logging
from typing import List, Type, TypeVar
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from typing import List, Type, Tuple
from functools import lru_cache

from tqdm import tqdm
from sqlalchemy import and_, func
from sqlalchemy.orm import Session


from nearquake.config import (
    generate_time_range_url,
    TIMESTAMP_NOW,
    REPORTED_SINCE_THRESHOLD,
    EARTHQUAKE_POST_THRESHOLD,
    generate_coordinate_lookup_detail_url,
    POSTGRES_CONNECTION_URL
)
from nearquake.tweet_processor import TweetOperator
from nearquake.app.db import EventDetails, Post, Base, LocationDetails
from nearquake.tweet_processor import TweetOperator
from nearquake.app.db import EventDetails, Post
from nearquake.utils.db_sessions import DbSessionManager
from nearquake.utils import (
    fetch_json_data_from_url,
    convert_timestamp_to_utc,
    generate_date_range,
    format_earthquake_alert,
    timer,
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
            _logger.error(f"Encountered an unexpected error: {e} {event_ids_from_api}")
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

    @timer
    def upload(self, url: str) -> None:
        """_summary_

        :param url: earthquake.usgs.gov api url
        """
        new_event = self._extract(url=url)

        if len(new_event) > 0:
            new_event_list = [
                self._fetch_event_details(event=event) for event in tqdm(new_event)
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

    @timer
    def backfill(self, start_date: str, end_date: str, interval: int = 15) -> None:
        """
        Performs a backfill operation for earthquake data between specified start and end dates.

        :param start_date: The start date for the backfill operation, in 'YYYY-MM-DD' format.
        :param end_date: The end date for the backfill operation, in 'YYYY-MM-DD' format.
        :param interval: The number of days to increment each start date within the range. defaults to 15 days
        """
        try:
            datetime.strptime(start_date, "%Y-%m-%d").date()
            datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")

        date_range = generate_date_range(start_date, end_date, interval=interval)
        _logger.info(
            f"Backfill process started for the range {start_date} to {end_date}. Running in module {__name__}."
        )
        for start, end in date_range:
            start = start.strftime("%Y-%m-%d")
            end = end.strftime("%Y-%m-%d")

            url = generate_time_range_url(
                start=start,
                end=end,
            )
            _logger.info(
                f"Running a backfill for earthquakes between {start} and {end}"
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
        id_event, latitude, longitude = event
        url = generate_coordinate_lookup_detail_url(
            latitude=latitude, longitude=longitude
        )
        content = fetch_json_data_from_url(url=url)

        if content is None:
            _logger.info(f"Skipping {event}. The url returned none type. url: {url}")
            return None

        if content.get("error") is not None:
            _logger.error(
                f"unable to get geocode for {event} content: {content} due to {content.get('error')} error "
            )

        try:
            return LocationDetails(
                id_event=id_event,
                continent=content.get("continent"),
                continentCode=content.get("continentCode"),
                countryName=content.get("countryName"),
                countryCode=content.get("countryCode"),
                principalSubdivision=content.get("principalSubdivision"),
                principalSubdivisionCode=content.get("principalSubdivisionCode"),
                city=content.get("city"),
            )

        except Exception as e:
            _logger.error(
                f"Encountered an error while attempting to extract long, and lattiude {e} content: {content} event {event}  url: {url}"
            )
        return None

    def _parallelize_fetch_location_details(self, event):
        with ThreadPoolExecutor() as executor:
            location_details = list(executor.map(self._fetch_location_detail, event))
        return location_details

    @timer
    def upload(self, date, parralel: bool = False):
        new_events = self._extract(date=date)
        if new_events:
            if parralel:
                location_details = self._parallelize_fetch_location_details(
                    event=new_events
                )

            else:
                location_details = [
                    self._fetch_location_detail(event=event) for event in new_events
                ]
                _logger.info(f"Completed the extractions of url content for {date} ")

            self.conn.insert_many(location_details)
            _logger.info(f"Added {len(location_details)} location detail for {date}")
        else:
            _logger.info(f"No new location records to add for {date}")
        return None

    @timer
    def backfill(self, start_date: str, end_date: str, interval: int = 1):
        date_range = generate_date_range(
            start_date=start_date, end_date=end_date, interval=interval
        )
        _logger.info(
            f"Backfill for earthquake locations between {start_date} and {end_date}"
        )
        for start, _ in date_range:
            _logger.info(f"Starting backfill for earthquake locations on {start}")
            self.upload(date=start, parralel=True)
            _logger.info(f"Complete backfill for earthquake locations on {start}")


class TweetEarthquakeEvents(BaseDataUploader, TweetOperator):

    def _extract(self) -> List:
        query = (
            self.conn.session.query(
                EventDetails.id_event,
                EventDetails.title,
                EventDetails.ts_event_utc,
                EventDetails.mag,
            )
            .join(
                Post,
                Post.id_event == EventDetails.id_event,
                isouter=True,
            )
            .filter(
                EventDetails.mag > EARTHQUAKE_POST_THRESHOLD,
                TIMESTAMP_NOW - func.timezone("UTC", EventDetails.ts_event_utc)
                < timedelta(seconds=REPORTED_SINCE_THRESHOLD),
                Post.id_event == None,
            )
        )
        return query.all()

    def upload(self):

        eligible_quakes = self._extract()
        if not eligible_quakes:
            _logger.info(
                f"No recent earthquakes with a magnitude of {EARTHQUAKE_POST_THRESHOLD} or higher were found. Nothing was posted to twiter"
            )
            return None

        for quake in eligible_quakes:

            duration = TIMESTAMP_NOW - quake.ts_event_utc.replace(tzinfo=timezone.utc)
            earthquake_ts_event = quake.ts_event_utc.strftime("%H:%M:%S")

            item = format_earthquake_alert(
                id_event=quake.id_event,
                ts_event=earthquake_ts_event,
                duration=duration,
                message=quake.title,
                post_type="event",
            )

            try:
                self.post_tweet(item=item, conn=self.conn)
                _logger.info(
                    "Recorded recent tweet posted in the database recent into the Database "
                )

            except Exception as e:
                _logger.error(
                    f"Encountered an error while attempting to post {item}. {e} "
                )

        return None


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


@lru_cache(maxsize=1)
def get_daily_earth_quakes() -> Tuple[List[str], List[int], List[float]]:

    conn = DbSessionManager(url=POSTGRES_CONNECTION_URL)

    with conn:
        query = (
            conn.session.query(
                EventDetails.date, EventDetails.mag, func.count(EventDetails.id_event)
            )
            .filter(EventDetails.date > "2010-01-01")
            .group_by(EventDetails.date, EventDetails.mag)
        )

        results = query.all()

        all_date, all_count, all_mag = [], [], []

        try:
            for date, count, mag in results:
                all_date.append(date.strftime("%Y-%m-%d"))
                all_count.append(count)
                all_mag.append(mag)
        except Exception as e:
            _logger.error(
                f"Unexpected error occured after trying to add to results. {e}, {date}, {count} {mag}"
            )

        return all_date, all_count, all_mag
