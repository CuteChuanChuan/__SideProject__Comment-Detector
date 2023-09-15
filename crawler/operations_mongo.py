import os
import pymongo
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient

load_dotenv(verbose=True)

uri = os.getenv("ATLAS_URI", "None")

# Create a new client and connect to the server
client = MongoClient(uri)
db = client.ptt


def article_existing(target_collection: str, search_url: str) -> bool:
    """
    check whether article already exists in mongodb
    :param target_collection: target collection
    :param search_url: article url
    :return: True if article exists, False otherwise
    """
    return True if db[target_collection].find_one({"article_url": search_url}) else False


def check_article_comments_num(target_collection: str, search_url: str) -> int:
    """
    get number of comments for article
    :param target_collection: target collection
    :param search_url: article url
    :return: number of comments
    """
    return db[target_collection].find_one({"article_url": search_url})["article_data"]["num_of_comment"]


def delete_article(target_collection: str, target_url: str):
    """
    delete article from mongodb
    :param target_collection: target collection
    :param target_url: article url
    """
    db[target_collection].delete_one({"article_url": target_url})


def update_article(target_collection: str, query: dict, new_data: dict):
    """
    update article in mongodb
    :param target_collection: target collection
    :param query: filter query
    :param new_data: new data
    """
    db[target_collection].update_one(query, {"$set": {"new_data": new_data}})


if __name__ == "__main__":
    existence = article_existing(target_collection="gossip",
                                 search_url="https://www.ptt.cc/bbs/Gossiping/M.1694736317.A.3A1.html")
    if existence:
        num_comments = check_article_comments_num(target_collection="gossip",
                                                  search_url="https://www.ptt.cc/bbs/Gossiping/M.1694736317.A.3A1.html")
        print(num_comments)

