import time
from datetime import datetime, timedelta

import tweepy

from . import CONSUMER_SECRET, CONSUMER_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
from .utils import generate_recent_quakes, update_last_updated_date, largest_quake, count_quake

# Authenticate to Twitter
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# Create API object
api = tweepy.API(auth)


def post_tweet(tweet):
    try:
        api.update_status(tweet)
    except:
        return f'Tweet Error'


def daily_tweet(mag, place, time):
    tweet = f'{mag} Magnitude #earthquake reported {place} at {time} UTC'
    return post_tweet(tweet)


def weekly_large_tweet():
    start_week = datetime.now().date() - timedelta(days=7)
    mag_week, location_week, time_week = largest_quake(start=start_week, end=datetime.now().date())[0]

    start_month = datetime.today().replace(day=1).date().strftime('%Y/%m/%d')
    mag_month, location_month, time_month = largest_quake(start=start_month, end=datetime.now().date())[0]

    ytd = datetime.today().replace(day=1, month=1).date()
    mag_ytd, location_ytd, time_ytd = largest_quake(start=ytd, end=datetime.now().date())[0]

    tweet = f"Largest Quakes\nWeek = Mag: {mag_week}, location: " \
            f"{location_week} on {time_week.date()}" \
            f"\nMonth = Mag: {mag_month}, location: {location_month} on {time_month.date()}" \
            f"\nYTD = Mag: {mag_ytd}, location: {location_ytd} on {time_ytd.date()}"

    return post_tweet(tweet)


def weekly_quake_count():
    start_week = datetime.now().date() - timedelta(days=7)
    count_week = count_quake(start=start_week, end=datetime.now().date())[0]

    start_month = datetime.today().replace(day=1).date().strftime('%Y/%m/%d')
    count_month = count_quake(start=start_month, end=datetime.now().date())[0]

    ytd = datetime.today().replace(day=1, month=1).date()
    count_ytd = count_quake(start=ytd, end=datetime.now().date())[0]

    tweet = f"--------- Total Earthquakes Greater than 5.0 ---------\nWeek = Count: {count_week[0]}" \
            f"\nMonth = Count {count_month[0]}" \
            f"\nYTD = Count: {count_ytd[0]} \n #earthquake"

    return post_tweet(tweet)


def post_recent_quakes():
    data = generate_recent_quakes()

    for quake in data:
        quake_mag = float(quake[0])
        quake_location = quake[1]
        quake_time = quake[2].strftime("%H:%m:%S")

        post_tweet(daily_tweet(quake_mag, quake_location, quake_time))
        time.sleep(60)
    update_last_updated_date()
