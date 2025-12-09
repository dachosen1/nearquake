import logging
from abc import ABC, abstractmethod
from io import BytesIO

import tweepy
from atproto import Client

from nearquake.app.db import Post
from nearquake.config import BLUESKY_PASSWORD, BLUESKY_USER_NAME, TWITTER_AUTHENTICATION
from nearquake.utils.logging_utils import (
    get_logger,
    log_db_operation,
    log_error,
    log_info,
)

_logger = get_logger(__name__)


class PlatformPoster(ABC):
    def __init__(self):
        self.client = None

    @abstractmethod
    def post(self, post_text, media_data=None):
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
        # Initialize API v1.1 for media uploads
        auth = tweepy.OAuth1UserHandler(
            TWITTER_AUTHENTICATION["CONSUMER_KEY"],
            TWITTER_AUTHENTICATION["CONSUMER_SECRET"],
            TWITTER_AUTHENTICATION["ACCESS_TOKEN"],
            TWITTER_AUTHENTICATION["ACCESS_TOKEN_SECRET"],
        )
        self.api = tweepy.API(auth)
        log_info(_logger, "Successfully authenticated with Twitter")

    def post(self, post_text: str, media_data: bytes = None) -> bool:
        try:
            media_ids = []
            if media_data:
                # Upload media using API v1.1
                media_file = BytesIO(media_data)
                media = self.api.media_upload(filename="earthquake.jpg", file=media_file)
                media_ids = [media.media_id]
                log_info(_logger, f"Successfully uploaded media: {media.media_id}")

            # Create tweet with media using API v2
            self.client.create_tweet(text=post_text, media_ids=media_ids if media_ids else None)
            log_info(_logger, f"Successfully posted to Twitter: {post_text}")
            return True
        except Exception as e:
            log_error(_logger, f"Failed to post to Twitter: {post_text}", exc=e)
            return False


class BlueSkyPost(PlatformPoster):
    def __init__(self):
        self.client = Client()
        self.client.login(BLUESKY_USER_NAME, BLUESKY_PASSWORD)
        log_info(_logger, "Successfully authenticated with BlueSky")

    def post(self, post_text: str, media_data: bytes = None) -> bool:
        try:
            self.client.send_post(text=post_text)
            log_info(_logger, f"Successfully posted to BlueSky: {post_text}")
            return True
        except Exception as e:
            log_error(_logger, f"Failed to post to BlueSky: {post_text}", exc=e)
            return False


def save_tweet_to_db(tweet_text: dict, conn) -> bool:
    """
    Save the posted tweet data into the database.
    :param tweet_data: The content of the tweet to be saved.
    :param conn: Database connection object.
    """
    try:
        conn.insert(Post(**tweet_text))
        log_db_operation(
            _logger,
            operation="INSERT",
            table="tweet.fct__post",
            details=f"Tweet saved: {tweet_text}",
            level=logging.INFO,
        )
        return True
    except Exception as e:
        log_error(_logger, f"Failed to save tweet to database {tweet_text}", exc=e)
        return False


_PLATFORM = [TwitterPost(), BlueSkyPost()]


def post_to_all_platforms(text: str, media_data: bytes = None) -> dict:
    for platform in _PLATFORM:
        platform.post(text, media_data)


def post_and_save_tweet(text: dict, conn, media_data: bytes = None) -> None:
    """
    Post tweet to all platforms and save to database

    :param text: Tweet content dictionary
    :param conn: Database connection
    :param media_data: Optional image data as bytes
    """
    post_to_all_platforms(text=text.get("post"), media_data=media_data)
    save_tweet_to_db(text, conn)
