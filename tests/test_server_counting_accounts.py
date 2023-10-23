from tests.config import db
from src.server.utils_dashboard.utils_mongodb import count_accounts


def test_valid_target_collection():
    for target_collection in ["gossip", "politics"]:
        result = count_accounts(target_collection)
        assert isinstance(result, int)
        assert result >= 0


def test_no_articles():
    target_collection = "empty_collection"
    result = count_accounts(target_collection)
    assert result == 0

