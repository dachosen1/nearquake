from nearquake.data_processor import Earthquake
from nearquake.config import generate_time_period_url


def daily_fetch():
    test = Earthquake()
    test.extract_data_properties(generate_time_period_url("day"))


if __name__ == "__main__":
    daily_fetch()
