# import concurrent.futures
# import json
# import logging
# import os
# from datetime import datetime, timedelta

# import requests
# from psycopg2 import sql
# from psycopg2 import connect
# from tqdm import tqdm


# _logger = logging.getLogger(__name__)


# def connect_db():
#     conn = connect(
#         host=os.getenv("NEARQUAKE_HOST"),
#         user=os.getenv("NEARQUAKE_USERNAME"),
#         password=os.getenv("NEARQUAKE_PASSWORD"),
#         dbname=os.getenv("NEARQUAKE_DATABASE"),
#     )
#     return conn


# conn = connect_db()


# def count_database_rows():
#     """
#     :return:
#     """
#     conn = connect_db()
#     with conn:
#         cur = conn.cursor()
#         sql = "select count(ids) from properties"
#         cur.execute(sql)
#         count_row = cur.fetchall()
#         count_row = list(map(list, count_row))
#         return count_row[0]


# def save_to_database_properties(
#     mag,
#     place,
#     time,
#     updated,
#     tz,
#     felt,
#     cdi,
#     mmi,
#     alert,
#     status,
#     tsunami,
#     sig,
#     net,
#     code,
#     ids,
#     source,
#     types,
#     nst,
#     dmin,
#     rms,
#     gap,
#     magType,
#     quake_type,
#     quake_title,
# ):
#     cur = conn.cursor()
#     query = "select ids from properties"
#     cur.execute(query)
#     all_id = cur.fetchall()
#     all_id = list(map(list, all_id))
#     eval_id = [ids]
#     if eval_id in all_id:
#         pass
#     else:
#         query = sql.SQL(
#             "insert into properties values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"
#             "%s) "
#         )

#         cur.execute(
#             query,
#             (
#                 mag,
#                 place,
#                 time,
#                 updated,
#                 tz,
#                 felt,
#                 cdi,
#                 mmi,
#                 alert,
#                 status,
#                 tsunami,
#                 sig,
#                 net,
#                 code,
#                 ids,
#                 source,
#                 types,
#                 nst,
#                 dmin,
#                 rms,
#                 gap,
#                 magType,
#                 quake_type,
#                 quake_title,
#             ),
#         )


# def save_to_database_coordinate(ids, longitude, latitude, depth):
#     cur = conn.cursor()
#     sql = "select ids from coordinate"
#     cur.execute(sql)
#     all_id = cur.fetchall()
#     all_id = list(map(list, all_id))
#     eval_id = [ids]

#     if eval_id in all_id:
#         pass
#     else:
#         sql = "insert into coordinate VALUES (%s,%s,%s,%s)"
#         cur.execute(sql, (ids, longitude, latitude, depth))


# class Earthquake:
#     def __init__(self):
#         self.initial_date = datetime(year=1970, month=1, day=1)
#         self.data = []
#         self.ids = []

#     def return_database_ids(self):
#         cur = conn.cursor()
#         sql = "select ids from properties"
#         cur.execute(sql)
#         quake_ids = cur.fetchall()
#         self.ids = quake_ids

#     def load_earthquake_data(self, url):
#         seq = requests.get(url)
#         seq.raise_for_status()
#         self.data = json.loads(seq.text)

#         _logger.info(
#             f"Successfully reached the quake API. Preparing to add {self.data['features']} quake"
#         )

#         for i in range(len(self.data["features"])):
#             self.add_features(i)

#         _logger.info(f"Done extracting new quakes")
#         # run_thread_pool(self.add_features, )

#     def add_features(self, index):
#         if self.data["features"][index]["id"] not in self.ids:
#             mag = self.data["features"][index]["properties"]["mag"]
#             place = self.data["features"][index]["properties"]["place"]
#             time_object_initial = timedelta(
#                 milliseconds=self.data["features"][index]["properties"]["time"]
#             )

#             eq_time = self.initial_date + time_object_initial
#             time_object_updated = timedelta(
#                 milliseconds=self.data["features"][index]["properties"]["updated"]
#             )
#             updated = self.initial_date + time_object_updated
#             tz = self.data["features"][index]["properties"]["tz"]
#             felt = self.data["features"][index]["properties"]["felt"]
#             cdi = self.data["features"][index]["properties"]["cdi"]
#             mmi = self.data["features"][index]["properties"]["mmi"]
#             alert = self.data["features"][index]["properties"]["alert"]
#             status = self.data["features"][index]["properties"]["status"]
#             tsunami = self.data["features"][index]["properties"]["tsunami"]
#             sig = self.data["features"][index]["properties"]["sig"]
#             net = self.data["features"][index]["properties"]["net"]
#             code = self.data["features"][index]["properties"]["code"]
#             ids = self.data["features"][index]["id"]
#             source = self.data["features"][index]["properties"]["sources"]
#             types = self.data["features"][index]["properties"]["types"]
#             nst = self.data["features"][index]["properties"]["nst"]
#             dmin = self.data["features"][index]["properties"]["dmin"]
#             rms = self.data["features"][index]["properties"]["rms"]
#             gap = self.data["features"][index]["properties"]["gap"]
#             magtype = self.data["features"][index]["properties"]["magType"]
#             quake_type = self.data["features"][index]["properties"]["type"]
#             quake_title = self.data["features"][index]["properties"]["title"]
#             longitude = self.data["features"][index]["geometry"]["coordinates"][0]
#             latitude = self.data["features"][index]["geometry"]["coordinates"][1]
#             depth = self.data["features"][index]["geometry"]["coordinates"][2]

#             save_to_database_properties(
#                 mag,
#                 place,
#                 eq_time,
#                 updated,
#                 tz,
#                 felt,
#                 cdi,
#                 mmi,
#                 alert,
#                 status,
#                 tsunami,
#                 sig,
#                 net,
#                 code,
#                 ids,
#                 source,
#                 types,
#                 nst,
#                 dmin,
#                 rms,
#                 gap,
#                 magtype,
#                 quake_type,
#                 quake_title,
#             )

#             save_to_database_coordinate(ids, longitude, latitude, depth)


# def run_thread_pool(function, my_iter):
#     with concurrent.futures.ProcessPoolExecutor() as executor:
#         executor.map(function, my_iter)


# def run_quake_url(url):
#     """
#     :param url:
#     :return:
#     """
#     count_ids = count_database_rows()
#     _logger.info(
#         f"Completed checking the status of the live database! Proceeding to add new eartquakes."
#     )
#     start = datetime.now()
#     run = Earthquake()
#     run.return_database_ids()
#     run.load_earthquake_data(url)
#     end = datetime.now()
#     duration = end - start
#     new_count_ids = count_database_rows()

#     msg = (
#         f"Duration: {duration.total_seconds()} seconds\n"
#         f""
#         f"Added {new_count_ids[0] - count_ids[0]} earthquakes\n"
#         f"-----------------------------------------------------"
#     )

#     _logger.info(msg)


# def load_custom_date_range(year, month):
#     """
#     :param year:
#     :param month:
#     :return:
#     """

#     all_url = f"https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?starttime={year}-{month}-01%2000:00:00&endtime={year}-{month}-31"
#     _logger.info(f"Database update complete for year {year} and month {month}")
#     run_quake_url(all_url)


# def load_recent_date(time):
#     """
#     :param time: ['day', 'week', 'month']
#     :return:
#     """

#     url = (
#         f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_{time}.geojson"
#     )
#     _logger.info(f"Database update started....")
#     run_quake_url(url)


# if __name__ == "__main__":
#     year_range = [i for i in range(1900, 2023)]
#     month_range = [i for i in range(1, 13)]

#     for year in tqdm(year_range):
#         for month in month_range:
#             load_custom_date_range(year, month)
