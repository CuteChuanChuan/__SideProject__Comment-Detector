import pytest
from bs4 import BeautifulSoup
from src.crawler.dags.dag_crawling import create_page_idx


def test_valid_input():
    with open("tests/for_creating_index.html", "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")
    start_page = 3
    result = create_page_idx(soup, start_page)
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], int)
    assert isinstance(result[1], int)


def test_calculate_values():
    with open("tests/for_creating_index.html", "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")
    start_page = 3
    result = create_page_idx(soup, start_page)
    assert result[0] == 4005
    assert result[1] == 4003


def test_invalid_soup():
    soup = None
    start_page = 3
    with pytest.raises(Exception):
        create_page_idx(soup, start_page)
