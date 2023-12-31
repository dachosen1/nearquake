from dataclasses import dataclass, field
from dotenv import load_dotenv
import os

load_dotenv()


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
            f"Invalid time period: {time_period}. Valid options are: {valid_periods}"
        )

    return API_BASE_URL.format(time_period=time_period)


@dataclass(init=False)
class ConnectionConfig:
    user: str = os.environ.get("NEARQUAKE_USERNAME")
    host: str = os.environ.get("NEARQUAKE_HOST")
    dbname: str = os.environ.get("NEARQUAKE_DATABASE")
    port: str = os.environ.get("NEARQUAKE_PORT")
    password: str = os.environ.get("NEARQUAKE_PASSWORD")
    sqlengine: str = os.environ.get("NEARQUAKE_ENGINE")

    def __post_init__(self):
        """
        Ensure all required fields are provided
        """
        required_fields = ["user", "host", "dbname", "port", "password", "sqlengine"]
        missing_fields = [
            field for field in required_fields if getattr(self, field) is None
        ]

        if missing_fields:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_fields)}"
            )

    def generate_connection_url(self):
        if self.sqlengine is None:
            raise ValueError("SQL Engine is not specifed")
        return f"{self.sqlengine}://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
