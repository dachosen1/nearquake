import tweepy
import logging
from datetime import datetime
from nearquake.config import TwitterAuth


_logger = logging.getLogger(__name__)


class TweetOperator:
    """
    Class to per form

    """

    def _auth(self):
        """_summary_

        :return: _description_
        """
        auth = TwitterAuth()
        return auth

    def _connect(self):
        auth = self._auth()
        client = tweepy.Client(
            bearer_token=auth.BEARER_TOKEN,
            consumer_key=auth.CONSUMER_KEY,
            consumer_secret=auth.CONSUMER_SECRET,
            access_token=auth.ACCESS_TOKEN,
            access_token_secret=auth.ACCESS_TOKEN_SECRET,
        )

        return client

    def post_tweet(self, tweet: str) -> None:
        """
        Post a tweet to twitter

        :param tweet: _description_
        """
        client = self._connect()

        try:
            client.create_tweet(text=tweet)
            _logger.info(f"Poster {tweet} to twitter at {datetime.now()}")
        except:
            _logger.info(f"Did not post {tweet}.")

    def tweet_image(self, file_path: str, tweet: str):
        """
        Post a tweet with an image to twitter

        :param file_path: file path where the image is saved
        :param tweet: content of the tweet to be posted

        """

        try:
            config = self._auth()

            auth = tweepy.OAuth2BearerHandler(config.BEARER_TOKEN)
            api = tweepy.API(auth)

            # Post the tweet with the image
            api.update_status_with_media(status=tweet, filename=file_path)
            _logger.info(f"Poster {tweet} to twitter at {datetime.now()}")

        except:
            _logger.info(f"Did not post {tweet}")
