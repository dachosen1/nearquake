import datetime
import json
import os
from datetime import timedelta
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
import requests
from PIL import Image

from nearquake.utils import (backfill_valid_date_range, convert_datetime,
                             convert_timestamp_to_utc, create_dir,
                             extract_coordinates, extract_image,
                             extract_properties, extract_url_content,
                             fetch_json_data_from_url, format_earthquake_alert,
                             generate_date_range, get_earthquake_image_url,
                             save_content, timer)


def test_generate_date_range():
    assert generate_date_range(
        start_date="2023-01-01", end_date="2023-02-01", interval=31
    ) == [(datetime.datetime(2023, 1, 1, 0, 0), datetime.datetime(2023, 2, 1, 0, 0))]


def test_generate_date_range_negative():

    result = generate_date_range(
        start_date="2023-01-01", end_date="2022-01-01", interval=15
    )
    assert result == []


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


def test_extract_properties():
    # Test with string values
    data = {"name": "John, Doe", "age": 30, "city": "New York"}
    keylist = ["name", "age"]
    result = extract_properties(data, keylist)
    assert result == {"name": "John Doe", "age": 30}

    # Test with missing keys
    data = {"name": "John, Doe"}
    keylist = ["name", "age"]
    result = extract_properties(data, keylist)
    assert result == {"name": "John Doe", "age": ""}

    # Test with empty data
    data = {}
    keylist = ["name", "age"]
    result = extract_properties(data, keylist)
    assert result == {"name": "", "age": ""}


def test_extract_coordinates():
    data = {
        "features": [
            {"id": "id1", "geometry": {"coordinates": [1.0, 2.0, 3.0]}},
            {"id": "id2", "geometry": {"coordinates": [4.0, 5.0, 6.0]}},
        ]
    }
    result = extract_coordinates(data)
    assert result == [["id1", 1.0, 2.0, 3.0], ["id2", 4.0, 5.0, 6.0]]


@patch("requests.get")
def test_get_earthquake_image_url_success(mock_get):
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=test&format=geojson"
    expected_image_url = "https://example.com/image.jpg"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = json.dumps(
        {
            "properties": {
                "products": {
                    "shakemap": [
                        {"contents": {"download/pga.jpg": {"url": expected_image_url}}}
                    ]
                }
            }
        }
    )
    mock_get.return_value = mock_response

    result = get_earthquake_image_url(url)
    assert result == expected_image_url


@patch("requests.get")
def test_get_earthquake_image_url_failure(mock_get):
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=test&format=geojson"

    # Test HTTP error
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = get_earthquake_image_url(url)
    assert result is None

    # Test KeyError
    mock_response.status_code = 200
    mock_response.text = json.dumps({"properties": {}})
    mock_get.return_value = mock_response

    result = get_earthquake_image_url(url)
    assert result is None


@patch("requests.get")
def test_extract_url_content_success(mock_get):
    url = "https://example.com/content"
    expected_content = b"test content"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = expected_content
    mock_get.return_value = mock_response

    result = extract_url_content(url)
    assert result == expected_content


@patch("requests.get")
def test_extract_url_content_failure(mock_get):
    url = "https://example.com/content"

    # Test HTTP error
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = extract_url_content(url)
    assert result is None


def test_extract_image():
    # Create a simple test image
    test_image = Image.new("RGB", (100, 100), color="red")
    img_byte_arr = BytesIO()
    test_image.save(img_byte_arr, format="JPEG")
    img_byte_arr = img_byte_arr.getvalue()

    result = extract_image(img_byte_arr)
    assert isinstance(result, Image.Image)
    assert result.size == (100, 100)


@patch("os.makedirs")
@patch("builtins.open", new_callable=MagicMock)
def test_save_content(mock_open, mock_makedirs):
    content = b"test content"
    content_id = "test_id"
    directory = "test_dir"

    save_content(content, content_id, directory)

    mock_makedirs.assert_called_once_with(directory, exist_ok=True)
    mock_open.assert_called_once_with(
        os.path.join(directory, f"{content_id}.jpg"), "wb"
    )
    mock_open.return_value.__enter__.return_value.write.assert_called_once_with(content)


def test_backfill_valid_date_range_success():
    start_date = "2023-01-01"
    end_date = "2023-01-15"
    interval = 7

    result = backfill_valid_date_range(start_date, end_date, interval)

    expected = [
        (datetime.datetime(2023, 1, 1, 0, 0), datetime.datetime(2023, 1, 8, 0, 0)),
        (datetime.datetime(2023, 1, 8, 0, 0), datetime.datetime(2023, 1, 15, 0, 0)),
    ]

    assert result == expected


def test_backfill_valid_date_range_invalid_dates():
    # Test start_date after end_date
    try:
        backfill_valid_date_range("2023-01-15", "2023-01-01", 7)
        pytest.fail("Expected ValueError was not raised")
    except ValueError as e:
        assert "Invalid date format" in str(e)

    # Test invalid interval
    try:
        backfill_valid_date_range("2023-01-01", "2023-01-15", 0)
        pytest.fail("Expected ValueError was not raised")
    except ValueError as e:
        assert "Invalid date format" in str(e)

    # Test invalid date format
    with pytest.raises(ValueError, match="Invalid date format"):
        backfill_valid_date_range("01-01-2023", "2023-01-15", 7)


@patch("nearquake.config.TIMESTAMP_NOW")
@patch("nearquake.config.EVENT_DETAIL_URL")
@patch("nearquake.utils.tweet_conclusion_text")
def test_format_earthquake_alert_event(
    mock_tweet_conclusion, mock_event_detail_url, mock_timestamp
):
    mock_timestamp.strftime.return_value = "2023-01-01 12:00:00"
    mock_event_detail_url.format.return_value = "https://example.com/event/123"
    mock_tweet_conclusion.return_value = "Stay safe!"

    result = format_earthquake_alert(
        post_type="event",
        title="Test Earthquake",
        ts_event="2023-01-01 11:30:00",
        duration=timedelta(minutes=30),
        id_event="123",
        message="Magnitude 5.0",
    )

    assert result["post_type"] == "event"
    assert result["id_event"] == "123"
    assert (
        "Recent #Earthquake: Magnitude 5.0 reported at 2023-01-01 11:30:00 UTC (30 minutes ago)"
        in result["post"]
    )
    assert "Stay safe!" in result["post"]
    assert "earthquake.usgs.gov/earthquakes/eventpage/123/executive" in result["post"]


@patch("nearquake.config.TIMESTAMP_NOW")
def test_format_earthquake_alert_fact(mock_timestamp):
    mock_timestamp.strftime.return_value = "2023-01-01 12:00:00"

    test_message = "Did you know earthquakes can cause tsunamis?"
    result = format_earthquake_alert(post_type="fact", message=test_message)

    assert result["post"] == test_message
    assert result["id_event"] is None
    assert result["post_type"] == "fact"


def test_format_earthquake_alert_invalid_type():
    with pytest.raises(
        ValueError, match="Invalid post type. Please choose 'event' or 'fact'."
    ):
        format_earthquake_alert(post_type="invalid")


def test_convert_datetime():
    test_date = datetime.datetime(2023, 1, 1, 12, 30, 45)

    # Test date format
    assert convert_datetime(test_date, "date") == "2023-01-01"

    # Test timestamp format
    assert convert_datetime(test_date, "timestamp") == "2023-01-01 12:30:45"

    # Test default format
    assert convert_datetime(test_date) == "2023-01-01"

    # Test invalid format
    with pytest.raises(
        ValueError, match="Invalid format_type. Only 'date' or 'timestamp' are allowed."
    ):
        convert_datetime(test_date, "invalid")


@patch("time.perf_counter")
def test_timer_decorator_seconds(mock_perf_counter):
    # Setup mock to return different values on consecutive calls
    mock_perf_counter.side_effect = [10.0, 15.0]  # 5 seconds difference

    # Create a test function with the timer decorator
    @timer
    def test_function():
        return "test result"

    # Use a mock logger to capture the log output
    with patch("nearquake.utils._logger") as mock_logger:
        result = test_function()

        # Check that the function result is returned correctly
        assert result == "test result"

        # Check that the logger was called with the correct message
        mock_logger.info.assert_called_once_with("test_function completed in 5 seconds")


@patch("time.perf_counter")
def test_timer_decorator_minutes(mock_perf_counter):
    # Setup mock to return different values on consecutive calls
    mock_perf_counter.side_effect = [10.0, 130.0]  # 120 seconds = 2 minutes

    @timer
    def test_function():
        return "test result"

    with patch("nearquake.utils._logger") as mock_logger:
        result = test_function()
        assert result == "test result"
        mock_logger.info.assert_called_once_with("test_function completed in 2 minutes")


@patch("time.perf_counter")
def test_timer_decorator_hours(mock_perf_counter):
    # Setup mock to return different values on consecutive calls
    mock_perf_counter.side_effect = [10.0, 7210.0]  # 7200 seconds = 2 hours

    @timer
    def test_function():
        return "test result"

    with patch("nearquake.utils._logger") as mock_logger:
        result = test_function()
        assert result == "test result"
        mock_logger.info.assert_called_once_with("test_function completed in 2 hours")
