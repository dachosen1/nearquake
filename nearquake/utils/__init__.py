import requests
import json
import os
import logging
from datetime import datetime, timezone

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


def download_image(url, id_, directory="image"):
    """
    Downloads an image from a given URL and saves it into a specified directory.

    :param url: URL of the image to download.
    :param id_: Identifier to be used in the image file name.
    :param directory: Directory where the image will be saved. Defaults to 'image'.
    :return: None
    """
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        _logger.error(f"Failed to download the image from {url}: {err}")
        return

    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, f"{id_}.jpg")

    try:
        with open(os.path.join(directory, f"{id_}.jpg"), "wb") as f:
            f.write(response.content)
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


def generate_date_range(start_date: str, end_date: str):
    """
    Generates a list of [year, month] pairs between two specified dates.

    This function creates a range of dates from the start date to the end date, inclusive.
    It assumes that the provided dates are in 'YYYY-MM' format. The function iterates
    through each year and month within the specified range and returns a list of [year, month]
    pairs.

    Example:
        >>> generate_date_range('2020-01-01', '2020-03-01')
        [[2020, 1], [2020, 2], [2020, 3]]

    :param start_date: The start date in 'YYYY-MM' format.
    :param end_date: The end date in 'YYYY-MM' format.
    :return: list of [int, int]: A list where each element is a list containing two integers, the first being the year and the second the month, for each
    month in the range from start_date to end_date, inclusive.

    """

    # Parse the start and end dates
    start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    end_datetime = datetime.strptime(end_date, "%Y-%m-%d")

    # Check if the start date is later than the end date
    if start_datetime > end_datetime:
        logging.error("Start time cannot be greater than end time")
        raise ValueError(f"Start time cannot be greater than end time")

    date_list = []

    for year in range(start_datetime.year, end_datetime.year + 1):
        start_month = start_datetime.month if year == start_datetime.year else 1
        end_month = end_datetime.month if year == end_datetime.year else 12
        for month in range(start_month, end_month + 1):
            date_list.append([year, month])

    return date_list


def create_dir(path: str):
    """
    Creates a directory if it doesn't exist

    :param path: directory path
    :return:
    """
    if os.path.exists(path):
        pass
    else:
        os.mkdir(path)
        _logger.info(f"Created a new directory path: {path}")
    return None
