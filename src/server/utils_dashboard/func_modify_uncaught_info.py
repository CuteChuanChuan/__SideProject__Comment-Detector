import pytz
from loguru import logger
from bson.objectid import ObjectId
from datetime import datetime
from config_dashboard import db


def convert_to_utc8(timestamp_str):
    current_year = datetime.now().year
    full_timestamp_str = f"{current_year}/{timestamp_str}:59"
    naive_dt = datetime.strptime(full_timestamp_str, "%Y/%m/%d %H:%M:%S")
    utc8 = pytz.timezone("Asia/Taipei")
    localized_dt = utc8.localize(naive_dt)
    timestamp = localized_dt.timestamp()

    return float(timestamp)


new_data = [
    ("61.228.224.201", "10/21 01:04"),
    ("203.204.194.135", "10/21 01:09"),
    ("114.35.115.89", "10/21 01:17"),
    ("101.138.104.128", "10/21 01:22"),
    ("220.137.34.16", "10/21 02:13"),
    ("219.70.184.41", "10/21 10:56"),
    ("36.225.6.132", "10/21 12:37"),
    ("36.225.6.132", "10/21 12:37")
]

pipeline = [
    {"$match": {"article_data.comments.comment_time": None}},
    {"$unwind": "$article_data.comments"},
    {"$match": {"article_data.comments.comment_time": None}},
    {"$project": {"_id": 1, "article_data.comments": 1, "article_url": 1}},
]

results = list(db.politics.aggregate(pipeline))

for doc in results[:3]:
    print(doc)

results = results[:20]
#
for idx, content in enumerate(results):
    print(idx, content)
    ptt_board = "gossip" if "Gossiping" in content["article_url"] else "politics"
    new_commenter_ip = new_data[idx][0]
    new_comment_time = new_data[idx][1]
    new_timestamp = convert_to_utc8(new_comment_time)

    filter_query = {
        "_id": ObjectId(content["_id"]),
    }
    update_query = {
        "$set": {
            "article_data.comments.$[elem].comment_time": new_timestamp,
            "article_data.comments.$[elem].commenter_ip": new_commenter_ip,
        }
    }
    array_filters = [
        {
            "elem.commenter_id": content["article_data"]["comments"]["commenter_id"],
            "$or": [{"elem.commenter_ip": None}, {"elem.comment_time": None}],
        }
    ]
    logger.debug("Filter:", filter_query)
    logger.debug("Update:", update_query)
    logger.debug("Array Filters:", array_filters)
    result = db[ptt_board].update_one(
        filter_query, update_query, array_filters=array_filters
    )
    logger.debug("Matched Count:", result.matched_count)
    logger.debug("Modified Count:", result.modified_count)


