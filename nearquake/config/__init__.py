from dataclasses import dataclass
from dotenv import load_dotenv
import os
from datetime import datetime
import logging


_logger = logging.getLogger(__name__)

load_dotenv()

TIMESTAMP_NOW = datetime.utcnow().strftime("%Y%m%d")

API_BASE_URL: str = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_{time_period}.geojson"

EARTHQUAKE_URL_TEMPLATE: str = "https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?starttime={year}-{month}-01%2000:00:00&endtime={year}-{month}-31%2023:59:59"


def generate_time_range_url(year: int, month: int) -> str:
    """
    Generate the URL for extracting earthquakes that occurred during a specific year and month.

    Example usage: generate_time_range_url('2018','01', '12')

    :param year: Year
    :param month: Month
    :param day: Day
    :return: The URL path for the earthquakes that happened during the specified month and year.
    """
    return EARTHQUAKE_URL_TEMPLATE.format(year=year, month=month)


def generate_time_period_url(time_period: int) -> str:
    """
    Generate the URL for extracting earthquakes that occurred during a specific time.

    :param time: The time period for the query. Options are 'day', 'week', 'month'.
    :return: The URL path for the earthquakes that happened during the specified month and year.
    """

    valid_periods = {"day", "week", "month"}
    if time_period not in valid_periods:
        raise ValueError(
            f"Invalid time period: {time_period}. Valid options are: {valid_periods}",
            time_period,
            valid_periods,
        )
    _logger.info(
        f"Generated the url to upload earthquake events for the last {time_period}"
    )

    return API_BASE_URL.format(time_period=time_period)


@dataclass
class ConnectionConfig:
    user = os.environ.get("NEARQUAKE_USERNAME")
    host = os.environ.get("NEARQUAKE_HOST")
    dbname = os.environ.get("NEARQUAKE_DATABASE")
    port = os.environ.get("NEARQUAKE_PORT")
    password = os.environ.get("NEARQUAKE_PASSWORD")
    sqlengine = os.environ.get("NEARQUAKE_ENGINE")

    def generate_connection_url(self):
        if self.sqlengine is None:
            raise ValueError("SQL Engine is not specifed")
        _logger.info(
            f"Successcully generated the credentials and URL to connect to the {self.dbname} on {self.sqlengine} "
        )
        return f"{self.sqlengine}://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
