import logging

import tweepy

from nearquake.config import TwitterAuth
from nearquake.app.db import Post


_logger = logging.getLogger(__name__)


class TweetOperator:
    """
    Class to perform operations on Twitter such as posting tweets.
    """

    def _auth(self) -> TwitterAuth:
        """
        Authenticate with Twitter API credentials.

        Returns:
            TwitterAuth: An object containing the authentication credentials.
        """
        auth = TwitterAuth()
        return auth

    def _connect(self) -> tweepy.client:
        """
        Create a Tweepy client using authenticated credentials.

        Returns:
            tweepy.Client: A Tweepy client object for interacting with Twitter API.
        """
        auth = self._auth()
        client = tweepy.Client(
            bearer_token=auth.BEARER_TOKEN,
            consumer_key=auth.CONSUMER_KEY,
            consumer_secret=auth.CONSUMER_SECRET,
            access_token=auth.ACCESS_TOKEN,
            access_token_secret=auth.ACCESS_TOKEN_SECRET,
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
