import os
from dotenv import load_dotenv
from fake_useragent import UserAgent
from pymongo.mongo_client import MongoClient

ua = UserAgent()
cookies = {"from": "/bbs/Gossiping/index.html", "yes": "yes"}

load_dotenv(verbose=True)

uri = os.getenv("ATLAS_URI", "None")
client = MongoClient(uri)
db = client.ptt


# --- Functions related to mongodb ---
def check_article_having_data(target_collection: str, search_url: str) -> bool:
    """
    check whether article data exists in mongodb
    :param target_collection: target collection
    :param search_url: article url
    :return: True if article data exists, False otherwise
    """
    return True if db[target_collection].find_one({"article_url": search_url})["article_data"] else False


def delete_article(target_collection: str, target_url: str):
    """
    delete article from mongodb
    :param target_collection: target collection
    :param target_url: article url
    """
    db[target_collection].delete_one({"article_url": target_url})

