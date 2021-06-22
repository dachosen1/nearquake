import logging
from datetime import datetime, timedelta

import tweepy
from tweepy import TweepError

from models import CONSUMER_SECRET, CONSUMER_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
from models.utils import largest_quake, count_quake

_logger = logging.getLogger(__name__)

# Authenticate to Twitter
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# Create API object
api = tweepy.API(auth)


def _start_week():
    return datetime.now().date() - timedelta(days=7)


def post_tweet(tweet):
    try:
        api.update_status(tweet)
        logging.info(f'Poster {tweet} to twitter at {datetime.now()}')
    except TweepError:
        logging.info(f'Did not post {tweet}. Duplicate Message ')


def daily_tweet(quake_title, time):
    duration = datetime.now() - time
    return f'Recent #EarthQuake: {quake_title} reported {duration.seconds/60} minutes ago '


def weekly_top_tweet():
    start_week = _start_week()
    mag_week, location_week, time_week = largest_quake(start=start_week, end=datetime.now().date())[0]

    start_month = datetime.today().replace(day=1).date().strftime('%Y/%m/%d')
    mag_month, location_month, time_month = largest_quake(start=start_month, end=datetime.now().date())[0]

    ytd = datetime.today().replace(day=1, month=1).date()
    mag_ytd, location_ytd, time_ytd = largest_quake(start=ytd, end=datetime.now().date())[0]

    return f"Largest Quakes\nWeek = Mag: {mag_week}, location: " \
           f"{location_week} on {time_week.date()}" \
           f"\nMonth = Mag: {mag_month}, location: {location_month} on {time_month.date()}" \
           f"\nYTD = Mag: {mag_ytd}, location: {location_ytd} on {time_ytd.date()}"


def weekly_quake_count():
    start_week = _start_week()
    count_week = count_quake(start=start_week, end=datetime.now().date())[0]

    start_month = datetime.today().replace(day=1).date().strftime('%Y/%m/%d')
    count_month = count_quake(start=start_month, end=datetime.now().date())[0]

    ytd = datetime.today().replace(day=1, month=1).date()
    count_ytd = count_quake(start=ytd, end=datetime.now().date())[0]

    return f"--------- Total Earthquakes Greater than 5.0 ---------\nWeek = Count: {count_week[0]}" \
           f"\nMonth = Count {count_month[0]}" \
           f"\nYTD = Count: {count_ytd[0]} \n #earthquake"
