from bs4 import BeautifulSoup
from src.crawler.dags.dag_crawling import (
    exclude_announcements_from_titles,
    get_num_announcements,
)


def test_return_list_of_titles_excluding_announcement_titles_if_num_announcement_greater_than_0():
    with open(
        "tests/for_getting_num_announcements_with_announcements.html", "r", encoding="utf-8"
    ) as file:
        soup = BeautifulSoup(file.read(), "lxml")
        current_page_title_collections = soup.find_all("div", "r-ent")
        num_announcement = get_num_announcements(soup=soup)

    result = exclude_announcements_from_titles(current_page_title_collections, num_announcement)
    assert len(result) == 13


def test_return_list_of_titles_excluding_announcement_titles_if_num_announcement_is_0():
    with open(
        "tests/for_getting_num_announcements_without_announcements.html", "r", encoding="utf-8"
    ) as file:
        soup = BeautifulSoup(file.read(), "lxml")
        current_page_title_collections = soup.find_all("div", "r-ent")
        num_announcement = get_num_announcements(soup=soup)

    result = exclude_announcements_from_titles(current_page_title_collections, num_announcement)
    assert len(result) == 20
