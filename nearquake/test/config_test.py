import pytest
from nearquake.config import generate_time_period_url, generate_time_range_url


def test_generate_time_range_url():
    start = "2021-01-01"
    end = "2023-01-01"
    expected_url = "https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?starttime=2021-01-01%2000:00:00&endtime=2023-01-01%2023:59:59"
    assert generate_time_range_url(start=start, end=end) == expected_url


def test_generate_time_period_url_day_url():
    expected_url = (
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    )
    assert generate_time_period_url(time_period="day") == expected_url


def test_generate_time_period_url_week_url():
    expected_url = (
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson"
    )
    assert generate_time_period_url(time_period="week") == expected_url


def test_generate_time_period_url_month_url():
    expected_url = (
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"
    )
    assert generate_time_period_url(time_period="month") == expected_url


def test_generate_time_period_url_hour_url():
    expected_url = (
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
    )
    assert generate_time_period_url(time_period="hour") == expected_url


def test_generate_period_url_error():
    """Test if ValueError is raised for invalid time periods with pytest"""
    with pytest.raises(ValueError):
        generate_time_period_url(time_period="invalid_time_period")
