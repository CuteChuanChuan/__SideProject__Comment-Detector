from dag_crawling import *

base_url = "https://www.ptt.cc/bbs/HatePolitics/index.html"
ptt_board = "gossip" if "Gossiping" in base_url else "politics"
for i in range(2, 3):
    crawl_results = crawl_articles(base_url, i, 1)
    if crawl_results:
        collection = db[ptt_board]
        collection.insert_many(crawl_results)
