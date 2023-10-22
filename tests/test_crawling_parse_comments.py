import requests
from datetime import datetime
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from src.crawler.dags.dag_crawling import parse_comments

URL = "https://www.ptt.cc/bbs/Gossiping/M.1686499940.A.496.html"


def test_parses_comments_with_valid_input():
    ua = UserAgent()
    cookies = {"from": "/bbs/Gossiping/index.html", "yes": "yes"}
    headers = {"user-agent": ua.random}
    current_session = requests.session()
    current_request = current_session.get(URL, headers=headers)

    if "over18" in current_request.url:
        current_session.post("https://www.ptt.cc/ask/over18", data=cookies)
        current_request = current_session.get(URL, headers=headers)

    soup = BeautifulSoup(
        current_request.text,
        "lxml",
    )
    article_time = "Mon Jun 12 00:12:17 2023"
    article_timestamp = datetime.strptime(article_time, "%a %b %d %H:%M:%S %Y")

    favor, against, arrow, comments = parse_comments(
        soup, article_time, article_timestamp
    )

    assert favor == 1
    assert against == 3
    assert arrow == 8
    assert len(comments) == 12
    assert comments[0]["commenter_id"] == "yu7038"
    assert comments[0]["commenter_ip"] == "118.168.128.49"
    assert comments[0]["comment_time"] == 1686499979
    assert comments[0]["comment_type"] == "噓"
    assert comments[0]["comment_content"] == "你爽就好"
