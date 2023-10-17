"""
This module contains utility functions for mongodb to analyze data and make graphs.
"""
import os
import pytz
import time
import json
import redis
import logging
import pandas as pd
from uuid import uuid4
from loguru import logger
import google.cloud.logging
from typing import Tuple, Any
from dotenv import load_dotenv
from .config_dashboard import db
from itertools import combinations
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from google.cloud.logging.handlers import CloudLoggingHandler

BATCH_SIZE = 10000
NUM_ARTICLES = 100

load_dotenv(verbose=True)
# key_content = json.loads(os.getenv("LOGGER_KEY"))
# credentials = Credentials.from_service_account_info(key_content)
#
# client = google.cloud.logging.Client(credentials=credentials)
# client.setup_logging()
# redis_connection_logger = logging.getLogger("redis_connection_logger")

current_timezone = pytz.timezone("Asia/Taipei")
current_time = datetime.now(current_timezone).replace(
    hour=0, minute=0, second=0, microsecond=0
)

redis_pool = redis.ConnectionPool(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=os.getenv("REDIS_PORT", 6379),
    db=os.getenv("REDIS_DB", 0),
    password=os.getenv("REDIS_PASSWORD", None),
    socket_timeout=10,
    socket_connect_timeout=10,
)
redis_conn = redis.StrictRedis(connection_pool=redis_pool, decode_responses=True)

# log_content = {
#         "redis_info": redis_conn.info(),
# }
# logger.info(json.dumps(log_content))
# logger.info(log_content)


# Section: overall information about crawling data (used in dashboard)
def count_articles(target_collection: str) -> int:
    """
    count number of articles in mongodb
    :param target_collection: target collection
    :return: number of articles
    """
    return db[target_collection].estimated_document_count({})


def store_articles_count_sum(max_retries: int = 5, delay: int = 2):
    """
    compute the total number of articles in mongodb and store it in Redis
    :param max_retries: maximum number of retries
    :param delay: delay between retries in seconds
    """
    total_articles = count_articles("gossip") + count_articles("politics")

    for trying in range(1, max_retries + 1):
        try:
            redis_conn.set("total_articles", total_articles)
            break
        except redis.exceptions as e:
            print(
                f"{e}: Failed to set value of article counts sum in Redis. "
                f"Attempt {trying + 1} of {max_retries}. Retrying in {delay} seconds."
            )
            if trying == max_retries:
                raise e(
                    f"Failed to set value of article counts sum in {max_retries} attempts"
                )
            time.sleep(delay)


def retrieve_articles_count_sum():
    """
    retrieve the total number of articles of mongodb from Redis
    """
    log_content = {
        "redis_info": redis_conn.info(),
    }
    logger.info(json.dumps(log_content))
    return json.loads(redis_conn.get("total_articles").decode("utf-8"))


def count_comments(target_collection: str) -> int:
    """
    count number of articles in mongodb
    :param target_collection: target collection
    :return: number of articles
    """
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_comments": {"$sum": "$article_data.num_of_comment"},
            }
        }
    ]

    result = list(db[target_collection].aggregate(pipeline))
    if result:
        return result[0]["total_comments"]
    return 0


def store_comments_count_sum(max_retries: int = 5, delay: int = 2):
    """
    compute the total number of comments in mongodb and store it in Redis
    :param max_retries: maximum number of retries
    :param delay: delay between retries in seconds
    """
    gossips_result = count_comments("gossip")
    politics_result = count_comments("politics")
    total_comments = gossips_result + politics_result

    for trying in range(1, max_retries + 1):
        try:
            redis_conn.set("total_comments", total_comments)
            break
        except redis.exceptions as e:
            print(
                f"{e}: Failed to set value of comments counts sum in Redis. "
                f"Attempt {trying + 1} of {max_retries}. Retrying in {delay} seconds."
            )
            if trying == max_retries:
                raise e(
                    f"Failed to set value of comments counts sum in {max_retries} attempts"
                )
            time.sleep(delay)


def retrieve_comments_count_sum():
    """
    retrieve the total number of comments of mongodb from Redis
    """
    return json.loads(redis_conn.get("total_comments").decode("utf-8"))


def count_accounts(target_collection: str) -> int:
    """
    count number of unique accounts in mongodb
    :param target_collection: target collection
    :return: number of articles
    """

    author_pipeline = [
        {
            "$group": {
                "_id": None,
                "unique_authors": {"$addToSet": "$article_data.author"},
            }
        }
    ]
    authors_result = list(db[target_collection].aggregate(author_pipeline))
    unique_authors = (
        set(authors_result[0]["unique_authors"]) if authors_result else set()
    )

    commenter_pipeline = [
        {"$unwind": "$article_data.comments"},
        {
            "$group": {
                "_id": None,
                "unique_commenters": {
                    "$addToSet": "$article_data.comments.commenter_id"
                },
            }
        },
    ]
    commenters_result = list(db[target_collection].aggregate(commenter_pipeline))
    unique_commenters = (
        set(commenters_result[0]["unique_commenters"]) if commenters_result else set()
    )
    all_unique_accounts = unique_authors.union(unique_commenters)
    return len(all_unique_accounts)


def store_accounts_count_sum(max_retries: int = 5, delay: int = 2):
    """
    compute the total number of accounts in mongodb and store it in Redis
    :param max_retries: maximum number of retries
    :param delay: delay between retries in seconds
    """
    total_accounts = count_accounts("gossip") + count_accounts("politics")
    for trying in range(1, max_retries + 1):
        try:
            redis_conn.set("total_accounts", total_accounts)
            break
        except redis.exceptions as e:
            print(
                f"{e}: Failed to set value of accounts counts sum in Redis. "
                f"Attempt {trying + 1} of {max_retries}. Retrying in {delay} seconds."
            )
            if trying == max_retries:
                raise e(
                    f"Failed to set value of accounts counts sum in {max_retries} attempts"
                )
            time.sleep(delay)


def retrieve_accounts_count_sum():
    """
    retrieve the total number of accounts of mongodb from Redis
    """
    return json.loads(redis_conn.get("total_accounts").decode("utf-8"))


# Section: operations about article
def get_top_n_breaking_news(target_collection: str, num_articles: int) -> list:
    """
    return top n breaking news defined by title including <爆卦>
    :param target_collection: target collection
    :param num_articles: number of articles
    """
    breaking_news = list(
        db[target_collection]
        .find(
            {"article_data.title": {"$regex": "爆卦", "$options": "i"}},
            {
                "article_data.title": 1,
                "article_data.author": 1,
                "article_data.num_of_comment": 1,
                "article_url": 1,
                "_id": 0,
            },
        )
        .sort("article_data.num_of_comment", -1)
        .limit(num_articles)
    )
    return breaking_news


def get_top_n_favored_articles(target_collection: str, num_articles: int) -> list:
    """
    return top n favored articles defined by <num of favor> subtracting <num of against> >= 100
    :param target_collection: target collection
    :param num_articles: number of articles
    """
    pipelines = [
        {
            "$project": {
                "_id": 0,
                "article_url": 1,
                "article_data.title": 1,
                "article_data.author": 1,
                "article_data.num_of_comment": 1,
                "favor_difference": {
                    "$subtract": [
                        "$article_data.num_of_favor",
                        "$article_data.num_of_against",
                    ]
                },
            }
        },
        {"$match": {"favor_difference": {"$gte": 100}}},
        {"$sort": {"favor_difference": -1}},
        {"$limit": num_articles},
    ]
    return list(db[target_collection].aggregate(pipelines))


def get_past_n_days_article_title(target_collection: str, n_days: int) -> list[dict]:
    """
    return article titles of the past n days
    :param target_collection: target collection
    :param n_days: number of days
    """
    n_days_ago_timestamp = int((current_time - timedelta(days=n_days)).timestamp())
    current_timestamp = int(current_time.timestamp())
    pipeline = [
        {
            "$match": {
                "article_data.time": {
                    "$gte": n_days_ago_timestamp,
                    "$lte": current_timestamp,
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "article_url": 1,
                "article_text": "$article_data.title",
            }
        },
    ]

    cursor = db[target_collection].aggregate(pipeline).batch_size(BATCH_SIZE)
    return list(cursor)


def store_past_n_days_article_title():
    collections = ["gossip", "gossip", "gossip", "politics", "politics", "politics"]
    past_n_days = [1, 3, 7, 1, 3, 7]
    for i in zip(collections, past_n_days):
        title_results = get_past_n_days_article_title(
            target_collection=i[0], n_days=i[1]
        )
        redis_conn.set(
            f"past_n_days_article_title_{i[0]}_{i[1]}", json.dumps(title_results)
        )


def retrieve_past_n_days_article_title(target_collection: str, n_days: int):
    return json.loads(
        redis_conn.get(
            f"past_n_days_article_title_{target_collection}_{n_days}"
        ).decode("utf-8")
    )


def get_past_n_days_comments(target_collection: str, n_days: int) -> list[dict]:
    """
    return the n days of comments
    :param target_collection: target collection
    :param n_days: number of days
    """
    n_days_ago_timestamp = int((current_time - timedelta(days=n_days)).timestamp())
    current_timestamp = int(current_time.timestamp())
    pipeline = [
        {
            "$match": {
                "article_data.time": {
                    "$gte": n_days_ago_timestamp,
                    "$lte": current_timestamp,
                }
            }
        },
        {"$project": {"_id": 0, "article_url": 1, "article_data.comments": 1}},
        {"$unwind": "$article_data.comments"},
        {
            "$project": {
                "_id": 0,
                "article_url": 1,
                "article_text": "$article_data.comments.comment_content",
            }
        },
    ]
    cursor = db[target_collection].aggregate(pipeline).batch_size(BATCH_SIZE)
    return list(cursor)


def store_past_n_days_comments():
    collections = ["gossip", "gossip", "gossip", "politics", "politics", "politics"]
    past_n_days = [1, 3, 7, 1, 3, 7]
    for i in zip(collections, past_n_days):
        comments_results = get_past_n_days_comments(target_collection=i[0], n_days=i[1])
        redis_conn.set(
            f"past_n_days_comments_{i[0]}_{i[1]}", json.dumps(comments_results)
        )


def retrieve_past_n_days_comments(target_collection: str, n_days: int):
    return json.loads(
        redis_conn.get(f"past_n_days_comments_{target_collection}_{n_days}").decode(
            "utf-8"
        )
    )


# Section: operations about accounts
def extract_all_articles_commenter_involved(
    target_collection: str, commenter_account: str
) -> list[dict]:
    """
    return all articles which have been commented by commenter in users' query
    :param target_collection: target collection
    :param commenter_account: account name of the commenter
    """
    cursor = (
        db[target_collection]
        .find(
            {"article_data.comments.commenter_id": commenter_account},
            {"_id": 0, "article_url": 1, "article_data.title": 1},
        )
        .batch_size(BATCH_SIZE)
    )
    articles_collection = []
    for article in cursor:
        articles_collection.append(
            {
                "article_url": article["article_url"],
                "article_title": article["article_data"]["title"],
            }
        )
    return articles_collection


def extract_top_n_articles_author_published(
    target_collection: str, author_account: str, num_articles: int
) -> list[dict]:
    pattern = "^" + author_account
    cursor = (
        db[target_collection]
        .find(
            {"article_data.author": {"$regex": pattern}},
            {"_id": 0, "article_url": 1, "article_data.title": 1},
        )
        .sort("article_data.num_of_comment", -1)
        .limit(num_articles)
    )
    articles_collection = []
    for article in cursor:
        articles_collection.append(
            {
                "article_url": article["article_url"],
                "article_title": article["article_data"]["title"],
            }
        )
    return articles_collection


def extract_top_n_articles_keyword_in_title(
    target_collection: str, keyword: str, num_articles: int
) -> list[dict]:
    cursor = (
        db[target_collection]
        .find(
            {"article_data.title": {"$regex": keyword, "$options": "i"}},
            {"_id": 0, "article_url": 1, "article_data.title": 1},
        )
        .sort("article_data.num_of_comment", -1)
        .limit(num_articles)
    )
    articles_collection = []
    for article in cursor:
        articles_collection.append(
            {
                "article_url": article["article_url"],
                "article_title": article["article_data"]["title"],
            }
        )
    return articles_collection


def extract_commenters_id_using_same_ipaddress(target_collection: str, ipaddress: str):
    pipeline = [
        {"$match": {"article_data.comments.commenter_ip": ipaddress}},
        {"$unwind": "$article_data.comments"},
        {"$match": {"article_data.comments.commenter_ip": ipaddress}},
        {"$project": {"commenter_id": "$article_data.comments.commenter_id", "_id": 0}},
        {"$group": {"_id": "$commenter_id", "ipaddress_usage_count": {"$sum": 1}}},
        {
            "$project": {
                "commenter_account": "$_id",
                "ipaddress_usage_count": 1,
                "_id": 0,
            }
        },
        {"$sort": {"ipaddress_usage_count": -1}},
    ]
    result = db[target_collection].aggregate(pipeline)
    return list(result)


# Section: operations to generate network graph
def extract_author_info_from_articles_title_having_keywords(
    target_collection: str, keyword: str, num_articles: int
) -> list[dict]:
    """
    return author_id and ipaddress of articles having keywords
    :param target_collection: target collection
    :param keyword: keyword
    :param num_articles: number of articles
    """
    cursor = (
        db[target_collection]
        .find(
            {"article_data.title": {"$regex": keyword, "$options": "i"}},
            {
                "_id": 0,
                "article_url": 1,
                "article_data.author": 1,
                "article_data.ipaddress": 1,
                "article_data.time": 1,
                "article_data.num_of_comment": 1,
            },
        )
        .sort("article_data.num_of_comment", -1)
        .limit(num_articles)
    )
    return list(cursor)


def extract_commenter_info_from_article_with_article_url(
    target_collection: str, article_data: dict
) -> list[dict]:
    """
    return commenter_id and ipaddress of article with article_url
    :param target_collection: target collection
    :param article_data: article data
    """
    article_published_time = article_data["article_data"]["time"]
    article_url = article_data["article_url"]
    pipeline = [
        {"$match": {"article_url": article_url}},
        {"$unwind": "$article_data.comments"},
        {
            "$addFields": {
                "time_difference": {
                    "$subtract": [
                        "$article_data.comments.comment_time",
                        article_published_time,
                    ]
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "article_data.article_url": 1,
                "article_data.comments": 1,
                "time_difference": 1,
            }
        },
    ]
    cursor = db[target_collection].aggregate(pipeline)
    return list(cursor)


def summarize_commenters_metadata(commenters_data: list, temp_dict: dict) -> dict:
    """
    summarize commenters metadata for network graph
    :param commenters_data: commenters data
    :param temp_dict: temp dict storing commenters info
    """
    for commenter in commenters_data:
        temp_dict[commenter.get("article_data").get("comments").get("commenter_id")][
            "freq"
        ] += 1

        comment_type = commenter.get("article_data").get("comments").get("comment_type")
        if comment_type == "推":
            temp_dict[
                commenter.get("article_data").get("comments").get("commenter_id")
            ]["agree"] += 1
        elif comment_type == "噓":
            temp_dict[
                commenter.get("article_data").get("comments").get("commenter_id")
            ]["disagree"] += 1
        else:
            temp_dict[
                commenter.get("article_data").get("comments").get("commenter_id")
            ]["reply"] += 1

        temp_dict[commenter.get("article_data").get("comments").get("commenter_id")][
            "time_total"
        ] += commenter.get("time_difference")

        temp_dict[commenter.get("article_data").get("comments").get("commenter_id")][
            "time_avg"
        ] = (
            temp_dict[
                commenter.get("article_data").get("comments").get("commenter_id")
            ]["time_total"]
            / temp_dict[
                commenter.get("article_data").get("comments").get("commenter_id")
            ]["freq"]
        )
    return temp_dict


def convert_commenters_metadata_to_dataframe(commenter_metadata: dict) -> pd.DataFrame:
    """
    convert commenters metadata to dataframe
    :param commenter_metadata: temp dict storing commenters info
    """
    data = []
    for commenter_id, stats in commenter_metadata.items():
        temp = stats.copy()
        temp["commenter_id"] = commenter_id
        data.append(temp)
    return pd.DataFrame(data)


def extract_top_freq_commenter_id(meta_df: pd.DataFrame, num_commenters: int) -> list:
    commenters_id = (
        meta_df.sort_values("freq", ascending=False)
        .head(num_commenters)["commenter_id"]
        .to_list()
    )
    commenters_freq = (
        meta_df.sort_values("freq", ascending=False)
        .head(num_commenters)["freq"]
        .to_list()
    )
    results = [
        f"{commenter_id} ({int(commenter_freq)} 次)"
        for commenter_id, commenter_freq in zip(commenters_id, commenters_freq)
    ]
    return results


def extract_top_agree_commenter_id(meta_df: pd.DataFrame, num_commenters: int) -> list:
    commenters_id = (
        meta_df.sort_values("agree", ascending=False)
        .head(num_commenters)["commenter_id"]
        .to_list()
    )
    commenters_freq = (
        meta_df.sort_values("agree", ascending=False)
        .head(num_commenters)["agree"]
        .to_list()
    )
    results = [
        f"{commenter_id} ({int(commenter_freq)} 次)"
        for commenter_id, commenter_freq in zip(commenters_id, commenters_freq)
    ]
    return results


def extract_top_disagree_commenter_id(
    meta_df: pd.DataFrame, num_commenters: int
) -> list:
    commenters_id = (
        meta_df.sort_values("disagree", ascending=False)
        .head(num_commenters)["commenter_id"]
        .to_list()
    )
    commenters_freq = (
        meta_df.sort_values("disagree", ascending=False)
        .head(num_commenters)["disagree"]
        .to_list()
    )
    results = [
        f"{commenter_id} ({int(commenter_freq)} 次)"
        for commenter_id, commenter_freq in zip(commenters_id, commenters_freq)
    ]
    return results


def extract_top_short_comment_latency_commenter_id(
    meta_df: pd.DataFrame, num_commenters: int
) -> list:
    return (
        meta_df.sort_values("time_avg", ascending=True)
        .head(num_commenters)["commenter_id"]
        .to_list()
    )


def check_commenter_in_article_filter_by_article_url(
    target_collection: str, commenter_id: str, article_url: str
) -> bool:
    query = {
        "article_url": article_url,
        "article_data.comments": {"$elemMatch": {"commenter_id": commenter_id}},
    }
    return db[target_collection].find_one(query) is not None


# Section: functions needed for network graph
# Rationale: (1) filter articles by keyword and sort by number of comments
# Rationale: (2) get top n commenters with 2 types of comments
# Rationale: (3) get all combinations of the top n commenters
# Rationale: (4) compute the concurrency of each combination -> divide by number of articles
# Rationale: (5) compute each commenter's response latency -> draw graph
def query_articles_store_temp_collection(
    keyword: str, target_collection: str
) -> Tuple[str, str, str]:
    if target_collection not in ["gossip", "politics"]:
        raise ValueError("Invalid target collection (only gossip, politics)")
    collection_name = f"concurrency_collection_{keyword}_{uuid4()}"
    pipeline = [
        {"$match": {"article_data.title": {"$regex": keyword, "$options": "i"}}},
        {"$sort": {"article_data.num_of_comment": -1}},
        {"$limit": NUM_ARTICLES},
        {"$out": collection_name},
    ]

    db[target_collection].aggregate(pipeline)
    return collection_name, target_collection, keyword


def list_top_n_commenters_filtered_by_comment_type(
    temp_collection: str, comment_type: str, num_commenters: int = 20
) -> tuple[list[Any], int]:
    """
    list top n commenters and number of comments filtered by comment type
    :param temp_collection: temporary collection
    :param comment_type: comment type  (either '推' or '噓')
    :param num_commenters: how many commenters to return
    :return: list of top n commenters and number of comments filtered by comment type
    """
    if comment_type not in ["推", "噓"]:
        raise ValueError("Invalid comment type (only accept '推' or '噓')")

    pipeline = [
        {"$unwind": "$article_data.comments"},
        {"$match": {"article_data.comments.comment_type": comment_type}},
        {
            "$group": {
                "_id": "$article_data.comments.commenter_id",
                "article_ids": {"$addToSet": "$_id"},
            }
        },
        {"$project": {"count": {"$size": "$article_ids"}}},
        {"$sort": {"count": -1}},
        {"$limit": num_commenters},
    ]

    results = db[temp_collection].aggregate(pipeline)
    return list(results), num_commenters


def generate_all_combinations(commenters: list[dict]) -> list[tuple]:
    """
    generate all combinations of commenters
    :param commenters: list of commenters with element format "{'_id': 'coffee112', 'count': 119}"
    """
    commenters = [commenter["_id"] for commenter in commenters]
    return list(combinations(commenters, 2))


def compute_concurrency(ids: tuple, temp_collection: str, comment_type: str):
    if comment_type not in ["推", "噓"]:
        raise ValueError("Invalid comment type (only accept '推' or '噓')")
    pipeline = [
        {
            "$match": {
                "$and": [
                    {
                        "article_data.comments": {
                            "$elemMatch": {
                                "commenter_id": ids[0],
                                "comment_type": comment_type,
                            }
                        }
                    },
                    {
                        "article_data.comments": {
                            "$elemMatch": {
                                "commenter_id": ids[1],
                                "comment_type": comment_type,
                            }
                        }
                    },
                ]
            }
        },
        {"$count": "count_articles"},
    ]
    result = list(db[temp_collection].aggregate(pipeline))
    concurrency = result[0]["count_articles"] / NUM_ARTICLES if len(result) != 0 else 0
    return ids[0], ids[1], concurrency


def weight_to_color(weight, weights, cmap):
    norm_weight = (weight - min(weights)) / (max(weights) - min(weights))
    rgba = cmap(norm_weight)
    return f"rgb({rgba[0]*255}, {rgba[1]*255}, {rgba[2]*255})"
