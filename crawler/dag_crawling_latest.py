import os
from dotenv import load_dotenv
from airflow.decorators import dag
from datetime import datetime, timedelta
from pymongo.mongo_client import MongoClient
from crawl_ptt_gossip import crawl_articles, parse_article
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

load_dotenv(verbose=True)

default_args = {
    'owner': 'Raymond',
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}


uri = os.getenv("ATLAS_URI", "None")

client = MongoClient(uri)
db = client.ptt


def crawl_ptt_latest_gossip():
    base_url = "https://www.ptt.cc/bbs/Gossiping/index.html"
    ptt_board = "gossip" if "Gossiping" in base_url else "politics"
    for i in range(0, 4):
        crawl_results = crawl_articles(base_url, i, 1)
        if crawl_results:
            collection = db[ptt_board]
            collection.insert_many(crawl_results)


# Reference: https://docs.astronomer.io/learn/airflow-passing-data-between-tasks
@dag(tags=['crawler-task-latest-gossip'], default_args=default_args, catchup=False,
     dag_id="crawler_task_latest_gossip",
     schedule_interval=timedelta(minutes=10))
def dag_ptt_latest_gossip():
    start_task = EmptyOperator(task_id="start_task")
    ptt_latest_gossip = PythonOperator(task_id="crawl_ptt_gossip", python_callable=crawl_ptt_latest_gossip)
    end_task = EmptyOperator(task_id="end_task")
    start_task >> ptt_latest_gossip >> end_task


dag_ptt_latest_gossip()
