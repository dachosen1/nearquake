from dagster import job, ScheduleDefinition, schedule


from nearquake.data_processor import Earthquake
from nearquake.config import generate_time_period_url


@job
def daily_fetch(): 
    test = Earthquake()
    test.extract_data_properties(generate_time_period_url("day")) 

# my_schedule = ScheduleDefinition(
#     job=daily_fetch, cron_schedule="*/30 * * * *"
# )


@schedule(cron_schedule="*/30 * * * *", job=daily_fetch, execution_timezone="US/Central")
def my_schedule(_context):
    return {}