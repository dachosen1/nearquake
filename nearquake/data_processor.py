import logging
from datetime import datetime

from nearquake.config import (
    generate_time_range_url,
    generate_time_period_url,
    ConnectionConfig,
)
from nearquake.utils.db_sessions import DbSessionManager
from nearquake.app.db import EventDetails
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
        timestamp_now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        added = 0
        skipped = 0

        with conn:
            try:
                for i in tqdm(data["features"]):
                    id_event = i["id"]
                    properties = i["properties"]
                    coordinates = i["geometry"]["coordinates"]

                    timestamp_utc = convert_timestamp_to_utc(properties.get("time"))
                    time_stamp_date = timestamp_utc.date().strftime("%Y-%m-%d")

                    earthquake_properties = {
                        "id_event": id_event,
                        "mag": properties.get("mag"),
                        "ts_event_utc": timestamp_utc.strftime("%Y-%m-%d %H:%M:%S"),
                        "ts_updated_utc": timestamp_now,
                        "tz": properties.get("tz"),
                        "felt": properties.get("felt"),
                        "detail": properties.get("detail"),
                        "cdi": properties.get("cdi"),
                        "mmi": properties.get("mmi"),
                        "status": properties.get("status"),
                        "tsunami": properties.get("tsunami"),
                        "type": properties.get("type"),
                        "title": properties.get("title"),
                        "date": time_stamp_date,
                        "place": properties.get("place"),
                        "longitude": coordinates[0],
                        "latitude": coordinates[1],
                    }

                    fetched_records = conn.fetch(
                        model=EventDetails, column="id_event", item=id_event
                    )

                    if len(fetched_records) == 0:
                        property_items = EventDetails(**earthquake_properties)
                        conn.insert(property_items)
                        added += 1
                    else:
                        skipped += 1
                _logger.info(
                    f" Upload Complete for {time_stamp_date}. Added {added} records, and {skipped} records were already in the database"
                )

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

        _logger.info(f"Completed the Backfill.. Horray :) ")


if __name__ == "__main__":
    test = Earthquake()
    # test.backfill_data_properties(start_date="2023-12-01", end_date="2023-12-31")
    test.extract_data_properties(generate_time_period_url("day"))
