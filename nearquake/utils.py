import logging
import os
from datetime import date, datetime, timedelta
from psycopg2 import connect, sql
import tweepy

_logger = logging.getLogger(__name__)


def connect_db():
    conn = connect(
        host=os.getenv("NEARQUAKE_HOST"),
        user=os.getenv("NEARQUAKE_USERNAME"),
        password=os.getenv("NEARQUAKE_PASSWORD"),
        dbname=os.getenv("NEARQUAKE_DATABASE"),
    )
    return conn


def get_last_updated_date():
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL(
        "SELECT  id, last_date, last_time FROM last_update ORDER BY  id DESC LIMIT 1;"
    )
    cur.execute(query)
    query_results = cur.fetchall()
    try:
        last_update_date = query_results[0][1]
        last_update_time = query_results[0][2]

        _logger.info(
            f"The last check for eligible earthquake was made on {last_update_date} at {last_update_time}"
        )

    except IndexError:
        today = date.today()
        time = datetime.now()

        last_update_date = today.strftime("%m/%d/%y")
        last_update_time = time.strftime("%H:%M:%S")

    return last_update_date, last_update_time


def generate_recent_quakes():
    last_date, last_time = get_last_updated_date()
    time_filter = f"{last_date} {last_time}"

    sql = (
        f"SELECT mag, quake_type, time FROM properties"
        f" WHERE time >= '{time_filter}' AND mag >= 5.0"
    )

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(sql)
    sql_data = cur.fetchall()

    return sql_data


def fetch_last_update():
    query = sql.SQL("SELECT max(time) FROM properties")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(query)
    last_update = cur.fetchall()
    _logger.info(f"Last Database update occured at {last_update}")
    return last_update


def update_last_updated_date():
    last_updated_date, last_updated_time = get_last_updated_date()

    last_update = fetch_last_update()
    last_date = last_update[0][0].strftime("%Y-%m-%d")
    last_time = last_update[0][0].strftime("%H:%M:%S")

    if last_updated_date == last_date and last_updated_time == last_time:
        _logger.info(f"No Date Change since last update")

    else:
        query = sql.SQL("INSERT INTO last_update VALUES (%s,%s)")

        conn = connect_db()
        cur = conn.cursor()
        cur.execute(
            query,
            (
                last_date,
                last_time,
            ),
        )
        conn.commit()
        _logger.info(
            f"Update: Checked Eligible Earthquake as of {last_date} on {last_time}"
        )


def largest_quake(start, end):
    query = sql.SQL(
        f"SELECT mag, place, time FROM properties"
        f"WHERE time::date BETWEEN '{start}' AND "
        f"'{end}' AND mag > 1"
        f" order by mag DESC "
        f"LIMIT 1"
    )

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(query)
    return cur.fetchall()


def count_quake(start, end):
    query = sql.SQL(
        f"SELECT count(*) FROM properties WHERE time::date BETWEEN '{start}' AND '{end}' AND mag > 5"
    )

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(query)
    return cur.fetchall()


auth = tweepy.OAuthHandler(os.getenv("CONSUMER_KEY"), os.getenv("CONSUMER_SECRET"))
auth.set_access_token(os.getenv("ACCESS_TOKEN"), os.getenv("ACCESS_TOKEN_SECRET"))

# Create API object
api = tweepy.API(auth)


def _start_week():
    return datetime.now().date() - timedelta(days=7)


def post_tweet(tweet):
    try:
        api.update_status(tweet)
        logging.info(f"Poster {tweet} to twitter at {datetime.now()}")
    except:
        logging.info(f"Did not post {tweet}. Duplicate Message ")


def daily_tweet(quake_title, time):
    duration = datetime.now() - time
    return f"Recent #EarthQuake: {quake_title} reported {duration.seconds/60:.0f} minutes ago "


def weekly_top_tweet():
    start_week = _start_week()
    mag_week, location_week, time_week = largest_quake(
        start=start_week, end=datetime.now().date()
    )[0]

    start_month = datetime.today().replace(day=1).date().strftime("%Y/%m/%d")
    mag_month, location_month, time_month = largest_quake(
        start=start_month, end=datetime.now().date()
    )[0]

    ytd = datetime.today().replace(day=1, month=1).date()
    mag_ytd, location_ytd, time_ytd = largest_quake(
        start=ytd, end=datetime.now().date()
    )[0]

    tweet = f"Largest Quakes\nWeek = Mag: {mag_week}, location: {location_week} on {time_week.date()}\n Month = Mag: {mag_month}, location: {location_month} on {time_month.date()} \n YTD = Mag: {mag_ytd}, location: {location_ytd} on {time_ytd.date()}"
    post_tweet(tweet)
    return "Done"


def weekly_quake_count():
    start_week = _start_week()
    count_week = count_quake(start=start_week, end=datetime.now().date())[0]

    start_month = datetime.today().replace(day=1).date().strftime("%Y/%m/%d")
    count_month = count_quake(start=start_month, end=datetime.now().date())[0]

    ytd = datetime.today().replace(day=1, month=1).date()
    count_ytd = count_quake(start=ytd, end=datetime.now().date())[0]
    tweet = f"--------- Total Earthquakes Greater than 5.0 ---------\nWeek = Count: {count_week[0]} \nMonth = Count {count_month[0]} \nYTD = Count: {count_ytd[0]} \n #earthquake"
    return post_tweet(tweet)
