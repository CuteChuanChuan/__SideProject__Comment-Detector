import requests
from bs4 import BeautifulSoup
from src.crawler.dags.dag_crawling import parse_article_content_and_ip


def test_extracts_main_content_and_ip_expected_format():
    response = requests.get(
        "https://www.ptt.cc/bbs/HatePolitics/M.1697779439.A.7EC.html"
    )
    soup = BeautifulSoup(response.text, "lxml")
    article_time = "Fri Oct 20 13:23:57 2023"

    result = parse_article_content_and_ip(soup=soup, article_time=article_time)
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert (
        result[0]
        == "\nhttps://i.imgur.com/f7BU3U6.png\n\n王姓男大生高學歷柯粉\n\n單純不爽林昶佐跟柯文哲不合\n\n直接拿政府部門書信偽造文書 企圖栽贓林昶佐\n\n這就是最理性最中立的新政治喔\n\n奇怪了 高學歷柯粉怎麼會連基本的法律觀念都沒有\n\n"
    )
    assert result[1] == "140.114.57.56"


def test_returns_none_content_ip():
    soup = BeautifulSoup("<div id='main-content'>內容--\n無法編輯</div>", "lxml")
    article_time = "Fri Oct 20 13:23:57 2023"
    result = parse_article_content_and_ip(soup, article_time)
    assert isinstance(result, tuple)
    assert result[0] is None
    assert result[1] is None

