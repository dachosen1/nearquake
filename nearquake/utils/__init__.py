import requests
import json
import os
import logging
from datetime import datetime, timezone

_logger = logging.getLogger(__name__)


def extract_properties(data, keylist):
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

    :param url: URL to the earthquake data.
    :return: String containing the URL to the image, or None if no image could be found.
    """
    response = requests.get(url, timeout=5)
    if response.status_code != 200:
        _logger.error(
            "Failed to get data from URL %s. Status code: %s", url, response.status_code
        )
        return None

    try:
        data = json.loads(response.text)
        image_url = data["properties"]["products"]["shakemap"][0]["contents"][
            "download/pga.jpg"
        ]["url"]
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
        print(f"Error: {err}")
        return

    os.makedirs(directory, exist_ok=True)

    try:
        with open(os.path.join(directory, f"{id_}.jpg"), "wb") as f:
            f.write(response.content)
    except Exception as e:
        _logger.error("An error occured while writing the file: %e", e)


def fetch_json_data_from_url(url):
    """
    Loads  data from a provided URL.

    :param url: URL
    """
    response = requests.get(url, timeout=5)

    if response.status_code != 200:
        _logger.error(
            "Failed to get data from URL %s. Status code: %s", url, response.status_code
        )
        return None
    try:
        response.raise_for_status()
        return json.loads(response.text)
    except json.JSONDecodeError:
        _logger.exception("Could not find image URL in response data.")
        return None


def convert_timestamp_to_utc(timestamp):
    # The given timestamp (assuming it's in milliseconds)
    timestamp = timestamp

    # Convert milliseconds to seconds
    timestamp_seconds = timestamp / 1000

    # Convert to datetime object in UTC
    utc_datetime = datetime.fromtimestamp(timestamp_seconds, timezone.utc)

    return utc_datetime


def extract_year_and_month(date):
    date = datetime.strptime(date, "%Y-%m-%d").date()
    return date.year, date.month


def generate_date_range(start_date, end_date):
    start_year, start_month = extract_year_and_month(start_date)
    end_year, end_month = extract_year_and_month(end_date)

    date_list = []

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            if year == start_year and month >= start_month:
                date_list.append([year, month])
            elif year == end_year and month <= end_month:
                date_list.append([year, month])
            elif year > start_year and year <= end_year:
                date_list.append([year, month])
    return date_list
