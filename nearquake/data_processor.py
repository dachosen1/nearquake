import logging
from datetime import datetime

from nearquake.config import generate_time_range_url, ConnectionConfig
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
    def extract_data_properties(self, url):
        """_summary_

        :param url: _description_
        """
        data = fetch_json_data_from_url(url=url)

        conn = DbSessionManager(config=ConnectionConfig())
        timestamp_now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        added = 0
        skipped = 0

        with conn:
            try:
                for i in data["features"]:
                    id_event = i["id"]
                    properties = i["properties"]
                    coordinates = i["geometry"]["coordinates"]

                    timestamp_utc = convert_timestamp_to_utc(properties.get("updated"))
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
                    f"Upload Complete for {time_stamp_date}. Added {added} records, and {skipped} records were already in the database"
                )

            except Exception as e:
                _logger.error(f"Encountereed an unexpected error: {e}")

    def backfill_data_properties(self, start_date: str, end_date: str):
        """_summary_

        :param start_date: _description_
        :param end_date: _description_
        """

        date_range = generate_date_range(start_date, end_date)
        for year, month in date_range:
            for day in range(1, 32):
                url = generate_time_range_url(
                    year=str(year).zfill(2),
                    month=str(month).zfill(2),
                    day=str(day).zfill(2),
                )
                self.extract_data_properties(url)

        _logger.info(f"Completed the Backfill.. Horray :) ")


if __name__ == "__main__":
    test = Earthquake()
    test.backfill_data_properties(start_date="2023-01-01", end_date="2023-09-01")
