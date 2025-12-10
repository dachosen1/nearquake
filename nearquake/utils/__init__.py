import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from io import BytesIO

import requests
from PIL import Image

from nearquake.config import EVENT_DETAIL_URL, TIMESTAMP_NOW, tweet_conclusion_text

_logger = logging.getLogger(__name__)


def extract_properties(data: dict, keylist: list):
    """
    Extracts specified properties from a data dictionary and removes specific characters.

    Given a dictionary and a list of keys, this function creates a new dictionary containing
    only the key-value pairs where the keys are in the provided list.

    Example:
    >>> extract_properties({'name': 'John, Doe', 'age': 30, 'city': 'New York'}, ['name', 'age'])
    {'name': 'JohnDoe', 'age': 30}

    :param data: The dictionary from which to extract properties
    :param keylist: A list of keys to extract from the dictionary.

    :return: dict: A dictionary containing key-value pairs for each key in keylist. String values
              are stripped of commas, single quotes, and spaces. Non-string values are
              included as-is.
    """
    table = str.maketrans("", "", ",'")
    return {
        key: (
            data.get(key, "").translate(table)
            if isinstance(data.get(key, ""), str)
            else data.get(key, "")
        )
        for key in keylist
    }


def extract_coordinates(data):
    coordinates = []
    for d in data["features"]:
        coordinates.append([d["id"], *d["geometry"]["coordinates"]])
    return coordinates


def get_earthquake_image_url(url):
    """
    Extract the image URL from the results of the USA.gov earthquake API

    Example:
        get_earthquake_image_url("https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=us6000kd0n&format=geojson")

    :param url: URL to the earthquake data.
    :return: String containing the URL to the image, or None if no image could be found.
    """
    response = requests.get(url, timeout=5)
    if response.status_code != 200:
        _logger.error(
            f"Failed to get data from URL {url}. Status code: {response.status_code}"
        )
        return None

    try:
        data = json.loads(response.text)
        image_url = data["properties"]["products"]["shakemap"][0]["contents"][
            "download/pga.jpg"
        ]["url"]
        _logger.info("")
        return image_url
    except KeyError:
        _logger.error("Could not find image URL in response data.")
        return None


def extract_url_content(url: str) -> bytes:
    """
    Extract content from a given URL.

    :param url: The URL from which content will be extracted.
    :return: The content retrieved from the URL in binary format (bytes).
    """
    response = requests.get(url, timeout=5)

    if response.status_code != 200:
        _logger.error(
            f"Failed to get data from URL {url}. Status code: {response.status_code}"
        )
        return None

    try:
        content = response.content
        return content

    except KeyError:
        _logger.error("Could not find image URL in response data.")
        return None


def extract_image(image_data: bytes) -> Image.Image:
    """
    Extract an image from binary image data.

    :param image_data: The binary image data to be processed.
    :return: A Pillow (PIL) Image object representing the extracted image.
    """
    image_stream = BytesIO(image_data)
    image = Image.open(image_stream)
    return image


def save_content(content: bytes, content_id: str, directory: str = "image"):
    """
    save byte content into a specified directory.

    :param content_id: Identifier to be used in the image file name.
    :param directory: Directory where the image will be saved. Defaults to 'image'.
    :return: None
    """

    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, f"{content_id}.jpg")

    try:
        with open(os.path.join(directory, f"{content_id}.jpg"), "wb") as f:
            f.write(content)
            _logger.info(f"Image downloaded and saved to {file_path}")

    except Exception as e:
        _logger.error("An error occured while writing the file: %e", e)


def fetch_json_data_from_url(url, params=None):
    """
    Fetches and loads JSON data from a specified URL.

    This function sends an HTTP GET request to the provided URL and attempts to parse
    the response as JSON.

    Note:
        This function assumes that the response is JSON. Non-JSON responses will result in a JSONDecodeError

    Example:
        >>> fetch_json_data_from_url('https://api.example.com/data')
        {'key': 'value'}

    :param url: The URL from which to fetch JSON data.
    :param params: Optional dictionary of query parameters to add to the request.

    :return: dict or None: A Python dictionary parsed from the JSON response if the request is successful and the response contains valid JSON.
    Returns None if there's an HTTP error or if the response is not valid JSON.

    """
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()  # Raise an HTTPError for bad requests (4xx or 5xx)

        try:
            return json.loads(response.text)

        except json.JSONDecodeError:
            _logger.error("Failed to decode JSON from the response.")

            return None

    except requests.exceptions.HTTPError as e:
        _logger.error(f"HTTP error occurred while fetching data: {e}")
        return None

    except requests.exceptions.ConnectionError as e:
        _logger.error(f"Connection error occurred while fetching data: {e}")
        return None

    except requests.exceptions.Timeout as e:
        _logger.error(f"Timeout error occurred while fetching data: {e}")
        return None

    except requests.exceptions.RequestException as e:
        _logger.error(f"An error occurred while fetching data: {e}")
        return None


def convert_timestamp_to_utc(timestamp: int):
    """
    Converts a given timestamp into a UTC datetime object.

    This function takes a timestamp (assumed to be in milliseconds since the Unix epoch)
    and converts it into a Python datetime object in UTC.

    :param timestamp: The timestamp to be converted. This should be an integer representing the time in milliseconds since the Unix epoch
    (00:00:00 UTC on 1 January 1970).

    Example:
        >>> convert_timestamp_to_utc(1609459200000)
        datetime.datetime(2021, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)

    :return: datetime: A datetime object representing the given timestamp in UTC.

    """
    return datetime.fromtimestamp(timestamp / 1000, timezone.utc)


def generate_date_range(start_date, end_date, interval) -> tuple:
    """
    Generates a list of (start_date, end_date) tuples where each tuple represents a range.
    Each range starts at 'start_date' and ends at the minimum of 'end_date' or 'start_date' + 'interval', incremented by 'interval' days.


    :param start_date: The beginning date of the range (format: 'YYYY-MM-DD').
    :param end_date: The ending date of the range (format: 'YYYY-MM-DD').
    :param interval: The number of days to increment each start date within the range.
    :return: A list of tuples, each containing a start and end date.
    """

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    current_start_date = start_date
    date_list = []

    while current_start_date < end_date:
        current_end_date = min(end_date, current_start_date + timedelta(days=interval))
        date_list.append((current_start_date, current_end_date))
        current_start_date = current_end_date

    return date_list


def backfill_valid_date_range(start_date, end_date, interval: int) -> tuple:
    """
    Validates the date format of start and end dates, generates a range of dates
    within the specified interval, and logs the backfill process.

    :param start_date: The start date in "YYYY-MM-DD" format.
    :param end_date: The end date in "YYYY-MM-DD" format.
    :param interval: The interval in days between each date in the range

    :return: A tuple of date ranges from start_date to end_date with the specified interval
    """

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        if start >= end:
            raise ValueError("start_date must be before end_date")
        if interval <= 0:
            raise ValueError("interval must be positive")

    except ValueError as err:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.") from err

    date_range = generate_date_range(start_date, end_date, interval=interval)

    _logger.info(
        f"Backfill process started for the range {start_date} to {end_date}. Running in module {__name__}."
    )
    return date_range


def create_dir(path: str):
    """
    Creates a directory if it doesn't exist.

    :param path: The path of the directory to be created.
    :return: None
    """
    try:
        os.makedirs(path, exist_ok=True)
        _logger.info(f"Directory ensured at path: {path}")
    except Exception as e:
        _logger.error(f"Failed to create directory at {path}: {e}")
        raise ValueError

    return None


def get_earthquake_emoji(magnitude: float) -> str:
    """
    Returns contextually appropriate emoji based on earthquake magnitude.

    :param magnitude: Earthquake magnitude
    :return: Emoji string
    """
    if magnitude >= 7.0:
        return "🚨"  # Critical alert
    elif magnitude >= 6.0:
        return "⚠️"  # Warning
    elif magnitude >= 5.0:
        return "📢"  # Alert
    else:
        return "🌍"  # General earth/location


def format_earthquake_alert(
    post_type: str,
    ts_event: str = None,
    duration: timedelta = None,
    id_event: str = None,
    message: str = None,
    magnitude: float = None,
    felt: int = None,
    tsunami: bool = None,
) -> dict:
    """
    Formats an alert for an earthquake event or fact.

    :param ts_event: Timestamp of the earthquake occurrence in UTC.
    :param duration: Duration since the earthquake event occurred.
    :param id_event: Unique identifier for the earthquake event.
    :param post_type: Type of post, either 'event' or 'fact'.
    :param message: Message content for fact-type posts.
    :param magnitude: Earthquake magnitude.
    :param place: Location description.
    :param felt: Number of people who reported feeling it.
    :param tsunami: Whether tsunami was generated.
    :return: A dictionary formatted as an alert or fact post.
    """

    ts_upload_utc = TIMESTAMP_NOW.strftime("%Y-%m-%d %H:%M:%S")

    if post_type == "event":
        # Get appropriate emoji
        emoji = get_earthquake_emoji(magnitude)

        # Format with impact first
        minutes_ago = duration.seconds / 60
        time_str = f"{minutes_ago:.0f} min ago" if minutes_ago < 60 else f"{minutes_ago/60:.1f} hrs ago"

        # Build the tweet with better formatting - use title directly
        tweet_lines = [
            f"{emoji} {message}",
            f"🕐 {ts_event} UTC ({time_str})",
        ]

        # Add felt reports if available - this creates engagement!
        if felt and felt > 0:
            tweet_lines.append(f"🙋 {felt:,} people reported feeling it")

        # Add tsunami warning if applicable
        if tsunami:
            tweet_lines.append("🌊 TSUNAMI WARNING")

        tweet_text = "\n".join(tweet_lines)
        tweet_text += f"\n\n🔗 Full details: {EVENT_DETAIL_URL.format(id=id_event)}"

        # Add engaging call-to-action based on magnitude
        if magnitude >= 5.5:
            tweet_text += "\n\n💬 Did you feel it? Reply with your location!"
        else:
            tweet_text += f"\n{tweet_conclusion_text()}"

        return {
            "post": tweet_text,
            "ts_upload_utc": ts_upload_utc,
            "id_event": id_event,
            "post_type": post_type,
        }
    elif post_type == "fact":
        return {
            "post": message,
            "ts_upload_utc": ts_upload_utc,
            "id_event": None,
            "post_type": post_type,
        }
    else:
        raise ValueError("Invalid post type. Please choose 'event' or 'fact'.")


def convert_datetime(date: datetime, format_type: str = "date") -> str:
    """
    Convert a datetime object to a formatted string.

    :param date: The datetime object to format.
    :param format_type: The type of format to apply. Options are date or timestamp defaults to 'date'
    :return: The formatted date string.
    """
    if format_type == "date":
        return date.strftime("%Y-%m-%d")
    elif format_type == "timestamp":
        return date.strftime("%Y-%m-%d %H:%M:%S")
    else:
        raise ValueError("Invalid format_type. Only 'date' or 'timestamp' are allowed.")


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_ts = time.perf_counter()
        result = func(*args, **kwargs)
        end_ts = time.perf_counter()
        duration = end_ts - start_ts
        if duration < 60:
            value, period = duration, "seconds"
        elif duration < 3600:
            value, period = duration // 60, "minutes"
        else:
            value, period = duration // 3600, "hours"

        _logger.info(f"{func.__name__} completed in {value:.0f} {period}")
        return result

    return wrapper


def generate_earthquake_context(magnitude: float, location: str) -> str:
    """
    Generate historical context for a significant earthquake using OpenAI.

    :param magnitude: Earthquake magnitude
    :param location: Location description
    :return: Context text suitable for a tweet (280 chars or less)
    """
    from nearquake.open_ai_client import generate_response

    prompt = f"""Generate a brief historical context tweet (max 250 characters) about a M{magnitude} earthquake near {location}.

Include ONE of the following if relevant:
- Comparison to recent earthquakes in this region
- Historical earthquake activity in this area
- What this magnitude typically means for ground shaking

Keep it factual, informative, and concise. Do NOT include quotes, hashtags, or emojis. This will be tweet 2 in a thread."""

    try:
        response = generate_response(prompt=prompt, role="user", model="gpt-4o-mini")
        # Truncate if needed
        if len(response) > 250:
            response = response[:247] + "..."
        return response
    except Exception as e:
        _logger.error(f"Failed to generate earthquake context: {e}")
        return f"This M{magnitude} earthquake is significant for the {location} region. Historical data suggests events of this size can cause damage to structures."


def generate_preparedness_tip() -> str:
    """
    Generate a preparedness tip using OpenAI.

    :return: Preparedness tip text suitable for a tweet (280 chars or less)
    """
    from nearquake.open_ai_client import generate_response

    prompt = """Generate a brief earthquake preparedness tip (max 250 characters).

Focus on ONE actionable tip such as:
- What to do during shaking
- Emergency kit essentials
- Home safety measures
- Community preparedness

Keep it concise and actionable. Do NOT include quotes or excessive hashtags. Include 1-2 relevant emojis. This will be the final tweet in a 3-tweet thread."""

    try:
        response = generate_response(prompt=prompt, role="user", model="gpt-4o-mini")
        # Truncate if needed
        if len(response) > 250:
            response = response[:247] + "..."
        return response
    except Exception as e:
        _logger.error(f"Failed to generate preparedness tip: {e}")
        return "🏠 Secure heavy items to walls and practice Drop, Cover, and Hold On with your family. Being prepared saves lives! #EarthquakePrep"
