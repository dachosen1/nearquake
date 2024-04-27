import requests
import json
import os
import logging
from PIL import Image
from io import BytesIO

from datetime import datetime, timezone, timedelta

from nearquake.config import TIMESTAMP_NOW, EVENT_DETAIL_URL, tweet_conclusion_text

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


def save_content(content: bytes, id: str, directory: str = "image"):
    """
    save byte content into a specified directory.

    :param id_: Identifier to be used in the image file name.
    :param directory: Directory where the image will be saved. Defaults to 'image'.
    :return: None
    """

    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, f"{id}.jpg")

    try:
        with open(os.path.join(directory, f"{id}.jpg"), "wb") as f:
            f.write(content)
            _logger.info(f"Image downloaded and saved to {file_path}")

    except Exception as e:
        _logger.error("An error occured while writing the file: %e", e)


def fetch_json_data_from_url(url):
    """
    Fetches and loads JSON data from a specified URL.

    This function sends an HTTP GET request to the provided URL and attempts to parse
    the response as JSON.

    Note:
        This function assumes that the response is JSON. Non-JSON responses will result in a JSONDecodeError

    Example:
        >>> fetch_json_data_from_url('https://api.example.com/data')
        {'key': 'value'}

    :param url: he URL from which to fetch JSON data.


    :return:  dict or None: A Python dictionary parsed from the JSON response if the request is successful and the response contains valid JSON.
    Returns None if there's an HTTP error or if the response is not valid JSON.

    """
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raise an HTTPError for bad requests (4xx or 5xx)

        try:
            return json.loads(response.text)

        except json.JSONDecodeError:
            _logger.error(f"Failed to decode JSON from response: {response.text}")
            return None

    except requests.exceptions.HTTPError as e:
        _logger.error(f"HTTP error occurred while fetching data from {url}: {e}")
        return None

    except requests.exceptions.ConnectionError as e:
        _logger.error(f"Connection error occurred while fetching data from {url}: {e}")
        return None

    except requests.exceptions.Timeout as e:
        _logger.error(f"Timeout error occurred while fetching data from {url}: {e}")
        return None

    except requests.exceptions.RequestException as e:
        _logger.error(f"An error occurred while fetching data from {url}: {e}")
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


def format_earthquake_alert(
    title: str,
    ts_event: str,
    duration: timedelta,
    id_event: str,
) -> dict:
    """
    _summary_

    :param title: _description_
    :param ts_event: _description_
    :param duration: _description_
    :param id_event: _description_
    :return: _description_
    """

    item = {
        "post": f"Recent #Earthquake: {title} reported at {ts_event} UTC ({duration.seconds/60:.0f} minutes ago). #EarthquakeAlert. \nSee more details at {EVENT_DETAIL_URL.format(id=id_event)}. \n {tweet_conclusion_text()}",
        "ts_upload_utc": TIMESTAMP_NOW.strftime("%Y-%m-%d %H:%M:%S"),
        "id_event": id_event,
    }

    return item


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
