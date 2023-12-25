import pytest
from nearquake.config import generate_time_range_url, generate_time_period


def test_generate_time_range_url():
    year = 2021
    month = 5
    day = 10
    expected_url = "https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?starttime=2021-5-10%2000:00:00&endtime=2021-5-10%2023:59:59"
    assert generate_time_range_url(year, month, day) == expected_url


def test_generate_time_period_day_url():
    year = 2021
    month = 5
    expected_url = (
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    )
    assert generate_time_period(time_period="day") == expected_url


def test_generate_time_period_week_url():
    year = 2021
    month = 5
    expected_url = (
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson"
    )
    assert generate_time_period(time_period="week") == expected_url


def test_generate_time_period_month_url():
    year = 2021
    month = 5
    expected_url = (
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"
    )
    assert generate_time_period(time_period="month") == expected_url


def test_generate_period_url_error():
    """Test if ValueError is raised for invalid time periods with pytest"""
    with pytest.raises(ValueError):
        generate_time_period(time_period="invalid_time_period")
