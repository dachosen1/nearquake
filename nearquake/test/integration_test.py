from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from nearquake.config import generate_time_period_url
from nearquake.data_processor import (TweetEarthquakeEvents,
                                      UploadEarthQuakeEvents,
                                      UploadEarthQuakeLocation)


# Mock database session for testing
class MockSession:
    def __init__(self):
        self.session = MagicMock()
        self.query = MagicMock()
        self.insert_many = MagicMock()
        self.insert = MagicMock()
        self.add = MagicMock()
        self.commit = MagicMock()
        self.close = MagicMock()
        self.execute = MagicMock()
        self.fetch_many = MagicMock(return_value=[])


@pytest.fixture(scope="module")
def test_db():
    """Create a mock database session for integration tests."""
    return MockSession()


# Mock database models for testing
class MockEventDetails:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockLocationDetails:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.mark.integration
class TestDataProcessingIntegration:
    """Integration tests for the data processing pipeline."""

    @pytest.mark.parametrize("time_period", ["hour", "day", "week", "month"])
    def test_earthquake_data_pipeline(self, test_db, time_period):
        """Test the complete earthquake data pipeline with mocked API responses."""
        # Test the earthquake data upload process
        with patch.object(UploadEarthQuakeEvents, "upload") as mock_upload:
            # Create and run the uploader
            uploader = UploadEarthQuakeEvents(test_db)
            url = generate_time_period_url(time_period)
            uploader.upload(url=url)

            # Verify upload was called
            assert mock_upload.called

    def test_location_data_pipeline(self, test_db):
        """Test the location data processing pipeline."""
        # Create a test earthquake event
        test_event_data = {
            "id_event": "location_test_id",
            "mag": 6.0,
            "ts_event_utc": datetime.now() - timedelta(hours=1),
            "longitude": 120.0,
            "latitude": 30.0,
        }

        # Mock the geolocation API response
        sample_location_response = {
            "continent": "Asia",
            "continentCode": "AS",
            "countryName": "China",
            "countryCode": "CN",
            "principalSubdivision": "Zhejiang",
            "city": "Hangzhou",
        }

        # Configure mock query to return our test event
        mock_event = ("location_test_id", 30.0, 120.0)  # id_event, latitude, longitude
        test_db.session.query.return_value.join.return_value.filter.return_value.all.return_value = [
            mock_event
        ]

        # Test the location data upload process
        with patch(
            "nearquake.data_processor.fetch_json_data_from_url",
            return_value=sample_location_response,
        ):
            # Create and run the uploader
            uploader = UploadEarthQuakeLocation(test_db)
            start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            end_date = datetime.now().strftime("%Y-%m-%d")

            # Also patch the backfill_valid_date_range function
            with patch(
                "nearquake.data_processor.backfill_valid_date_range"
            ) as mock_backfill:
                mock_start = datetime.strptime("2022-01-01", "%Y-%m-%d").date()
                mock_end = datetime.strptime("2022-01-15", "%Y-%m-%d").date()
                mock_backfill.return_value = [(mock_start, mock_end)]

                uploader.upload(start_date=start_date, end_date=end_date)

            # Verify insert_many was called
            assert test_db.insert_many.called

    def test_tweet_pipeline(self, test_db):
        """Test the tweet processing pipeline."""
        # Create a test earthquake event that should be eligible for tweeting
        test_event_data = {
            "id_event": "tweet_test_id",
            "mag": 6.5,  # High magnitude to ensure it's eligible
            "ts_event_utc": datetime.now() - timedelta(minutes=5),  # Recent event
            "longitude": 120.0,
            "latitude": 30.0,
            "title": "Test Earthquake for Tweeting",
        }

        # Configure mock query to return our test event
        mock_event = MockEventDetails(**test_event_data)
        test_db.session.query.return_value.join.return_value.filter.return_value.filter.return_value.all.return_value = [
            mock_event
        ]

        # Test the tweet process
        with patch("nearquake.data_processor.post_and_save_tweet") as mock_post:
            # Create and run the tweeter
            tweeter = TweetEarthquakeEvents(test_db)
            tweeter.upload()

            # Verify that post_and_save_tweet was called
            assert mock_post.called


@pytest.mark.integration
def test_end_to_end_pipeline(test_db):
    """Test the complete data pipeline from fetching to posting."""
    # Mock all external API calls
    with (
        patch.object(UploadEarthQuakeEvents, "upload") as mock_earthquake_upload,
        patch.object(UploadEarthQuakeLocation, "upload") as mock_location_upload,
        patch.object(TweetEarthquakeEvents, "upload") as mock_tweet_upload,
    ):

        # Step 1: Upload earthquake data
        earthquake_uploader = UploadEarthQuakeEvents(test_db)
        earthquake_uploader.upload(url=generate_time_period_url("hour"))

        # Step 2: Upload location data
        location_uploader = UploadEarthQuakeLocation(test_db)
        start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        location_uploader.upload(start_date=start_date, end_date=end_date)

        # Step 3: Process tweets
        tweeter = TweetEarthquakeEvents(test_db)
        tweeter.upload()

        # Verify all methods were called
        assert mock_earthquake_upload.called
        assert mock_location_upload.called
        assert mock_tweet_upload.called
