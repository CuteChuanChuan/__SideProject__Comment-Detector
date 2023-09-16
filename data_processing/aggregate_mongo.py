import os
import time
from dotenv import load_dotenv
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient

load_dotenv(verbose=True)

uri = os.getenv("ATLAS_URI", "None")

BATCH_SIZE = 10000

# Create a new client and connect to the server
client = MongoClient(uri)
db = client.ptt


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


def extract_all_authors_accounts_and_ip(target_collection: str):
    """
    extract all accounts and ip addresses of article author
    :param target_collection: target collection
    """
    cursor = db[target_collection].find({}, {"article_data.author": 1, "article_data.ipaddress": 1})
    cursor.batch_size(BATCH_SIZE)
    authors_id_set = []
    authors_ip_set = []
    for document in cursor:
        article_data = document.get("article_data", {})
        author_nickname = article_data.get("author", "")
        author = author_nickname.split(" ")[0] if author_nickname else None
        ipaddress = article_data.get("ipaddress", "")
        authors_id_set.append(author)
        authors_ip_set.append(ipaddress)
    print(len(authors_id_set))
    return authors_id_set, authors_ip_set


if __name__ == "__main__":
    start = time.time()
    print(extract_all_authors_accounts_and_ip(target_collection="gossip"))
    print(time.time() - start)
