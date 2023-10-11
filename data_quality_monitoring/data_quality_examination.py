import os
import json
import pprint
import logging
import pandas as pd
from loguru import logger
import google.cloud.logging
from dotenv import load_dotenv
from pymongo import MongoClient, ReadPreference
from google.oauth2.service_account import Credentials

load_dotenv(verbose=True)

mongo_client = MongoClient(
    os.getenv("ATLAS_URI", "None"), read_preference=ReadPreference.SECONDARY
)
db = mongo_client.ptt
gossips = db.gossip

# logger.add(
#     level="DEBUG",
#     format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} {function}() | {message}",
#     enqueue=True,
#     serialize=True,
#     backtrace=True,
#     diagnose=True
# )

key_content = json.loads(os.getenv("LOGGER_KEY"))
credentials = Credentials.from_service_account_info(key_content)
client = google.cloud.logging.Client(credentials=credentials)
client.setup_logging()

logger_null_time = logging.getLogger("logger_null_time")


def check_comment_ip(target_collection: str) -> list[dict]:
    pipeline = [
        {"$match": {"article_data.comments.commenter_ip": None}},
        {"$unwind": "$article_data.comments"},
        {"$match": {"article_data.comments.commenter_ip": None}},
        {"$project": {"_id": 0, "article_url": 1, "article_data.comments": 1}},
    ]
    return list(db[target_collection].aggregate(pipeline))


def modify_commenter_ip(comments_incomplete: list[dict], target_collection: str):
    for comment in comments_incomplete:
        article_url = comment["article_url"]
        selection_criteria = {
            "commenter_id": comment["article_data"]["comments"]["commenter_id"],
        }

        db[target_collection].update_one(
            {
                "article_url": article_url,
                "article_data.comments.commenter_id": selection_criteria[
                    "commenter_id"
                ],
                "article_data.comments.commenter_ip": None,
            },
            {"$set": {"article_data.comments.$.commenter_ip": "0.0.0.0"}},
        )


def find_null_comment_time(target_collection: str) -> list[dict]:
    """
    return comments whose comment time is null
    :param target_collection: target collection
    """
    pipeline = [
        {"$match": {"article_data.comments.comment_time": None}},
        {"$unwind": "$article_data.comments"},
        {"$match": {"article_data.comments.comment_time": None}},
        {"$project": {"_id": 0, "article_url": 1, "article_data.comments": 1}},
    ]
    return list(db[target_collection].aggregate(pipeline))


# check_results = check_comment_ip(target_collection="gossip")
# print(check_results)


def find_null_commenter_ip(target_collection: str) -> list[dict]:
    """
    return comments whose commenter ip is null
    :param target_collection: target collection
    """
    pipeline = [
        {"$match": {"article_data.comments.commenter_ip": None}},
        {"$unwind": "$article_data.comments"},
        {"$match": {"article_data.comments.commenter_ip": None}},
        {"$project": {"_id": 0, "article_url": 1, "article_data.comments": 1}},
    ]
    return list(db[target_collection].aggregate(pipeline))


def find_null_comment_content(target_collection: str) -> list[dict]:
    """
    return comments whose comment content is null
    :param target_collection: target collection
    """
    pipeline = [
        {"$match": {"article_data.comments.comment_content": None}},
        {"$unwind": "$article_data.comments"},
        {"$match": {"article_data.comments.comment_content": None}},
        {"$project": {"_id": 0, "article_url": 1, "article_data.comments": 1}},
    ]
    return list(db[target_collection].aggregate(pipeline))


def find_crawling_time_earlier_published_time(target_collection: str) -> list[dict]:
    """
    return articles whose crawling time is earlier than published time
    :param target_collection: target collection
    """
    return list(
        db[target_collection].find(
            {"article_data.last_crawled_datetime": {"$lt": "$article_data.time"}},
            {"_id": 0, "article_url": 1, "article_data": 1},
        )
    )


null_time_results = {
    "gossips": find_null_comment_time(target_collection="gossip"),
    "politic": find_null_comment_time(target_collection="politics"),
}

null_ips_results = {
    "gossips": find_null_commenter_ip(target_collection="gossip"),
    "politic": find_null_commenter_ip(target_collection="politics"),
}

null_comments_results = {
    "gossips": find_null_comment_content(target_collection="gossip"),
    "politic": find_null_comment_content(target_collection="politics"),
}

wrong_time_results = {
    "gossips": find_crawling_time_earlier_published_time(target_collection="gossip"),
    "politic": find_crawling_time_earlier_published_time(target_collection="politics"),
}

pprint.pprint(wrong_time_results)
