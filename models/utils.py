from psycopg2 import sql

from models import connect_db
import logging
from datetime import date, datetime

_logger = logging.getLogger(__name__)


def get_last_updated_date():
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT  id, last_date, last_time FROM last_update ORDER BY  id DESC LIMIT 1;")
    cur.execute(query)
    query_results = cur.fetchall()

    try:
        last_update_date = query_results[0][1]
        last_update_time = query_results[0][2]

        _logger.info(f'The last check for eligible earthquake was made on {last_update_date} at {last_update_time}')

    except IndexError:
        today = date.today()
        time = datetime.now()

        last_update_date = today.strftime("%m/%d/%y")
        last_update_time = time.strftime("%H:%M:%S")

    return last_update_date, last_update_time


def generate_recent_quakes():
    last_date, last_time = get_last_updated_date()
    time_filter = f'{last_date} {last_time}'

    sql = f"SELECT mag, quake_type, time FROM properties" \
          f" WHERE time >= '{time_filter}' AND mag >= 5.0"

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
    _logger.info(f'Last Database update occured at {last_update}')
    return last_update


def update_last_updated_date():
    last_updated_date, last_updated_time = get_last_updated_date()

    last_update = fetch_last_update()
    last_date = last_update[0][0].strftime("%Y-%m-%d")
    last_time = last_update[0][0].strftime("%H:%M:%S")

    if last_updated_date == last_date and last_updated_time == last_time:
        _logger.info(f'No Date Change since last update')

    else:
        query = sql.SQL("INSERT INTO last_update VALUES (%s,%s)")

        conn = connect_db()
        cur = conn.cursor()
        cur.execute(query, (last_date, last_time,))
        conn.commit()
        _logger.info(f'Update: Checked Eligible Earthquake as of {last_date} on {last_time}')


def largest_quake(start, end):
    query = sql.SQL(f"SELECT mag, place, time FROM properties"
                    f"WHERE time::date BETWEEN '{start}' AND "
                    f"'{end}' AND mag > 1"
                    f" order by mag DESC "
                    f"LIMIT 1")

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(query)
    return cur.fetchall()


def count_quake(start, end):
    query = sql.SQL(f"SELECT count(*) FROM properties "
                    f"WHERE time::date BETWEEN '{start}' AND '{end}' AND mag > 5")

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(query)
    return cur.fetchall()
