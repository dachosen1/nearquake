import logging

import tweepy

from nearquake.app.db import Post
from nearquake.config import TWITTER_AUTHENTICATION

_logger = logging.getLogger(__name__)


class TweetOperator:
    """
    Class to perform operations on Twitter such as posting tweets.
    """

    def _tweepy_connect(self) -> tweepy.client:
        """
        Initialize a Tweepy client using authenticated credentials.

        """

        client = tweepy.Client(
            bearer_token=TWITTER_AUTHENTICATION["BEARER_TOKEN"],
            consumer_key=TWITTER_AUTHENTICATION["CONSUMER_KEY"],
            consumer_secret=TWITTER_AUTHENTICATION["CONSUMER_SECRET"],
            access_token=TWITTER_AUTHENTICATION["ACCESS_TOKEN"],
            access_token_secret=TWITTER_AUTHENTICATION["ACCESS_TOKEN_SECRET"],
        )

        self.client = client

    def post_tweet(self, tweet_text: dict) -> None:
        """
        Post a tweet to twitter
        :param tweet_text: The content of the tweet to be posted.
        """

        try:
            self.client.create_tweet(text=tweet_text.get("post"))
            _logger.info(f"Latest post to twitter {tweet_text}")
        except Exception as e:
            _logger.error(f"Did not post {tweet_text}. {e} ")

    def save_tweet_to_db(self, tweet_text: dict, conn) -> None:
        """
        Save the posted tweet data into the database.
        :param tweet_data: The content of the tweet to be saved.
        :param conn: Database connection object.
        """
        try:
            conn.insert(Post(**tweet_text))
            _logger.info(f"Tweet saved to database: {tweet_text}")
        except Exception as e:
            _logger.error(f"Failed to save tweet to database {tweet_text}. Error: {e}")
            raise

    def run_tweet_operator(self, tweet_text: dict, conn) -> None:
        """
        Execute the tweet posting and saving operation.

        :param tweet_text: A dictionary containing the tweet data to be posted and saved.
        :param conn: A database connection object used to insert the tweet data into the database.
        """
        self.post_tweet(tweet_text=tweet_text)
        self.save_tweet_to_db(tweet_text=tweet_text, conn=conn)
