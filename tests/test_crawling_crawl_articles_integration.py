import logging
import requests
from loguru import logger
from bs4 import BeautifulSoup

from tests.config import db
from src.crawler.dags.dag_crawling import crawl_articles, set_range_and_crawl

PAGE_IDX_FOR_CHECKING = 27975

logger_test_integration = logging.getLogger("logger_test_integration")


def manually_create_page_idx():
    base_url = "https://www.ptt.cc/bbs/Gossiping/index.html"
    soup = BeautifulSoup(requests.get(base_url, cookies={"over18": "1"}).text, "lxml")
    if soup.find_all("a", "btn wide")[1] is not None:
        previous_page = soup.find_all("a", "btn wide")[1].get("href")
        prev_idx = previous_page[
            (previous_page.find("index") + 5): previous_page.find(".html")
        ]
        start_idx = int(prev_idx) + 1 - PAGE_IDX_FOR_CHECKING + 1
        return start_idx


def test_crawl_articles():
    start_idx = manually_create_page_idx()

    base_url = "https://www.ptt.cc/bbs/Gossiping/index.html"
    # for i in range(start_idx, start_idx + 1):
    #     crawl_results = crawl_articles(
    #         base_url, i, 1, crawling_logger=logger_test_integration
    #     )
    #     if crawl_results:
    #         collection = db.testing_collection
    #         collection.insert_many(crawl_results)

    set_range_and_crawl(
        base_url=base_url,
        ptt_board="testing_collection",
        logger_assigned=logger_test_integration,
        start_generation=start_idx,
        end_generation=start_idx + 1,
    )

    articles_inserted_with_testing_functions = list(
        db.testing_collection.find({"article_page_idx": PAGE_IDX_FOR_CHECKING})
    )
    articles_already_in_db = list(
        db.gossip.find({"article_page_idx": PAGE_IDX_FOR_CHECKING})
    )
    keys_used = [
        "author",
        "ipaddress",
        "title",
        "time",
        "main_content",
        "num_of_comment," "num_of_favor," "num_of_against," "num_of_arrow," "comments",
    ]
    assert len(articles_inserted_with_testing_functions) == len(articles_already_in_db)
    for article in articles_inserted_with_testing_functions:
        article_url = article.get("article_url")

        for key in keys_used:
            assert article.get("article_data").get(key) == db.gossip.find_one(
                {"article_url": article_url}
            ).get("article_data").get(key)

        assert article.get("article_data").get("title") == db.gossip.find_one(
            {"article_url": article_url}
        ).get("article_data").get("title")
        assert article.get("article_data").get("title") == db.gossip.find_one(
            {"article_url": article_url}
        ).get("article_data").get("title")

    db.testing_collection.delete_many({"article_page_idx": PAGE_IDX_FOR_CHECKING})
