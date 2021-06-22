import time
from datetime import datetime

from models.quake_upload import load_recent_date
from models.tweeter import daily_tweet, post_tweet, weekly_top_tweet, weekly_quake_count
from models.utils import generate_recent_quakes, update_last_updated_date

if __name__ == '__main__':

    WEEK_RUN = False

    while True:
        load_recent_date(time='day')
        data = generate_recent_quakes()

        if len(data) > 0:
            for quake in data:
                quake_mag = float(quake[0])
                quake_title = quake[1]
                quake_time = quake[2]

                post_tweet(daily_tweet(quake_title, quake_time))
                time.sleep(20)

            update_last_updated_date()
            time.sleep(300)

        if datetime.today().day == 1 and WEEK_RUN:
            post_tweet(weekly_top_tweet())
            post_tweet(weekly_quake_count())
            WEEK_RUN = False

        elif datetime.today().day > 1:
            WEEK_RUN = True
