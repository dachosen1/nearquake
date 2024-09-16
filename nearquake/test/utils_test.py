import datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

from nearquake.utils import (
    convert_timestamp_to_utc,
    create_dir,
    fetch_json_data_from_url,
    generate_date_range,
)


def test_generate_date_range():
    assert generate_date_range(
        start_date="2023-01-01", end_date="2023-02-01", interval=31
    ) == [(datetime.datetime(2023, 1, 1, 0, 0), datetime.datetime(2023, 2, 1, 0, 0))]


def test_generate_date_range_negative():

    generate_date_range(
        start_date="2023-01-01", end_date="2022-01-01", interval=15
    ) == []


def test_convert_time_to_utc():
    assert convert_timestamp_to_utc(1609459200000).strftime("%Y-%m-%d") == "2021-01-01"


@patch("os.makedirs")
def test_create_dir_success(mock_makedirs):
    path = "/path/to/directory"

    create_dir(path)

    mock_makedirs.assert_called_once_with(path, exist_ok=True)


@patch("os.makedirs", side_effect=Exception("Failed to create directory"))
def test_create_dir_failure(mock_makedirs):
    path = "/path/to/directory"

    with pytest.raises(ValueError):
        create_dir(path)


@patch("requests.get")
def test_fetch_json_data_from_url_success(mock_get):
    url = "https://api.example.com/data"
    expected_json_data = {"key": "value"}

    mock_response = MagicMock()
    mock_response.text = '{"key": "value"}'
    mock_get.return_value = mock_response

    json_data = fetch_json_data_from_url(url)

    assert json_data == expected_json_data


@patch("requests.get")
def test_fetch_json_data_from_url_http_error(mock_get):
    url = "https://api.example.com/data"

    mock_get.side_effect = requests.exceptions.HTTPError("HTTP Error")

    json_data = fetch_json_data_from_url(url)

    assert json_data is None


@patch("requests.get")
def test_fetch_json_data_from_url_json_decode_error(mock_get):
    url = "https://api.example.com/data"

    mock_response = MagicMock()
    mock_response.text = "Not a JSON response"
    mock_get.return_value = mock_response

    json_data = fetch_json_data_from_url(url)

    assert json_data is None
