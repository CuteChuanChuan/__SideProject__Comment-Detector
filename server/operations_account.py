import os
import time
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient

load_dotenv(verbose=True)

uri = os.getenv("ATLAS_URI", "None")
client = MongoClient(uri)
db = client[os.getenv("ATLAS_DATABASE", "ptt")]

BATCH_SIZE = 1000


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
