from unittest.mock import patch, MagicMock

from nearquake.tweet_processor import TweetOperator


@patch("nearquake.tweet_processor.TwitterAuth")
@patch("nearquake.tweet_processor.tweepy.Client")
@patch("nearquake.tweet_processor._logger")
def test_post_tweet_failure(mock_logger, mock_client_class, mock_auth_class):
    mock_auth_instance = MagicMock()
    mock_auth_class.return_value = mock_auth_instance

    mock_client_instance = MagicMock()
    mock_client_class.return_value = mock_client_instance

    operator = TweetOperator()

    tweet = {"post": "Test tweet"}
    mock_create_tweet = MagicMock(side_effect=Exception("Failed to post tweet"))
    mock_client_instance.create_tweet = mock_create_tweet

    result = operator.post_tweet(tweet)

    assert result == "Error Failed to post tweet"
    mock_logger.info.assert_called_once_with(f"Did not post {tweet}.")
