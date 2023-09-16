import os
import time
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient

load_dotenv(verbose=True)

uri = os.getenv("ATLAS_URI", "None")

PTT_BOARD = "gossip"

# Create a new client and connect to the server
client = MongoClient(uri)
db = client.ptt
collection = db[PTT_BOARD]

people_info_collection = []

num_comments = 0

start = time.time()

cursor = collection.find({}, {"article_data.author": 1, "article_data.ipaddress": 1,
                              "article_data.num_of_comment": 1, "article_data.comments": 1})
batch_size = 10000
cursor.batch_size(batch_size)

ip = set()

for document in cursor:
    article_data = document.get("article_data", {})
    author = article_data.get("author", "")
    ipaddress = article_data.get("ipaddress", "")
    print(ipaddress)
    comments = article_data.get("num_of_comment", [])
    if ipaddress:
        ip.add(ipaddress)
print(len(ip))
print(time.time() - start)




