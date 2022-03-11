from airflow import DAG
from datetime import datetime

from airflow.operators.python_operator import PythonOperator

from datetime import timedelta
from nearquake import (
    daily_tweet,
    post_tweet,
    generate_recent_quakes,
    update_last_updated_date,
    load_recent_date,
    weekly_top_tweet, 
    weekly_quake_count
)


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


def fetchtweets():
    load_recent_date(time="day")
    data = generate_recent_quakes()

    if len(data) > 0:
        for quake in data:
            quake_title = quake[1]
            quake_time = quake[2]

            post_tweet(daily_tweet(quake_title, quake_time))


with DAG(
    "Daily_Quake_Post",
    default_args=default_args,
    description="A bot to push tweet to twitter",
    schedule_interval=timedelta(minutes=5),
    tags=["fetch"],
) as dag:

    t1 = PythonOperator(
        task_id="Update_database_to_last_post_date",
        python_callable=update_last_updated_date,
    )

    t2 = PythonOperator(task_id="Push_to_Twitter", python_callable=fetchtweets)

    t1 >> t2


with DAG(
    "Weekly_Quake_Post",
    default_args=default_args,
    description="A bot to push tweet to twitter",
    schedule_interval=timedelta(days=7),
) as dag:

    t1 = PythonOperator(
        task_id="weekly_top_tweet",
        python_callable=weekly_top_tweet,
    )

    t2 = PythonOperator(task_id="weekly_quake_count", python_callable=weekly_quake_count)

    t1 
    t2