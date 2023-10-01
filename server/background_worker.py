import time
import pytz
import logging
from fastapi import FastAPI
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from utils_dashboard.func_get_keyword_from_text import store_top_n_keywords
from utils_dashboard.utils_mongodb import (store_articles_count_sum,
                                           store_comments_count_sum,
                                           store_accounts_count_sum,
                                           store_past_n_days_article_title,
                                           store_past_n_days_comments)

app = FastAPI()
scheduler = BackgroundScheduler()
scheduler.start()


def update_overview_crawled_data():
    try:
        print(f"Start - update_overview_crawled_data")
        store_articles_count_sum()
        print("Updated overview crawled data - articles count")
        store_comments_count_sum()
        print("Updated overview crawled data - comments count")
        store_accounts_count_sum()
        print("Updated overview crawled data - accounts count")
    except Exception as e:
        print(e)


def update_keywords_trends():
    try:
        start = time.time()
        print(f"Start - update_keywords_trends")
        store_past_n_days_article_title()
        print("Updated overview past n days article title")
        store_past_n_days_comments()
        print("Updated overview pas n days article comments")
        store_top_n_keywords()
        print("Updated overview trends of keywords")
        print(f"Time: {time.time() - start}")
    except Exception as e:
        print(e)


scheduler.add_job(update_overview_crawled_data, "interval", seconds=60)
scheduler.add_job(
    update_keywords_trends,
    trigger="cron", hour=0, minute=0, timezone=pytz.timezone("Asia/Taipei"))
# scheduler.add_job(update_keywords_trends, "interval", seconds=60)
