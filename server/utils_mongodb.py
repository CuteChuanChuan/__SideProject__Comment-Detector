import pytz
from datetime import datetime, timedelta
from utils_dashboard.config_dashboard import db

BATCH_SIZE = 10000
current_timezone = pytz.timezone('Asia/Taipei')
current_time = datetime.now(current_timezone).replace(hour=0, minute=0, second=0, microsecond=0)


# Section: overall information about crawling data
def extract_all_articles_commenter_involved(target_collection: str, account: str) -> list[dict]:
    """
    return all articles which have been commented by commenter
    """
    cursor = db[target_collection].find({"article_data.comments.commenter_id": account},
                                        {"_id": 1, "article_url": 1, "article_data.title": 1}).batch_size(BATCH_SIZE)
    articles_collection = []
    for article in cursor:
        articles_collection.append({"article_url": article["article_url"],
                                    "article_title": article["article_data"]["title"]})
    return articles_collection


def count_articles(target_collection: str) -> int:
    """
    count number of articles in mongodb
    :param target_collection: target collection
    :return: number of articles
    """
    return db[target_collection].count_documents({})


def count_comments(target_collection: str) -> int:
    """
    count number of articles in mongodb
    :param target_collection: target collection
    :return: number of articles
    """
    num_comments = 0
    cursor = db[target_collection].find({}, {"article_data.num_of_comment": 1})
    cursor.batch_size(BATCH_SIZE)
    for document in cursor:
        article_data = document.get("article_data", {})
        comments = article_data.get("num_of_comment", 0)
        num_comments += comments
    return num_comments


def count_accounts(target_collection: str) -> int:
    """
    count number of unique accounts in mongodb
    :param target_collection: target collection
    :return: number of articles
    """
    unique_accounts = set()
    cursor = db[target_collection].find({}, {"article_data.author": 1})
    cursor.batch_size(BATCH_SIZE)
    for document in cursor:
        article_data = document.get("article_data", {})
        unique_accounts.add(article_data["author"])
    pipeline = [
        {"$unwind": "$article_data.comments"},
        {"$group": {"_id": None,
                    "unique_commenter_ids": {"$addToSet": "$article_data.comments.commenter_id"}}}
    ]

    result = list(db[target_collection].aggregate(pipeline))
    unique_commenter_ids = result[0]['unique_commenter_ids'] if result else []
    for commenter in unique_commenter_ids:
        unique_accounts.add(commenter)

    return len(unique_accounts)


# Section: operations about article
def get_top_n_breaking_news(target_collection: str, num_articles: int) -> list:
    breaking_news = list(db[target_collection].find({"article_data.title": {"$regex": "爆卦", "$options": "i"}},
                                                    {"article_data.title": 1,
                                                     "article_data.num_of_comment": 1,
                                                     "article_url": 1,
                                                     "_id": 0})
                         .sort("article_data.num_of_comment", -1).limit(num_articles))
    return breaking_news


def get_top_n_favored_articles(target_collection: str, num_articles: int) -> list:
    pipelines = [
        {"$project": {"_id": 0, "article_url": 1, "article_data.title": 1,
                      "favor_difference":
                          {"$subtract": ["$article_data.num_of_favor", "$article_data.num_of_against"]}}},
        {"$match": {"favor_difference": {"$gt": 100}}},
        {"$sort": {"favor_difference": -1}},
        {"$limit": num_articles}
    ]
    favored_articles = list(db[target_collection].aggregate(pipelines))
    return favored_articles


def get_past_n_days_article_title(target_collection: str, n_days: int) -> list[dict]:
    """
    return article titles of the past n days
    :param target_collection: target collection
    :param n_days: number of days
    """
    n_days_ago_timestamp = int((current_time - timedelta(days=n_days)).timestamp())
    current_timestamp = int(current_time.timestamp())
    pipeline = [{"$match": {"article_data.time": {"$gte": n_days_ago_timestamp, "$lte": current_timestamp}}},
                {"$project": {"_id": 0, "article_url": 1, "article_text": "$article_data.title"}}]

    cursor = db[target_collection].aggregate(pipeline).batch_size(BATCH_SIZE)
    return list(cursor)


def get_past_n_days_comments(target_collection: str, n_days: int) -> list[dict]:
    """
    return the n days of comments
    :param target_collection: target collection
    :param n_days: number of days
    """
    n_days_ago_timestamp = int((current_time - timedelta(days=n_days)).timestamp())
    current_timestamp = int(current_time.timestamp())
    pipeline = [
        {"$match": {"article_data.time": {"$gte": n_days_ago_timestamp, "$lte": current_timestamp}}},
        {"$project": {"_id": 0, "article_url": 1, "article_data.comments": 1}},
        {"$unwind": "$article_data.comments"},
        {"$project": {"_id": 0, "article_url": 1, "article_text": "$article_data.comments.comment_content"}}
    ]
    cursor = (db[target_collection].aggregate(pipeline).batch_size(BATCH_SIZE))
    return list(cursor)

# Section: operations about accounts


if __name__ == "__main__":
    get_top_n_breaking_news("gossip", num_articles=10)
