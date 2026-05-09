from unittest.mock import MagicMock, patch

import pytest

from nearquake.app.db import Post
from nearquake.post_manager import (
    BlueSkyPost,
    PlatformPoster,
    TwitterPost,
    post_and_save_tweet,
    post_to_all_platforms,
    save_tweet_to_db,
)


class TestPlatformPoster:
    def test_abstract_class(self):
        # Verify that PlatformPoster is an abstract class that can't be instantiated directly
        with pytest.raises(TypeError):
            PlatformPoster()


class TestTwitterPost:
    @patch("tweepy.Client")
    def test_init(self, mock_client):
        # Test initialization of TwitterPost
        twitter_post = TwitterPost()

        # Verify that the client was created with the correct parameters
        assert twitter_post.client is not None
        mock_client.assert_called_once()

    @patch("tweepy.Client")
    def test_post_success(self, mock_client):
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        # Create TwitterPost instance and post a message
        twitter_post = TwitterPost()
        result = twitter_post.post("Test tweet")

        # Returns a tweet ID (string) on success, not True
        assert result is not None
        mock_client_instance.create_tweet.assert_called_once_with(
            text="Test tweet", media_ids=None, in_reply_to_tweet_id=None
        )

    @patch("tweepy.Client")
    def test_post_failure(self, mock_client):
        # Setup mock to raise an exception
        mock_client_instance = MagicMock()
        mock_client_instance.create_tweet.side_effect = Exception("Twitter API error")
        mock_client.return_value = mock_client_instance

        # Create TwitterPost instance and post a message
        twitter_post = TwitterPost()
        result = twitter_post.post("Test tweet")

        # Verify the post failed but didn't raise an exception
        assert result is None
        mock_client_instance.create_tweet.assert_called_once_with(
            text="Test tweet", media_ids=None, in_reply_to_tweet_id=None
        )


class TestBlueSkyPost:
    def test_init(self):
        # Get the global mock from conftest.py
        with patch("nearquake.post_manager.Client") as mock_client:
            # Setup mock
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            # Create BlueSkyPost instance
            bluesky_post = BlueSkyPost()

            # Verify that the client was created and login was called
            assert bluesky_post.client is not None
            mock_client.assert_called_once()
            mock_client_instance.login.assert_called_once()

    def test_post_success(self):
        # Get the global mock from conftest.py
        with patch("nearquake.post_manager.Client") as mock_client:
            # Setup mock
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            # Create BlueSkyPost instance and post a message
            bluesky_post = BlueSkyPost()
            result = bluesky_post.post("Test post")

            # Verify the post was successful
            assert result is True
            mock_client_instance.send_post.assert_called_once_with(text="Test post")

    def test_post_failure(self):
        # Get the global mock from conftest.py
        with patch("nearquake.post_manager.Client") as mock_client:
            # Setup mock to raise an exception
            mock_client_instance = MagicMock()
            mock_client_instance.send_post.side_effect = Exception("BlueSky API error")
            mock_client.return_value = mock_client_instance

            # Create BlueSkyPost instance and post a message
            bluesky_post = BlueSkyPost()
            result = bluesky_post.post("Test post")

            # Verify the post failed but didn't raise an exception
            assert result is False
            mock_client_instance.send_post.assert_called_once_with(text="Test post")


def test_save_tweet_to_db_success():
    # Create mock database connection
    mock_conn = MagicMock()

    # Test saving a tweet to the database
    tweet_text = {"post": "Test tweet", "id_event": "test123", "post_type": "event"}
    result = save_tweet_to_db(tweet_text, mock_conn)

    # Verify the tweet was saved successfully
    assert result is True
    mock_conn.insert.assert_called_once()
    # Verify the correct model was used
    args, _ = mock_conn.insert.call_args
    assert isinstance(args[0], Post)


def test_save_tweet_to_db_failure():
    # Create mock database connection that raises an exception
    mock_conn = MagicMock()
    mock_conn.insert.side_effect = Exception("Database error")

    # Test saving a tweet to the database
    tweet_text = {"post": "Test tweet", "id_event": "test123", "post_type": "event"}
    result = save_tweet_to_db(tweet_text, mock_conn)

    # Verify the function handled the exception and returned False
    assert result is False
    mock_conn.insert.assert_called_once()


@patch("nearquake.post_manager._PLATFORM")
def test_post_to_all_platforms(mock_platform):
    mock_twitter = MagicMock(spec=TwitterPost)
    mock_bluesky = MagicMock(spec=BlueSkyPost)
    mock_platform.__iter__.return_value = [mock_twitter, mock_bluesky]

    post_to_all_platforms("Test message")

    mock_twitter.post.assert_called_once_with("Test message", None, None)
    mock_bluesky.post.assert_called_once_with("Test message", None)


@patch("nearquake.post_manager.post_to_all_platforms")
@patch("nearquake.post_manager.save_tweet_to_db")
def test_post_and_save_tweet(mock_save_tweet, mock_post_to_all_platforms):
    mock_conn = MagicMock()
    mock_post_to_all_platforms.return_value = {"twitter": "tweet_id_123"}

    tweet_text = {"post": "Test tweet", "id_event": "test123", "post_type": "event"}
    post_and_save_tweet(tweet_text, mock_conn)

    mock_post_to_all_platforms.assert_called_once_with(
        text="Test tweet", media_data=None, in_reply_to_tweet_id=None
    )
    mock_save_tweet.assert_called_once_with(tweet_text, mock_conn)


@patch("nearquake.post_manager.post_to_all_platforms")
@patch("nearquake.post_manager.save_tweet_to_db")
def test_post_and_save_tweet_skips_db_when_all_platforms_fail(
    mock_save_tweet, mock_post_to_all_platforms
):
    mock_conn = MagicMock()
    mock_post_to_all_platforms.return_value = {"twitter": None, "bluesky": False}

    tweet_text = {"post": "Test tweet", "id_event": "test123", "post_type": "event"}
    post_and_save_tweet(tweet_text, mock_conn)

    mock_post_to_all_platforms.assert_called_once_with(
        text="Test tweet", media_data=None, in_reply_to_tweet_id=None
    )
    mock_save_tweet.assert_not_called()
