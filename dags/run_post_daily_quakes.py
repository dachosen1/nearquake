from airflow import DAG
from datetime import datetime

from airflow.operators.python import PythonOperator

from datetime import timedelta
from nearquake.data_processor import Earthquake
from nearquake.config import generate_time_period_url


default_args = {
    "owner": "Anderson Nelson",
    "depends_on_past": False,
    "email": ["anderson.nelson1@gmail.com"],
    "email_on_failure": True,
    "email_on_retry": True,
    "retries": 1,
    "start_date": datetime.now(),
    "retry_delay": timedelta(minutes=5),
}


def daily_fetch(): 
    test = Earthquake()
    test.extract_data_properties(generate_time_period_url("day")) 


with DAG(
    "Daily_Quake_Post",
    default_args=default_args,
    description="A bot to push tweet to twitter",
    schedule_interval=timedelta(minutes=5),
    tags=["fetch"],
) as dag:
    t1 = PythonOperator(
        task_id="Update_database_to_last_post_date",
        python_callable=daily_fetch,
    )

    t1