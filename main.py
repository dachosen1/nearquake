from nearquake.data_processor import Earthquake
from nearquake.config import generate_time_period_url


if __name__ == "__main__":
    import argparse

    run = Earthquake()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--daily", action="store_true", help="Execute the daily program"
    )
    parser.add_argument(
        "-w", "--weekly", action="store_true", help="Execute the weekly program"
    )
    parser.add_argument(
        "-m", "--monthly", action="store_true", help="Execute the monthly program"
    )

    args = parser.parse_args()

    if args.daily:
        run.extract_data_properties(url=generate_time_period_url("day"))

    if args.weekly:
        run.extract_data_properties(url=generate_time_period_url("week"))

    if args.monthly:
        run.extract_data_properties(url=generate_time_period_url("month"))
