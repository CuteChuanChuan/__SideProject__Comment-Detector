import requests
from tests.config import db
from src.crawler.dags.dag_crawling import parse_article

response = requests.get(
    "https://www.ptt.cc/bbs/Gossiping/M.1686499940.A.496.html",
    cookies={"over18": "1"},
)


def test_parse_article_compared_with_db_gossip():
    parsed_results = parse_article(response)
    correct_results = db.gossip.find_one({"article_url": "https://www.ptt.cc/bbs/Gossiping/M.1686499940.A.496.html"}).get("article_data")

    keys_used = [
        "author",
        "ipaddress",
        "title",
        "time",
        "main_content",
        "num_of_comment,"
        "num_of_favor,"
        "num_of_against,"
        "num_of_arrow,"
        "comments"
    ]
    for key in keys_used:
        assert parsed_results.get(key) == correct_results.get(key)

