from psycopg2 import sql

from . import connect_db


def get_last_updated_date():
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT  id, last_date, last_time FROM last_update ORDER BY  id DESC LIMIT 1;")
    cur.execute(query)
    query_results = cur.fetchall()
    last_update_date = query_results[0][1]
    last_update_time = query_results[0][2]

    return last_update_date, last_update_time


def generate_recent_quakes():
    last_date, last_time = get_last_updated_date()

    sql = f"SELECT mag, place, time FROM properties" \
          f" WHERE time::date >= '{last_date}' AND " \
          f"time::time >= '{last_time}' AND mag >= 5.0"

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
    return last_update


def update_last_updated_date():
    last_update = fetch_last_update()
    last_date = last_update[0][0].strftime("%Y-%m-%d")
    last_time = last_update[0][0].strftime("%H:%M:%S")
    query = sql.SQL("INSERT INTO last_update VALUES (%s,%s)")

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(query, (last_date, last_time,))
    conn.commit()


def largest_quake(start, end):

    query = sql.SQL(f"SELECT mag, place, time FROM properties "
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
