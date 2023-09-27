import os
import time
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient

load_dotenv(verbose=True)

uri = os.getenv("ATLAS_URI", "None")

BATCH_SIZE = 10000

client = MongoClient(uri)
db = client.ptt


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
    return authors_id_set, authors_ip_set


def extract_all_commenters_accounts_and_ip(target_collection: str):
    """
    extract all accounts and ip addresses of article commenters
    :param target_collection: target collection
    """
    cursor = db[target_collection].find({}, {"article_data.comments": 1})
    cursor.batch_size(BATCH_SIZE)
    commenter_ids = []
    commenter_ips = []
    pipeline = [
        {"$unwind": "$article_data.comments"},  # Unwind the comments array
        {"$project": {  # Project only the fields we need
            "commenter_id": "$article_data.comments.commenter_id",
            "commenter_ip": "$article_data.comments.commenter_ip"
        }}
    ]

    cursor = db[target_collection].aggregate(pipeline, batchSize=15000)
    for doc in cursor:
        commenter_ids.append(doc["commenter_id"])
        commenter_ips.append(doc["commenter_ip"])
    print(commenter_ids[:20])
    print(commenter_ips[:20])
    return commenter_ids, commenter_ips


def retrieve_article(target_collection: str, search_url: str) -> dict:
    """
    retrieve article data from mongodb
    :param target_collection: target collection
    :param search_url: article url
    :return: article data
    """
    return db[target_collection].find_one({"article_url": search_url})


def get_all_article_filtered_by_keyword(target_collection: str, key_word: str, num_articles: int) -> list[tuple]:
    pipelines = [
        {"$match": {"article_data.title": {"$regex": key_word, "$options": "i"}}},
        {"$sort": {"article_data.num_of_comments": -1}},
        {"$limit": num_articles},
        {"$project": {"_id": 0, "article_url": 1, "article_data": 1}}
    ]
    all_article_data = []
    mongo_cursor = db[target_collection].aggregate(pipelines)
    for _ in mongo_cursor:
        all_article_data.append((_["article_url"], _["article_data"]["title"], _["article_data"]["author"],
                                 _["article_data"]["ipaddress"], _["article_data"]["time"],
                                 _["article_data"]["num_of_comment"]))
    return all_article_data


if __name__ == "__main__":
    start = time.time()
    extract_all_commenters_accounts_and_ip(target_collection="gossip")
    print(time.time() - start)
