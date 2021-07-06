import time
from airflow import DAG
from datetime import datetime

from airflow.operators.bash import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago

from datetime import timedelta
from models.quake_upload import load_recent_date
from models.tweeter import daily_tweet, post_tweet, weekly_top_tweet, weekly_quake_count
from models.utils import generate_recent_quakes, update_last_updated_date


default_args = {
    'owner': 'Anderson Nelson',
    'depends_on_past': False,
    'email': ['anderson.nelson1@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 1,
    'start_date': datetime.now(),
    'retry_delay': timedelta(minutes=5)
}


def run():
    load_recent_date(time='day')
    data = generate_recent_quakes()

    if len(data) > 0:
        for quake in data:
            quake_title = quake[1]
            quake_time = quake[2]

            post_tweet(daily_tweet(quake_title, quake_time))
            time.sleep(20)


with DAG(
    'Quake Post ',
    default_args=default_args,
    description='A bot to push tweet to twitter',
    schedule_interval=timedelta(minutes=5),
    tags=['example'],
) as dag:

    t1 = PythonOperator(
        task_id='print_the_context',
        python_callable=update_last_updated_date,
    )

    t2 = PythonOperator(
        task_id='print_the_context',
        python_callable=run,
    )

    t1 >> t2



