from bs4 import BeautifulSoup
from src.crawler.dags.dag_crawling import get_num_announcements


def test_returns_zero_when_no_announcements():
    with open(
        "tests/for_getting_num_announcements_without_announcements.html", "r", encoding="utf-8"
    ) as file:
        soup = BeautifulSoup(file.read(), "lxml")
    result = get_num_announcements(soup)
    assert result == 0


def test_returns_correct_number_of_announcements():
    with open(
        "tests/for_getting_num_announcements_with_announcements.html", "r", encoding="utf-8"
    ) as file:
        soup = BeautifulSoup(file.read(), "lxml")
    result = get_num_announcements(soup)
    assert result == 3

