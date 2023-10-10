import os
import pandas as pd
from loguru import logger
from dotenv import load_dotenv
from pymongo import MongoClient, ReadPreference
import great_expectations as gx

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

# context = gx.get_context()


def check_comment_ip(target_collection: str):
    pipeline = [
        {"$match": {"article_data.comments.commenter_ip": None}},
        {"$unwind": "$article_data.comments"},
        {"$match": {"article_data.comments.commenter_ip": None}},
        {"$project": {"_id": 0, "article_url": 1, "article_data.comments": 1}},
    ]
    check_result = db[target_collection].aggregate(pipeline)

    return list(check_result)


def modify_commenter_ip(comments_incomplete: list[dict], target_collection: str):
    for comment in comments_incomplete:
        article_url = comment["article_url"]
        selection_criteria = {
            "commenter_id": comment["article_data"]["comments"]["commenter_id"],
        }

        db[target_collection].update_one(
            {
                "article_url": article_url,
                "article_data.comments.commenter_id": selection_criteria["commenter_id"],
                "article_data.comments.commenter_ip": None,
            },
            {"$set": {"article_data.comments.$.commenter_ip": "0.0.0.0"}},
        )


check_results = check_comment_ip(target_collection="gossip")

