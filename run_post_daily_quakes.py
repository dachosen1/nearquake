import time

from models.tweeter import daily_tweet, post_tweet
from models.utils import generate_recent_quakes, update_last_updated_date

if __name__ == '__main__':

    data = generate_recent_quakes()

    for quake in data:
        quake_mag = float(quake[0])
        quake_location = quake[1]
        quake_time = quake[2].strftime("%H:%m:%S")

        post_tweet(daily_tweet(quake_mag, quake_location, quake_time))
        time.sleep(60)

    update_last_updated_date()
