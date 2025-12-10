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

    def post(self, post_text: str, media_data: bytes = None, in_reply_to_tweet_id: str = None):
        """
        Post a tweet, optionally as a reply to another tweet.

        :param post_text: The text content of the tweet
        :param media_data: Optional image data to attach
        :param in_reply_to_tweet_id: Optional tweet ID to reply to (for threading)
        :return: Tweet ID if successful, None otherwise
        """
        try:
            media_ids = []
            if media_data:
                # Upload media using API v1.1
                media_file = BytesIO(media_data)
                media = self.api.media_upload(filename="earthquake.png", file=media_file)
                media_ids = [media.media_id]
                log_info(_logger, f"Successfully uploaded media: {media.media_id}")

            # Create tweet with media using API v2
            response = self.client.create_tweet(
                text=post_text,
                media_ids=media_ids if media_ids else None,
                in_reply_to_tweet_id=in_reply_to_tweet_id,
            )
            tweet_id = response.data["id"]
            log_info(_logger, f"Successfully posted to Twitter: {post_text}")
            return tweet_id
        except tweepy.TooManyRequests as e:
            # Log detailed rate limit information
            from datetime import datetime

            log_error(_logger, "=" * 80)
            log_error(_logger, "TWITTER RATE LIMIT EXCEEDED")
            log_error(_logger, "=" * 80)
            log_error(_logger, f"Attempted to post: {post_text[:100]}...")
            log_error(_logger, f"Media attached: {'Yes' if media_data else 'No'}")
            log_error(_logger, f"Reply to tweet: {'Yes' if in_reply_to_tweet_id else 'No'}")

            if hasattr(e, 'response') and e.response and hasattr(e.response, 'headers'):
                headers = e.response.headers
                limit = headers.get('x-rate-limit-limit', 'Unknown')
                remaining = headers.get('x-rate-limit-remaining', 'Unknown')
                reset_timestamp = headers.get('x-rate-limit-reset', None)

                log_error(_logger, f"\nRate Limit Details:")
                log_error(_logger, f"  • Total allowed: {limit} requests")
                log_error(_logger, f"  • Remaining: {remaining} requests")

                if reset_timestamp:
                    try:
                        reset_time = datetime.fromtimestamp(int(reset_timestamp))
                        now = datetime.now()
                        time_until_reset = reset_time - now
                        minutes = int(time_until_reset.total_seconds() / 60)
                        log_error(_logger, f"  • Resets at: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        log_error(_logger, f"  • Time until reset: {minutes} minutes")
                    except (ValueError, TypeError):
                        log_error(_logger, f"  • Reset timestamp: {reset_timestamp}")
            else:
                log_error(_logger, "\nRate limit details not available in response headers")

            log_error(_logger, "\nTroubleshooting:")
            log_error(_logger, "  1. Check your Twitter API tier at: https://developer.twitter.com/en/portal/dashboard")
            log_error(_logger, "  2. Free tier: 1,500 tweets/month | Basic tier: 3,000 tweets/month")
            log_error(_logger, "  3. Verify monthly usage hasn't been exceeded")
            log_error(_logger, "  4. Check if app is active and not suspended")
            log_error(_logger, "=" * 80)
            return None
        except Exception as e:
            log_error(_logger, f"Failed to post to Twitter: {post_text}", exc=e)
            return None


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


def post_to_all_platforms(text: str, media_data: bytes = None, in_reply_to_tweet_id: str = None) -> dict:
    """
    Post to all platforms and return tweet IDs.

    :param text: Tweet text
    :param media_data: Optional image data
    :param in_reply_to_tweet_id: Optional tweet ID to reply to
    :return: Dictionary with platform names and their tweet IDs
    """
    results = {}
    for platform in _PLATFORM:
        if isinstance(platform, TwitterPost):
            tweet_id = platform.post(text, media_data, in_reply_to_tweet_id)
            results["twitter"] = tweet_id
        else:
            # Bluesky doesn't support threading yet
            platform.post(text, media_data)
    return results


def post_and_save_tweet(text: dict, conn, media_data: bytes = None, in_reply_to_tweet_id: str = None) -> dict:
    """
    Post tweet to all platforms and save to database

    :param text: Tweet content dictionary
    :param conn: Database connection
    :param media_data: Optional image data as bytes
    :param in_reply_to_tweet_id: Optional tweet ID to reply to
    :return: Dictionary with platform tweet IDs
    """
    results = post_to_all_platforms(text=text.get("post"), media_data=media_data, in_reply_to_tweet_id=in_reply_to_tweet_id)
    save_tweet_to_db(text, conn)
    return results
