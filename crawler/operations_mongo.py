import os
from dotenv import load_dotenv
from datetime import datetime
from pymongo.mongo_client import MongoClient

load_dotenv(verbose=True)

uri = os.getenv("ATLAS_URI", "None")

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


def update_article(target_collection: str, search_url: str, new_data: dict, previous_num_comments: int) -> bool:
    """
    update article in mongodb
    :param target_collection: target collection
    :param search_url: article url
    :param new_data: new data
    :param previous_num_comments: previous number of comments
    """
    num_of_favor = new_data["num_of_favor"]
    num_of_against = new_data["num_of_against"]
    num_of_arrow = new_data["num_of_arrow"]
    num_of_comment = num_of_favor + num_of_against + num_of_arrow
    new_comments = new_data["comments"][previous_num_comments:]

    db[target_collection].update_one(
        {"article_url": search_url},
        {
            "$set": {
                "article_data.last_crawled_datetime": datetime.now().timestamp(),
                "article_data.num_of_favor": num_of_favor,
                "article_data.num_of_against": num_of_against,
                "article_data.num_of_arrow": num_of_arrow,
                "article_data.num_of_comment": num_of_comment,
            }
        })

    for comment in new_comments:
        db[target_collection].update_one(
            {"article_url": search_url},
            {"$push": {"article_data.comments": comment}})


def check_article_having_data(target_collection: str, search_url: str) -> bool:
    """
    check whether article data exists in mongodb
    :param target_collection: target collection
    :param search_url: article url
    :return: True if article data exists, False otherwise
    """
    return True if db[target_collection].find_one({"article_url": search_url})["article_data"] else False


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


# def update_article(target_collection: str, query: dict, new_data: dict):
#     """
#     update article in mongodb
#     :param target_collection: target collection
#     :param query: filter query
#     :param new_data: new data
#     """
#     db[target_collection].update_one(query, {"$set": {"new_data": new_data}})


def update_wrong_ip():
    """
    find out documents with error ip which includes space at the end before update the ip address
    """
    result = list(db["gossip"].find({"article_data.ipaddress": {'$regex': '\s'}}))
    for _ in result:
        new_ip = _["article_data"]["ipaddress"].split(" ")[0]
        new_ip_values = {"$set": {"article_data.ipaddress": new_ip}}
        db["gossip"].update_many({"article_data.ipaddress": {'$regex': '\s'}}, new_ip_values)


def delete_duplicates(target_collection: str):
    """
    delete duplicated articles in mongodb
    :param target_collection: target collection
    """
    collection = db[target_collection]
    pipeline = [
        {"$group": {"_id": "$article_url", "ids": {"$push": "$_id"}, "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}}
    ]
    duplicates = collection.aggregate(pipeline)

    for duplicate in duplicates:
        print(duplicate)
        article_url = duplicate["_id"]
        duplicate_ids = duplicate["ids"]
        print(f"Duplicate article_url: {article_url}, count: {len(duplicate_ids)}")

        for id_to_delete in duplicate_ids[1:]:
            collection.delete_one({"_id": id_to_delete})
