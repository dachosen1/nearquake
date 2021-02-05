from datetime import timedelta

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago

from models.quake_upload import load_recent_date
from models.tweeter import post_recent_quakes, weekly_large_tweet, weekly_quake_count

default_args = {
    'owner': 'Anderson Nelson',
    'depends_on_past': False,
    'start_date': days_ago(2),
    'email': ['anderson.nelson1@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 5,
    'retry_delay': timedelta(minutes=5),
}

instant_dag = DAG(
    'instant_dag',
    default_args=default_args,
    description='A DAG to automatically schedule and publish earthquakes to Twitter',
    schedule_interval=timedelta(minutes=10)
)

weekly_dag = DAG(
    'weekly_dag',
    default_args=default_args,
    description='A DAG to automatically schedule and publish earthquakes to Twitter',
    schedule_interval=timedelta(days=7)
)

monthly_dag = DAG(
    'monthly_dag',
    default_args=default_args,
    description='A DAG to automatically schedule and publish earthquakes to Twitter',
    schedule_interval=timedelta(days=30)
)

tweet_latest_quakes = PythonOperator(
    task_id='Post_Recent_Quakes',
    python_callable=post_recent_quakes,
    dag=instant_dag
)

download_recent_quake_day = PythonOperator(
    task_id='Download_Recent_Quakes',
    python_callable=load_recent_date,
    op_kwargs={'time': 'day'},
    dag=instant_dag
)


download_recent_quake_week = PythonOperator(
    task_id='Download_Recent_Quakes',
    python_callable=load_recent_date,
    op_kwargs={'time': 'week'},
    dag=weekly_dag
)


download_recent_quake_month = PythonOperator(
    task_id='Download_Recent_Quakes',
    python_callable=load_recent_date,
    op_kwargs={'time': 'month'},
    dag=monthly_dag
)

post_large_earthquake_weekly = PythonOperator(
    task_id='Publish_Largest_Quake_For_The_Week',
    python_callable=weekly_large_tweet,
    dag=weekly_dag
)

post_earthquake_weekly_count = PythonOperator(
    task_id='Publish_Weekly_Earthquakes_Count',
    python_callable=weekly_quake_count,
    dag=weekly_dag
)

download_recent_quake_day.set_downstream(tweet_latest_quakes)
download_recent_quake_week.set_downstream([post_large_earthquake_weekly, post_earthquake_weekly_count])



