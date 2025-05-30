import logging
import os
import random
from datetime import UTC, datetime

from dotenv import load_dotenv

_logger = logging.getLogger(__name__)

load_dotenv()

TIMESTAMP_NOW = datetime.now(UTC)

API_BASE_URL: str = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_{time_period}.geojson"
)

EARTHQUAKE_URL_TEMPLATE: str = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?starttime={start}%2000:00:00&endtime={end}%2023:59:59"
)

EVENT_DETAIL_URL: str = (
    "https://earthquake.usgs.gov/earthquakes/eventpage/{id}/executive"
)

EARTHQUAKE_POST_THRESHOLD = 4.5

REPORTED_SINCE_THRESHOLD = 7200


def generate_time_range_url(start: int, end: int) -> str:
    """
    Generate the URL for extracting earthquakes that occurred during a specific year and month.

    Example usage: generate_time_range_url('2018','01', '12')

    :param year: Year
    :param month: Month

    :return: The URL path for the earthquakes that happened during the specified month and year.
    """
    return EARTHQUAKE_URL_TEMPLATE.format(start=start, end=end)


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
    else:
        _logger.info(
            f"Uplading the recent earthquake events for the last {time_period}......"
        )
        return API_BASE_URL.format(time_period=time_period)


DB_AUTHENTICATION = {
    "user": os.environ.get("NEARQUAKE_USERNAME"),
    "host": os.environ.get("NEARQUAKE_HOST"),
    "dbname": os.environ.get("NEARQUAKE_DATABASE"),
    "port": os.environ.get("NEARQUAKE_PORT"),
    "password": os.environ.get("NEARQUAKE_PASSWORD"),
    "sqlengine": os.environ.get("NEARQUAKE_ENGINE"),
}

POSTGRES_CONNECTION_URL = f"{DB_AUTHENTICATION['sqlengine']}://{DB_AUTHENTICATION['user']}:{DB_AUTHENTICATION['password']}@{DB_AUTHENTICATION['host']}:{DB_AUTHENTICATION['port']}/{DB_AUTHENTICATION['dbname']}"


TWITTER_AUTHENTICATION = {
    "CONSUMER_KEY": os.environ.get("CONSUMER_KEY"),
    "CONSUMER_SECRET": os.environ.get("CONSUMER_SECRET"),
    "ACCESS_TOKEN": os.environ.get("ACCESS_TOKEN"),
    "ACCESS_TOKEN_SECRET": os.environ.get("ACCESS_TOKEN_SECRET"),
    "BEARER_TOKEN": os.environ.get("BEARER_TOKEN"),
}

BLUESKY_USER_NAME = os.environ.get("BLUESKY_USER_NAME")
BLUESKY_PASSWORD = os.environ.get("BLUESKY_PASSWORD")

TWEET_CONCLUSION = [
    "How do you prepare? Share tips and stay safe! #earthquakePrep. Data provided by #usgs",
    "Were you near the epicenter? Share your experience. #earthquake. Data provided by #usgs",
    "In an #earthquake, use stairs, not elevators! 🚶‍♂️🚶‍♀ #safetyfirst. Data provided by #usgs",
]


CHAT_PROMPT = [
    "Tell me an interesting fact about earthquakes in 140 characters or less, but come close as possible to the 140 characters. Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes. I already know about the largest earthquake facts",
    "Tell me one common misconceptions about earthquakes in 140 characters or less, but come close as possible to the 140 characters. Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "Share tips to prepare for earthquakes in 140 characters or less. Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "What should I do if i'm in earthquake in in 140 characters or less. Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "What emergency supplies do you think are crucial to have in an earthquake kit? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "Do you know the safest spots to take cover during an earthquake? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "Do you know what to do if you're outdoors during an earthquake? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "Do you know what to do if you're indoors during an earthquake? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "What lessons have you learned from past earthquakes that can help others prepare? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "What are some items that should be in my earthquake emergency kit? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "What steps can schools take to ensure the safety of students and staff during earthquakes? Share your school preparedness ideas! Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "What considerations should tourists or visitors keep in mind for earthquake safety when visiting earthquake-prone areas? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "How do you ensure that your workplace is prepared for earthquakes? Share your office safety practices! Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "What steps can be taken to support mental health and well-being after experiencing an earthquake? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "What are some consideration before purchasing earthquake insurance? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "walk me through a pros or cons of earthquake insurance? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "What community resources are available to assist with earthquake preparedness efforts? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "How do you stay calm and focused during the chaos of an earthquake? Share your mindfulness techniques! Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "Give me one government agency that deals with eartquakes and what their role. Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "What are the most common misconceptions about earthquake safety? Let's debunk them! Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "What steps can individuals take to support earthquake relief efforts in affected areas? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "What innovative technologies or inventions could improve earthquake preparedness and response in the future? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "How do you ensure the structural integrity of your home or workplace against earthquake damage? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "Do you know what to do if you're in a swimming pool during an earthquake? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "Do you know what to do if you're in a sky scraper during an earthquake? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "Do you know what to do if you're in an air plane during an earthquake? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "Do you know what to do if you're in a boat during an earthquake? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "Do you know what to do if you're driving during an earthquake? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "Do you know what to do if you're in a elevator during earthquake? Convert the response to be appropriate for a Twitter post, and include some hashtags. Do not include quotes",
    "How do you ensure the safety of children and infants during earthquakes? Share your child safety tips!",
    "How do you stay informed about earthquake risks and updates in your area? Share your favorite resources for earthquake information!",
]


COORDINATE_LOOKUP_BASE_URL = "{BASE_URL}?latitude={latitude}&longitude={longitude}&localityLanguage=en&key={API_KEY}"


def generate_coordinate_lookup_detail_url(latitude, longitude) -> str:
    """
    Generate a URL for reverse geocoding using OpenStreetMap's Nominatim API.

    :param lat: Latitude of the location
    :param long: Longitude of the location
    :return: str: A fully formatted URL with specified latitude and longitude.
    """
    return COORDINATE_LOOKUP_BASE_URL.format(
        BASE_URL=os.environ.get("GEO_REVERSE_LOOKUP_BASE_URL"),
        latitude=latitude,
        longitude=longitude,
        API_KEY=os.environ.get("GEO_API_KEY"),
    )


def tweet_conclusion_text():
    tweet_conclusion_text = random.choice(TWEET_CONCLUSION)
    return tweet_conclusion_text
