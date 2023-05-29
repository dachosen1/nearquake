import os 
import requests
import json
from utils.db import DbOperator
from config import API_URL, EARTH_QUAKE_FEATURES, generate_earthquake_url
import logging

_logger = logging.getLogger(__name__)


def load_earthquake_data(url, time_range):
    """
    Loads earthquake data from a provided URL.

    :param url: URL
    :param time_range: Time range to upload the data options are ['day', 'week', 'month']
    """
    response = requests.get(url.format(time=time_range), timeout=5)

    if response.status_code != 200:
        _logger.error(
            f"Failed to get data from URL {url}. Status code: {response.status_code}"
        )
        return None
    try:
        response.raise_for_status()
        return json.loads(response.text)
    except json.JSONDecodeError:
        _logger.exception("Could not find image URL in response data.")
        return None


if __name__ == "__main__":
    db = DbOperator()
    db.connect(
        host=os.getenv("NEARQUAKE_HOST"),
        user=os.getenv("NEARQUAKE_USERNAME"),
        password=os.getenv("NEARQUAKE_PASSWORD"),
        dbname=os.getenv("NEARQUAKE_DATABASE"),
        port=5433,
    )

    load_earthquake_data(url=API_URL, time_range='day')
