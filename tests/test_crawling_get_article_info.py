import requests
from bs4 import BeautifulSoup
from src.crawler.dags.dag_crawling import get_article_info


responses = requests.get(
        "https://www.ptt.cc/bbs/HatePolitics/M.1697779439.A.7EC.html", "lxml"
    )
soup = BeautifulSoup(responses.text, "lxml")
article_basic_info = soup.find_all("div", "article-metaline")


def test_returns_correct_article_info_article_author():
    result = get_article_info(article_basic_info, 0)
    assert result == "Friend5566 (朋友56)"


def test_returns_correct_article_info_article_title():
    result = get_article_info(article_basic_info, 1)
    assert result == "[討論] 高學歷柯粉怎麼連基本法律素養都沒有"


def test_returns_correct_article_info_article_time():
    result = get_article_info(article_basic_info, 2)
    assert result == "Fri Oct 20 13:23:57 2023"

