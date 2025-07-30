from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from nearquake.app.db import EventDetails
from nearquake.data_processor import (
    BaseDataUploader,
    TweetEarthquakeEvents,
    UploadEarthQuakeEvents,
    UploadEarthQuakeLocation,
    get_date_range_summary,
)
from sqlalchemy.orm import Session


class MockQuery:
    def __init__(self, return_value=None):
        self.return_value = return_value or []

    def join(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self.return_value


@pytest.fixture
def mock_session():
    session = MagicMock(spec=Session)
    session.session = MagicMock()  # Add session attribute to mock

    # Add additional methods needed by tests
    session.fetch_many = MagicMock(return_value=[])
    session.insert_many = MagicMock()
    session.insert = MagicMock()

    return session


@pytest.fixture
def mock_earthquake_data():
    return {
        "id": "test_id",
        "properties": {
            "mag": 5.0,
            "time": 1646870400000,  # 2022-03-10 00:00:00 UTC
            "tz": "UTC",
            "felt": 100,
            "detail": "test_detail",
            "cdi": 5.0,
            "mmi": 4.0,
            "status": "reviewed",
            "tsunami": 0,
            "type": "earthquake",
            "title": "Test Earthquake",
            "place": "Test Location",
        },
        "geometry": {"coordinates": [1.0, 2.0]},
    }


@pytest.fixture
def mock_location_data():
    return {
        "continent": "North America",
        "continentCode": "NA",
        "countryName": "United States",
        "countryCode": "US",
        "principalSubdivision": "California",
        "principalSubdivisionCode": "CA",
        "city": "Los Angeles",
    }


def test_base_data_uploader_abstract(mock_session):
    """Test that BaseDataUploader cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseDataUploader(mock_session)


class TestUploadEarthQuakeEvents:
    @pytest.fixture
    def uploader(self, mock_session):
        return UploadEarthQuakeEvents(mock_session)

    @pytest.mark.parametrize(
        "api_response,expected_count",
        [
            (
                {
                    "features": [
                        {
                            "id": "test_id_1",
                            "properties": {"mag": 5.0},
                            "geometry": {"coordinates": [1.0, 1.0]},
                        }
                    ]
                },
                1,
            ),
            ({"features": []}, 0),
            ({"features": [{"id": "test_id_1"}, {"id": "test_id_2"}]}, 2),
        ],
    )
    def test_extract_new_events(
        self, uploader, mock_session, api_response, expected_count
    ):
        """Test extraction of new earthquake events with different API responses."""
        with patch(
            "nearquake.data_processor.fetch_json_data_from_url",
            return_value=api_response,
        ):
            mock_session.fetch_many.return_value = []
            events = uploader._extract("test_url")
            assert len(events) == expected_count

    def test_fetch_event_details(self, uploader, mock_earthquake_data):
        """Test creation of event details from raw earthquake data."""
        event_details = uploader._fetch_event_details(mock_earthquake_data)

        assert event_details.id_event == "test_id"
        assert event_details.mag == 5.0
        assert event_details.longitude == 1.0
        assert event_details.latitude == 2.0
        assert event_details.type == "earthquake"
        assert event_details.title == "Test Earthquake"
        assert event_details.place == "Test Location"

    def test_upload_with_no_new_events(self, uploader):
        """Test upload method when no new events are found."""
        with patch.object(uploader, "_extract", return_value=[]):
            uploader.upload("test_url")
            uploader.conn.insert_many.assert_not_called()


class TestUploadEarthQuakeLocation:
    @pytest.fixture
    def uploader(self, mock_session):
        return UploadEarthQuakeLocation(mock_session)

    def test_fetch_location_detail_success(self, uploader, mock_location_data):
        """Test successful fetching of location details."""
        with patch(
            "nearquake.data_processor.fetch_json_data_from_url",
            return_value=mock_location_data,
        ):
            test_event = ("test_id", 34.0522, -118.2437)
            location_details = uploader._fetch_location_detail(test_event)

            assert location_details.id_event == "test_id"
            assert location_details.continent == "North America"
            assert location_details.city == "Los Angeles"
            assert location_details.countryCode == "US"

    def test_fetch_location_detail_api_error(self, uploader):
        """Test handling of API errors in location detail fetching."""
        with patch(
            "nearquake.data_processor.fetch_json_data_from_url", return_value=None
        ):
            test_event = ("test_id", 34.0522, -118.2437)
            location_details = uploader._fetch_location_detail(test_event)
            assert location_details is None

    @pytest.mark.parametrize(
        "start_date,end_date",
        [
            ("2022-01-01", "2022-01-02"),
            ("2022-01-01", None),
            ("2022-01-01", "2022-12-31"),
        ],
    )
    def test_upload_with_different_date_ranges(self, uploader, start_date, end_date):
        """Test upload method with different date ranges."""
        # Create datetime objects for the mock
        mock_start = datetime.strptime("2022-01-01", "%Y-%m-%d").date()
        mock_end = datetime.strptime("2022-01-15", "%Y-%m-%d").date()

        with patch.object(uploader, "_extract_between", return_value=[]), patch(
            "nearquake.data_processor.backfill_valid_date_range",
            return_value=[(mock_start, mock_end)],
        ):
            uploader.upload(start_date=start_date, end_date=end_date)
            uploader.conn.insert_many.assert_not_called()


class TestTweetEarthquakeEvents:
    @pytest.fixture
    def tweeter(self, mock_session):
        return TweetEarthquakeEvents(mock_session)

    @pytest.fixture
    def mock_quake(self):
        quake = MagicMock()
        quake.id_event = "test_id"
        quake.title = "Test Earthquake"
        quake.ts_event_utc = datetime.now(timezone.utc)
        quake.mag = 6.0
        return quake

    def test_upload_eligible_quakes(self, tweeter, mock_quake):
        """Test tweeting of eligible earthquake events."""
        mock_query = MockQuery([mock_quake])
        tweeter.conn.session.query.return_value = mock_query

        with patch("nearquake.data_processor.post_and_save_tweet") as mock_post:
            tweeter.upload()
            mock_post.assert_called_once()

    def test_upload_no_eligible_quakes(self, tweeter):
        """Test behavior when no eligible quakes are found."""
        mock_query = MockQuery([])
        tweeter.conn.session.query.return_value = mock_query

        with patch("nearquake.data_processor.post_and_save_tweet") as mock_post:
            tweeter.upload()
            mock_post.assert_not_called()


@pytest.mark.parametrize(
    "date_range,expected_count",
    [
        (("2022-01-01", "2022-01-02"), 1),
        (("2022-01-01", "2022-12-31"), 2),
    ],
)
def test_get_date_range_summary(mock_session, date_range, expected_count):
    """Test getting earthquake summaries for different date ranges."""
    mock_events = [MagicMock(spec=EventDetails) for _ in range(expected_count)]
    mock_query = MockQuery(mock_events)
    mock_session.session.query.return_value = mock_query

    result = get_date_range_summary(
        mock_session, EventDetails, date_range[0], date_range[1]
    )

    assert len(result) == expected_count
    assert all(isinstance(event, MagicMock) for event in result)
