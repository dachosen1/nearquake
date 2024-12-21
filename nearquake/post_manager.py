import logging
from abc import ABC, abstractmethod


import tweepy
from atproto import Client

from nearquake.config import TWITTER_AUTHENTICATION, BLUESKY_PASSWORD, BLUESKY_USER_NAME

_logger = logging.getLogger(__name__)


class PlatformPoster(ABC):

    def __init__(self):
        self.client = None

    @abstractmethod
    def post(self, post_text):
        pass


class TwitterPost(PlatformPoster):
    def __init__(self):
        self.client = tweepy.Client(
            bearer_token=TWITTER_AUTHENTICATION["BEARER_TOKEN"],
            consumer_key=TWITTER_AUTHENTICATION["CONSUMER_KEY"],
            consumer_secret=TWITTER_AUTHENTICATION["CONSUMER_SECRET"],
            access_token=TWITTER_AUTHENTICATION["ACCESS_TOKEN"],
            access_token_secret=TWITTER_AUTHENTICATION["ACCESS_TOKEN_SECRET"],
        )

    def post(self, post_text: str) -> bool:
        try:
            self.client.create_tweet(text=post_text)
            _logger.info(f"Successfully posted {post_text}")
            return True

        except Exception as e:
            _logger.error(f"Failed to post {post_text}. Error: {e}")
            return False


class BlueSkyPost(PlatformPoster):
    def __init__(self):
        self.client = Client()
        self.client.login(BLUESKY_USER_NAME, BLUESKY_PASSWORD)

    def post(self, post_text: str) -> bool:
        try:
            self.client.create_tweet(text=post_text)
            return True

        except Exception as e:
            _logger.error(f"Failed to post {post_text}. Error: {e}")
            return False


def post_to_all_platforms(post_text: str) -> dict:

    platforms = [TwitterPost(), BlueSkyPost()]
    for platform in platforms:
        platform.post(post_text)


if __name__ == "__main__":
    post_to_all_platforms("Hello World")
