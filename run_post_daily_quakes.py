import time
from models.quake_upload import load_recent_date
from models.tweeter import daily_tweet, post_tweet
from models.utils import generate_recent_quakes, update_last_updated_date

if __name__ == '__main__':

    while True:
        load_recent_date(time='day')
        data = generate_recent_quakes()

        for quake in data:
            quake_mag = float(quake[0])
            quake_location = quake[1]
            quake_time = quake[2].strftime("%H:%m:%S")

            post_tweet(daily_tweet(quake_mag, quake_location, quake_time))
            time.sleep(2)

        update_last_updated_date()

        time.sleep(300)
