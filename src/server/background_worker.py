import os
import json
import time
import pytz
import logging
import uvicorn
from loguru import logger
from fastapi import FastAPI
import google.cloud.logging
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from apscheduler.schedulers.background import BackgroundScheduler
from utils_dashboard.func_get_keyword_from_text import store_top_n_keywords
from utils_dashboard.utils_mongodb import (
    store_articles_count_sum,
    store_comments_count_sum,
    store_accounts_count_sum,
    store_past_n_days_article_title,
    store_past_n_days_comments,
)

app = FastAPI()
scheduler = BackgroundScheduler()
scheduler.start()

logger.add(
    sink="log/redis_update_{time}.log",
    rotation="00:00",
    retention="14 days",
    level="DEBUG",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} {function}() | {message}",
    enqueue=True,
    serialize=True,
    backtrace=True,
    diagnose=False,
)

load_dotenv(verbose=True)
key_content = json.loads(os.getenv("LOGGER_KEY"))
credentials = Credentials.from_service_account_info(key_content)

client = google.cloud.logging.Client(credentials=credentials)
client.setup_logging()
redis_update_crawled_data_logger = logging.getLogger("redis_update_crawled_data_logger")
redis_update_keyword_data_logger = logging.getLogger("redis_update_keyword_data_logger")


def update_overview_crawled_data():
    try:
        logger.opt(lazy=True, colors=True).info(
            f"<blue>Start - update overview crawled data</blue>"
        )
        start = time.time()
        store_articles_count_sum()
        logger.opt(lazy=True).info("Updated - articles count")
        store_comments_count_sum()
        logger.opt(lazy=True).info("Updated - comments count")
        store_accounts_count_sum()
        logger.opt(lazy=True).info("Updated - accounts count")
        end = time.time() - start
        logger.opt(lazy=True, colors=True).info(
            f"<blue>Finish - update overview crawled data (Time: {end})</blue>"
        )
        crawled_data_update_info = {"crawled_update_time": end}
        redis_update_crawled_data_logger.info(json.dumps(crawled_data_update_info))
    except Exception as e:
        logger.error(e)


def update_keywords_trends():
    try:
        logger.opt(lazy=True, colors=True).info(
            f"<blue>Start - update keywords trends</blue>"
        )
        start = time.time()
        store_past_n_days_article_title()
        logger.opt(lazy=True).info("Updated - past n days article title")
        store_past_n_days_comments()
        logger.opt(lazy=True).info("Updated - past n days article comments")
        store_top_n_keywords()
        logger.opt(lazy=True).info("Updated - trends of keywords")
        end = time.time() - start
        logger.opt(lazy=True, colors=True).info(
            f"<blue>Finish - update keywords trends (Time: {end})</blue>"
        )
        keyword_data_update_info = {"keyword_update_time": end}
        redis_update_keyword_data_logger.info(json.dumps(keyword_data_update_info))
    except Exception as e:
        logger.error(e)


scheduler.add_job(update_overview_crawled_data, "interval", seconds=120)
scheduler.add_job(
    update_keywords_trends,
    trigger="cron",
    hour="0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22",
    minute=0,
    timezone=pytz.timezone("Asia/Taipei"),
)


if __name__ == "__main__":
    uvicorn.run(app, port=8001, host="0.0.0.0")
