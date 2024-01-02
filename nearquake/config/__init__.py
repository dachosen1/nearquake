from dataclasses import dataclass, field
from dotenv import load_dotenv
import os
from datetime import datetime
import logging


_logger = logging.getLogger(__name__)

load_dotenv()

TIMESTAMP_NOW = datetime.utcnow().strftime("%Y%m%d")

API_BASE_URL: str = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_{time_period}.geojson"

EARTHQUAKE_URL_TEMPLATE: str = "https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?starttime={year}-{month}-01%2000:00:00&endtime={year}-{month}-31%2023:59:59"


@dataclass(kw_only=True)
class QuakeFeatures:
    id_event: str = field(default_factory=str)
    mag: float = field(default_factory=float)
    ts_event_utc: str = field(default_factory=str)
    ts_updated_utc: str = field(default_factory=str)
    tz: str = field(default_factory=str)
    felt: str = field(default_factory=str)
    detail: str = field(default_factory=str)
    cdi: str = field(default_factory=str)
    mmi: str = field(default_factory=str)
    status: str = field(default_factory=str)
    tsunami: str = field(default_factory=str)
    type: str = field(default_factory=str)
    title: str = field(default_factory=str)
    date: str = field(default_factory=str)
    place: str = field(default_factory=str)
    longitude: float = field(default_factory=float)
    latitude: float = field(default_factory=float)


def generate_time_range_url(year: int, month: int) -> str:
    """
    Generate the URL for extracting earthquakes that occurred during a specific year and month.

    Example usage: generate_time_range_url('2018','01', '12')

    :param year: Year
    :param month: Month

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


@dataclass()
class ConnectionConfig:
    user: str = field(default_factory=lambda: os.environ.get("NEARQUAKE_USERNAME"))
    host: str = field(default_factory=lambda: os.environ.get("NEARQUAKE_HOST"))
    dbname: str = field(default_factory=lambda: os.environ.get("NEARQUAKE_DATABASE"))
    port: str = field(default_factory=lambda: os.environ.get("NEARQUAKE_PORT"))
    password: str = field(default_factory=lambda: os.environ.get("NEARQUAKE_PASSWORD"))
    sqlengine: str = field(default_factory=lambda: os.environ.get("NEARQUAKE_ENGINE"))

    def __post_init__(self):
        missing = [
            attr
            for attr in ["user", "host", "dbname", "port", "password", "sqlengine"]
            if getattr(self, attr) is None
        ]
        if missing:
            error_message = (
                f"The following attributes are not specified: {', '.join(missing)}"
            )
            _logger.error(error_message)
            raise ValueError(error_message)

    def generate_connection_url(self) -> str:
        _logger.info(
            f"Successfully generated the URL to connect to the {self.dbname} database using the {self.sqlengine} engine."
        )
        return f"{self.sqlengine}://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
