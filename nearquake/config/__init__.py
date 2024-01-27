from dataclasses import dataclass, field
from dotenv import load_dotenv
import os
from datetime import datetime
import logging
from random import randint


_logger = logging.getLogger(__name__)

load_dotenv()

TIMESTAMP_NOW = datetime.utcnow()

API_BASE_URL: str = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_{time_period}.geojson"
)

EARTHQUAKE_URL_TEMPLATE: str = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?starttime={year}-{month}-{start}%2000:00:00&endtime={year}-{month}-{end}%2023:59:59"
)

EVENT_DETAIL_URL: str = (
    "https://earthquake.usgs.gov/earthquakes/eventpage/{id}/executive"
)


EARTHQUAKE_POST_THRESHOLD = 4.5

REPORTED_SINCE_THRESHOLD = 3600


def generate_time_range_url(year: int, month: int, start: int, end: int) -> str:
    """
    Generate the URL for extracting earthquakes that occurred during a specific year and month.

    Example usage: generate_time_range_url('2018','01', '12')

    :param year: Year
    :param month: Month

    :return: The URL path for the earthquakes that happened during the specified month and year.
    """
    return EARTHQUAKE_URL_TEMPLATE.format(year=year, month=month, start=start, end=end)


def generate_time_period_url(time_period: int) -> str:
    """
    Generate the URL for extracting earthquakes that occurred during a specific time.

    :param time: The time period for the query. Options are 'day', 'week', 'month'.
    :return: The URL path for the earthquakes that happened during the specified month and year.
    """

    valid_periods = {"hour", "day", "week", "month"}
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


@dataclass()
class TwitterAuth:
    CONSUMER_KEY: str = field(default_factory=lambda: os.environ.get("CONSUMER_KEY"))
    CONSUMER_SECRET: str = field(
        default_factory=lambda: os.environ.get("CONSUMER_SECRET")
    )
    ACCESS_TOKEN: str = field(default_factory=lambda: os.environ.get("ACCESS_TOKEN"))
    ACCESS_TOKEN_SECRET: str = field(
        default_factory=lambda: os.environ.get("ACCESS_TOKEN_SECRET")
    )
    BEARER_TOKEN: str = field(default_factory=lambda: os.environ.get("BEARER_TOKEN"))


TWEET_CONCLUSION = [
    "How do you prepare? Share tips and stay safe! #earthquakePrep. Data provided by #usgs",
    "Were you near the epicenter? Share your experience. #earthquake. Data provided by #usgs",
    "In an #earthquake, use stairs, not elevators! 🚶‍♂️🚶‍♀ #safetyfirst. Data provided by #usgs",
]


CHAT_PROMPT = [
    "Tell me an interesting fact about earthquakes in 140 characters or less, but come close as possible to the 140 characters. Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "Tell me one common misconceptions about earthquakes in 140 characters or less, but come close as possible to the 140 characters. Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    f"Tell me What a {randint(1,10)} magnitude earthquake feel like in 140 characters or less, but come close as possible to the 140 characters. Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes. Make it informational",
    "Tell me an interesting fact about under water earthquakes in 140 characters or less, but come close as possible to the 140 characters. Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "Tell me an interesting fact or tip about aftershocks? Explain in 140 characters, but come close as possible to the 140 characters. Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
]
