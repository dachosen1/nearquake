import logging

import tweepy

from nearquake.config import TWITTER_AUTHENTICATION
from nearquake.app.db import Post


_logger = logging.getLogger(__name__)


class TweetOperator:
    """
    Class to perform operations on Twitter such as posting tweets.
    """

    def _connect(self) -> tweepy.client:
        """
        Create a Tweepy client using authenticated credentials.

        Returns:
            tweepy.Client: A Tweepy client object for interacting with Twitter API.
        """

        client = tweepy.Client(
            bearer_token=TWITTER_AUTHENTICATION["BEARER_TOKEN"],
            consumer_key=TWITTER_AUTHENTICATION["CONSUMER_KEY"],
            consumer_secret=TWITTER_AUTHENTICATION["CONSUMER_SECRET"],
            access_token=TWITTER_AUTHENTICATION["ACCESS_TOKEN"],
            access_token_secret=TWITTER_AUTHENTICATION["ACCESS_TOKEN_SECRET"],
        )

        return client

    def post_tweet(self, item: dict, conn=None) -> None:
        """
        Post a tweet to twitter
        :param tweet: The content of the tweet to be posted.
        """
        client = self._connect()

        try:
            client.create_tweet(text=item.get("post"))
            conn.insert(Post(**item))
            _logger.info(f"Latest post to twitter {item}")
        except Exception as e:
            _logger.info(f"Did not post {item}.")
            return f"Error {e}"
