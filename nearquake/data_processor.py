from abc import ABC, abstractmethod
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import List, Type, TypeVar

from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from tqdm import tqdm

from nearquake.app.db import Base, EventDetails, LocationDetails, Post
from nearquake.config import (
    EARTHQUAKE_POST_THRESHOLD,
    REPORTED_SINCE_THRESHOLD,
    TIMESTAMP_NOW,
    _nearquake_secrets,
    generate_coordinate_lookup_detail_url,
    generate_event_detail_url,
    generate_time_range_url,
)
from nearquake.post_manager import post_and_save_tweet
from nearquake.utils import (
    backfill_valid_date_range,
    convert_timestamp_to_utc,
    extract_url_content,
    fetch_json_data_from_url,
    format_earthquake_alert,
    get_earthquake_image_url,
    timer,
)
from nearquake.utils.logging_utils import (
    get_logger,
    log_api_request,
    log_api_response,
    log_db_operation,
    log_error,
    log_info,
)

_logger = get_logger(__name__)

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

    def _extract(self, url: str) -> List[dict]:
        """
        Extracts earthquake data from earthquake.usgs.gov, and returns a list of events that are not in the current database

        Note: this function only works for earthquake.usgs.gov urls , since it's expect the JSON api repsonse to follow a specific format.

        :param url: earthquake.usgs.gov api url
        :return: a list of earthquake events
        """
        log_api_request(
            _logger,
            api_name="USGS Earthquake API",
            endpoint=url,
        )

        data = fetch_json_data_from_url(url=url)
        try:
            event_ids_from_api = {i["id"] for i in data["features"]}

            log_db_operation(
                _logger,
                operation="SELECT",
                table="earthquake.fct__event_details",
                details=f"Fetching existing events from {len(event_ids_from_api)} potential new events",
            )

            existing_event_records = self.conn.fetch_many(
                model=EventDetails, column="id_event", items=event_ids_from_api
            )
            existing_event_ids = [record.id_event for record in existing_event_records]

            new_events = [
                i for i in data["features"] if i["id"] not in existing_event_ids
            ]
            self.existing_event_ids_count = len(existing_event_ids)

            log_api_response(
                _logger,
                api_name="USGS Earthquake API",
                endpoint=url,
                status_code=200,
                response_summary=f"Found {len(new_events)} new events out of {len(data['features'])} total events",
            )

        except TypeError:
            new_events = data["features"]
            self.existing_event_ids_count = 0
            log_api_response(
                _logger,
                api_name="USGS Earthquake API",
                endpoint=url,
                status_code=200,
                response_summary=f"Processing all {len(new_events)} events as new (no existing events found)",
            )

        except Exception as e:
            new_events = data["features"]
            self.existing_event_ids_count = 0
            log_error(
                _logger,
                "Encountered an unexpected error during earthquake data extraction",
                exc=e,
            )
        return new_events

    def _fetch_event_details(self, event: dict) -> EventDetails:
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

            log_db_operation(
                _logger,
                operation="INSERT",
                table="earthquake.fct__event_details",
                details=f"Inserting {len(new_event_list)} new earthquake events",
            )

            self.conn.insert_many(new_event_list)
            summary = Counter(str(event.date) for event in new_event_list)
            log_info(
                _logger,
                f"Added {len(new_event_list)} records and {self.existing_event_ids_count} records were already added. {dict(summary)}",
            )
        else:
            log_info(_logger, "No new records found")

    @timer
    def backfill(self, start_date: str, end_date: str, interval: int = 15) -> None:
        """
        Performs a backfill operation for earthquake data between specified start and end dates.

        :param start_date: The start date for the backfill operation, in 'YYYY-MM-DD' format.
        :param end_date: The end date for the backfill operation, in 'YYYY-MM-DD' format.
        :param interval: The number of days to increment each start date within the range. defaults to 15 days
        """

        date_range = backfill_valid_date_range(start_date, end_date, interval=interval)

        for start, end in date_range:
            start_str = start.strftime("%Y-%m-%d")
            end_str = end.strftime("%Y-%m-%d")

            url = generate_time_range_url(
                start=start_str,
                end=end_str,
            )
            log_info(
                _logger,
                f"Running a backfill for earthquakes between {start_str} and {end_str}",
            )
            self.upload(url=url)

        log_info(
            _logger, f"Completed the Backfill for {len(date_range)} months!!! Horray :)"
        )


class UploadEarthQuakeLocation(BaseDataUploader):
    def _extract(self, date: str) -> list:
        log_db_operation(
            _logger,
            operation="SELECT",
            table="earthquake.fct__event_details",
            details=f"Extracting events on {date} without location details",
        )

        query = (
            self.conn.session.query(
                EventDetails.id_event, EventDetails.latitude, EventDetails.longitude
            )
            .join(
                LocationDetails,
                LocationDetails.id_event == EventDetails.id_event,
                isouter=True,
            )
            .filter(LocationDetails.id_event.is_(None), EventDetails.date == date)
        )
        results = query.all()
        log_info(_logger, f"Extracted {len(results)} quake events on {date}")
        return results

    def _extract_between(self, start_date, end_date) -> list:
        log_db_operation(
            _logger,
            operation="SELECT",
            table="earthquake.fct__event_details",
            details=f"Extracting events between {start_date} and {end_date} without location details",
        )

        query = (
            self.conn.session.query(
                EventDetails.id_event, EventDetails.latitude, EventDetails.longitude
            )
            .join(
                LocationDetails,
                LocationDetails.id_event == EventDetails.id_event,
                isouter=True,
            )
            .filter(
                LocationDetails.id_event.is_(None),
                EventDetails.date.between(start_date, end_date),
            )
        )
        results = query.all()
        log_info(
            _logger,
            f"Successfully extracted {len(results)} earthquake events from {start_date} to {end_date}.",
        )
        return results

    def _fetch_location_detail(self, event: str) -> LocationDetails:
        id_event, latitude, longitude = event
        url = generate_coordinate_lookup_detail_url(
            latitude=latitude, longitude=longitude
        )

        # Pass API key as a separate parameter for secure logging
        params = {"key": _nearquake_secrets.get("GEO_API_KEY")}
        content = fetch_json_data_from_url(url=url, params=params)

        if content is None:
            log_info(
                _logger,
                f"Skipping event: {id_event}. The URL returned None type for {latitude} {longitude}",
            )
            return None

        if content.get("error") is not None:
            log_error(_logger, "Unable to get geocode due to an error.")

        try:
            location = LocationDetails(
                id_event=id_event,
                continent=content.get("continent"),
                continentCode=content.get("continentCode"),
                countryName=content.get("countryName"),
                countryCode=content.get("countryCode"),
                principalSubdivision=content.get("principalSubdivision"),
                principalSubdivisionCode=content.get("principalSubdivisionCode"),
                city=content.get("city"),
            )

            return location

        except Exception as e:
            log_error(
                _logger,
                "Encountered an error while attempting to extract location details",
                exc=e,
            )
        return None

    @timer
    def upload(self, start_date, end_date=None, interval: int = 15) -> None:
        date_range = backfill_valid_date_range(start_date, end_date, interval=interval)

        for start, end in date_range:
            start_date = start.strftime("%Y-%m-%d")
            end_date = end.strftime("%Y-%m-%d")

            new_events = self._extract_between(start_date=start_date, end_date=end_date)
            extraction_period = f"from {start_date} to {end_date}"

            if new_events:
                log_info(
                    _logger,
                    f"Fetching location details for {len(new_events)} events {extraction_period}",
                )

                location_details = [
                    self._fetch_location_detail(event=event) for event in new_events
                ]

                log_info(
                    _logger,
                    f"Done Fetching location details for {len(new_events)} events {extraction_period}",
                )

                # Filter out None values
                location_details = [loc for loc in location_details if loc is not None]

                if location_details:
                    log_db_operation(
                        _logger,
                        operation="INSERT",
                        table="earthquake.dim__location_details",
                        details=f"Inserting {len(location_details)} location details",
                    )

                    self.conn.insert_many(location_details)
                    log_info(
                        _logger,
                        f"Added {len(location_details)} location details {extraction_period}",
                    )
                else:
                    log_info(
                        _logger, f"No valid location details to add {extraction_period}"
                    )
            else:
                log_info(_logger, f"No new location records to add {extraction_period}")
        return None

    @timer
    def backfill(
        self,
        start_date: str,
        end_date: str = None,
        interval: int = 15,
    ):
        log_info(
            _logger,
            f"Starting backfill for earthquake locations between {start_date} and {end_date}",
        )

        self.upload(start_date=start_date, end_date=end_date, interval=interval)

        log_info(
            _logger,
            f"Completed backfill for earthquake locations between {start_date} and {end_date}",
        )


class TweetEarthquakeEvents(BaseDataUploader):

    def _extract(self) -> List:
        threshold_time = TIMESTAMP_NOW - timedelta(seconds=REPORTED_SINCE_THRESHOLD)

        log_db_operation(
            _logger,
            operation="SELECT",
            table="earthquake.fct__event_details",
            details=f"Finding earthquakes with magnitude > {EARTHQUAKE_POST_THRESHOLD} since {threshold_time}",
        )

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
                func.now() - EventDetails.ts_event_utc
                < timedelta(seconds=REPORTED_SINCE_THRESHOLD),
                Post.id_event.is_(None),
            )
        )
        results = query.all()

        log_info(_logger, f"Found {len(results)} eligible earthquakes for tweeting")

        return results

    def upload(self):
        eligible_quakes = self._extract()
        if not eligible_quakes:
            log_info(
                _logger,
                f"No recent earthquakes with a magnitude of {EARTHQUAKE_POST_THRESHOLD} or higher were found.",
            )
            return None

        for quake in eligible_quakes:
            duration = TIMESTAMP_NOW - quake.ts_event_utc.replace(tzinfo=timezone.utc)
            earthquake_ts_event = quake.ts_event_utc.strftime("%H:%M:%S")

            log_info(
                _logger,
                f"Preparing tweet for earthquake {quake.id_event} (magnitude {quake.mag})",
            )

            # Get full event details for depth and place
            event_query = (
                self.conn.session.query(EventDetails)
                .filter(EventDetails.id_event == quake.id_event)
                .first()
            )

            tweet_text = format_earthquake_alert(
                id_event=quake.id_event,
                ts_event=earthquake_ts_event,
                duration=duration,
                message=quake.title,
                post_type="event",
                magnitude=quake.mag,
                felt=event_query.felt if event_query else None,
                tsunami=event_query.tsunami if event_query else None,
            )

            try:
                log_info(_logger, f"Posting tweet about earthquake {quake.id_event}")

                # Fetch earthquake shakemap image
                image_data = None
                try:
                    event_url = generate_event_detail_url(quake.id_event)
                    event_details = fetch_json_data_from_url(event_url)
                    if event_details:
                        image_url = get_earthquake_image_url(event_details)
                        if image_url:
                            image_data = extract_url_content(image_url)
                            log_info(
                                _logger,
                                f"Successfully fetched shakemap image for {quake.id_event}",
                            )
                except Exception as img_error:
                    log_error(
                        _logger,
                        f"Failed to fetch shakemap image for {quake.id_event}, posting without image",
                        exc=img_error,
                    )

                # Post initial tweet
                result = post_and_save_tweet(
                    tweet_text, self.conn, media_data=image_data
                )

                log_info(
                    _logger,
                    f"Successfully posted tweet about earthquake {quake.id_event}",
                )

                # For significant earthquakes (M5.5+), create a 2-tweet thread with context
                if quake.mag >= 5.5:
                    from nearquake.utils import generate_earthquake_context

                    twitter_tweet_id = result.get("twitter")
                    if twitter_tweet_id:
                        log_info(
                            _logger,
                            f"Creating thread for significant earthquake {quake.id_event} (M{quake.mag})",
                        )

                        try:
                            # Tweet 2: Historical context
                            location = (
                                event_query.place if event_query else "this region"
                            )
                            context_text = generate_earthquake_context(
                                magnitude=quake.mag,
                                location=location,
                                latitude=event_query.latitude if event_query else None,
                                longitude=(
                                    event_query.longitude if event_query else None
                                ),
                                conn=self.conn,
                            )

                            context_tweet = {
                                "post": f"📊 Context: {context_text}",
                                "ts_upload_utc": tweet_text["ts_upload_utc"],
                                "id_event": quake.id_event,
                                "post_type": "context",
                            }

                            post_and_save_tweet(
                                context_tweet,
                                self.conn,
                                in_reply_to_tweet_id=twitter_tweet_id,
                            )

                            log_info(
                                _logger,
                                f"Successfully created 2-tweet thread for {quake.id_event}",
                            )
                        except Exception as thread_error:
                            log_error(
                                _logger,
                                f"Failed to create thread for {quake.id_event}",
                                exc=thread_error,
                            )

            except Exception as e:
                log_error(
                    _logger,
                    f"Encountered an error while attempting to post tweet about earthquake {quake.id_event}",
                    exc=e,
                )

        return None


class TweetDailySummary(BaseDataUploader):
    """Post daily earthquake summary with professional graphics."""

    def _extract(self) -> List:
        """Not used for summary posting."""
        pass

    def upload(self, date: str = None) -> None:
        """
        Generate and post daily earthquake summary.

        :param date: Date in YYYY-MM-DD format (defaults to yesterday)
        """
        from nearquake.graphics_generator import generate_daily_summary_graphic

        if date is None:
            date = (TIMESTAMP_NOW - timedelta(days=1)).strftime("%Y-%m-%d")

        log_info(_logger, f"Generating daily summary for {date}")

        try:
            # Generate graphic
            log_info(
                _logger, f"Attempting to generate daily summary graphic for {date}"
            )
            image_data = generate_daily_summary_graphic(self.conn, date)

            if not image_data:
                log_info(_logger, f"No events to summarize for {date}")
                return

            log_info(
                _logger,
                f"Successfully generated graphic, size: {len(image_data)} bytes",
            )

            # Get event count for tweet text
            events = (
                self.conn.session.query(EventDetails)
                .filter(EventDetails.date == date, EventDetails.type == "earthquake")
                .all()
            )

            magnitudes = [e.mag for e in events if e.mag]
            max_mag = max(magnitudes) if magnitudes else 0
            max_event = max(events, key=lambda e: e.mag if e.mag else 0)
            location = max_event.place if max_event.place else "Unknown"
            event_time = (
                max_event.ts_event_utc.strftime("%H:%M")
                if max_event.ts_event_utc
                else "00:00"
            )

            # Create narrative tweet text
            tweet_text = f"""Over the last 24 hours there were {len(events)} earthquakes detected and the largest being M{max_mag:.1f} - {location} reported in at {event_time} UTC

#Earthquake #SeismicActivity
Data: earthquake.usgs.gov"""

            tweet_data = {
                "post": tweet_text,
                "ts_upload_utc": TIMESTAMP_NOW.strftime("%Y-%m-%d %H:%M:%S"),
                "id_event": None,
                "post_type": "daily_summary",
            }

            post_and_save_tweet(tweet_data, self.conn, media_data=image_data)
            log_info(_logger, f"Successfully posted daily summary for {date}")

        except Exception as e:
            log_error(_logger, f"Failed to post daily summary for {date}", exc=e)


class TweetWeeklySummary(BaseDataUploader):
    """Post weekly earthquake summary with professional graphics."""

    def _extract(self) -> List:
        """Not used for summary posting."""
        pass

    def upload(self, end_date: str = None) -> None:
        """
        Generate and post weekly earthquake summary.

        :param end_date: End date in YYYY-MM-DD format (defaults to yesterday)
        """
        from nearquake.graphics_generator import generate_weekly_summary_graphic

        if end_date is None:
            end_date = (TIMESTAMP_NOW - timedelta(days=1)).strftime("%Y-%m-%d")

        start_date = (
            datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=6)
        ).strftime("%Y-%m-%d")

        log_info(_logger, f"Generating weekly summary from {start_date} to {end_date}")

        try:
            # Generate graphic
            log_info(
                _logger,
                f"Attempting to generate weekly summary graphic for week ending {end_date}",
            )
            image_data = generate_weekly_summary_graphic(self.conn, end_date)

            if not image_data:
                log_info(_logger, f"No events to summarize for week ending {end_date}")
                return

            log_info(
                _logger,
                f"Successfully generated graphic, size: {len(image_data)} bytes",
            )

            # Get event count for tweet text
            events = (
                self.conn.session.query(EventDetails)
                .filter(
                    EventDetails.date >= start_date,
                    EventDetails.date <= end_date,
                    EventDetails.type == "earthquake",
                )
                .all()
            )

            magnitudes = [e.mag for e in events if e.mag]
            max_mag = max(magnitudes) if magnitudes else 0
            max_event = max(events, key=lambda e: e.mag if e.mag else 0)
            location = max_event.place if max_event.place else "Unknown"
            max_event_date = (
                max_event.date.strftime("%Y-%m-%d") if max_event.date else end_date
            )

            # Create narrative tweet text
            tweet_text = f"""Over the last 7 days there were {len(events)} earthquakes detected and the largest being M{max_mag:.1f} - {location} reported in on {max_event_date}

#Earthquake #WeeklyReport
Data: earthquake.usgs.gov"""

            tweet_data = {
                "post": tweet_text,
                "ts_upload_utc": TIMESTAMP_NOW.strftime("%Y-%m-%d %H:%M:%S"),
                "id_event": None,
                "post_type": "weekly_summary",
            }

            post_and_save_tweet(tweet_data, self.conn, media_data=image_data)
            log_info(
                _logger,
                f"Successfully posted weekly summary for week ending {end_date}",
            )

        except Exception as e:
            log_error(
                _logger,
                f"Failed to post weekly summary for week ending {end_date}",
                exc=e,
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
    log_db_operation(
        _logger,
        operation="SELECT",
        table=model.__tablename__,
        details=f"Getting summary for date range {start_date} to {end_date}",
    )

    query = conn.session.query(model).filter(
        and_(
            model.ts_event_utc.between(start_date, end_date),
            model.mag > 0,
            model.type == "earthquake",
        )
    )

    results = query.all()

    log_info(
        _logger,
        f"Retrieved {len(results)} records for date range {start_date} to {end_date}",
    )

    return results
