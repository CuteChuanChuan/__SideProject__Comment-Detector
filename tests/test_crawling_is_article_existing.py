from src.crawler.dags.dag_crawling import is_article_existing


def test_returns_true_if_article_exists():
    target_collection = "gossip"
    article_url = "https://www.ptt.cc/bbs/Gossiping/M.1695226744.A.B77.html"

    result = is_article_existing(article_url, target_collection)
    assert result is True


def test_returns_false_if_article_does_not_exist():
    target_collection = "gossip"
    article_url = "https://www.ptt.cc/bbs/Gossiping/M.1695226744.A.B78.html"

    result = is_article_existing(article_url, target_collection)
    assert result is False


def test_returns_false_if_target_collection_does_not_exist():
    target_collection = "politics"
    article_url = "https://www.ptt.cc/bbs/Gossiping/M.1695226744.A.B77.html"

    result = is_article_existing(article_url, target_collection)
    assert result is False

