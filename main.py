from nearquake.data_processor import Earthquake
from nearquake.config import generate_time_period_url


def daily_fetch():
    test = Earthquake()
    test.backfill_data_properties(start_date='2020-01-01', end_date='2023-12-01')


if __name__ == "__main__":
    daily_fetch()
