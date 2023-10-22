import bs4
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from src.crawler.dags.dag_crawling import parse_basic_info

responses = requests.get(
    "https://www.ptt.cc/bbs/HatePolitics/M.1697779439.A.7EC.html", "lxml"
)
soup = BeautifulSoup(responses.text, "lxml")
example_article_basic_info = soup.find_all("div", "article-metaline")

responses_wrong_format = requests.get(
    "https://www.ptt.cc/bbs/HatePolitics/M.1694139970.A.129.html", "lxml"
)
soup_wrong_format = BeautifulSoup(responses_wrong_format.text, "lxml")
example_article_basic_info_wrong_format = soup_wrong_format.find_all(
    "div", "article-metaline"
)


def test_valid_basic_info():
    result = parse_basic_info(example_article_basic_info)
    assert isinstance(result, tuple)
    assert len(result) == 5
    assert result[0] == "Friend5566 (朋友56)"
    assert result[1] == "[討論] 高學歷柯粉怎麼連基本法律素養都沒有"
    assert result[2] == "Fri Oct 20 13:23:57 2023"
    assert result[3] == datetime(2023, 10, 20, 13, 23, 57)
    assert result[4] == 1697779437.0
    assert isinstance(result[3], datetime)
    assert isinstance(result[4], float)


def test_parse_basic_info_with_wrong_input():
    result = parse_basic_info(example_article_basic_info_wrong_format)
    assert result[0] == "Homura (德意志國防貓)"
    assert result[1] == "[新聞] 提早結束訪日行程！遭爆「名車接送"
    assert result[2] == "Fri Sep 8 10:26:08 2023"
    assert result[3] == datetime(2023, 9, 8, 10, 26, 8)
    assert result[4] == 1694139968.0


def test_missing_basic_info():
    article_basic_info = bs4.element.ResultSet(source="")
    result = parse_basic_info(article_basic_info)
    assert isinstance(result, dict)
    assert "error" in result
    assert result["error"] == "Article's info (author, title and time) is incomplete"
