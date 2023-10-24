import dag_crawling

base_url = "https://www.ptt.cc/bbs/HatePolitics/index.html"
ptt_board = "gossip" if "Gossiping" in base_url else "politics"

for i in range(3, 4):
    crawl_results = dag_crawling.crawl_articles(
        base_url, i, 1,
        crawling_logger=dag_crawling.logger_politic_from_latest_to_middle
    )
    if crawl_results:
        collection = dag_crawling.db["testing_collection"]
        collection.insert_many(crawl_results)
