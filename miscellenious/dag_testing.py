import os
from dotenv import load_dotenv
from airflow.decorators import dag
from datetime import datetime, timedelta
from pymongo.mongo_client import MongoClient
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

load_dotenv(verbose=True)

default_args = {
    "owner": "Raymond",
    "start_date": datetime(2023, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 5,
    "retry_delay": timedelta(minutes=1),
}


uri = os.getenv("ATLAS_URI", "None")

client = MongoClient(uri)
db = client.ptt


def hello_gossip():
    print("Hello, World!")


# Reference: https://docs.astronomer.io/learn/airflow-passing-data-between-tasks
@dag(
    tags=["hello-task"],
    default_args=default_args,
    catchup=False,
    dag_id="hello_task",
    schedule_interval=timedelta(minutes=3),
)
def calling():
    start_task = EmptyOperator(task_id="start_task")
    crawl_ptt = PythonOperator(task_id="hello_gossip", python_callable=hello_gossip)
    end_task = EmptyOperator(task_id="end_task")
    start_task >> crawl_ptt >> end_task


calling()
