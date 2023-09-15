import os
from dotenv import load_dotenv
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient
from crawl_ptt_gossip import crawl_articles, parse_article

load_dotenv(verbose=True)

uri = os.getenv("ATLAS_URI", "None")

# Create a new client and connect to the server
client = MongoClient(uri)
db = client.ptt
collection = db.gossip

result = collection.find({"article_data.author": "sweat992001 (小樽)"})
for doc in result:
    print(doc)
