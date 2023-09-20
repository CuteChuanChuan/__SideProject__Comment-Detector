import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from crawl_ptt_gossip import crawl_articles, parse_article

load_dotenv(verbose=True)

uri = os.getenv("ATLAS_URI", "None")

client = MongoClient(uri)
db = client.ptt

base_url = "https://www.ptt.cc/bbs/Gossiping/index.html"
ptt_board = "gossip" if "Gossiping" in base_url else "politics"
for i in range(2, 3):
    crawl_results = crawl_articles(base_url, i, 1)
    if crawl_results:
        collection = db[ptt_board]
        collection.insert_many(crawl_results)
