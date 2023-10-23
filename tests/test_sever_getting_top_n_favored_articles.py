from loguru import logger
from tests.config import db, TARGET_COLLECTION
from src.server.utils_dashboard.utils_mongodb import get_top_n_favored_articles


def test_get_top_n_favored_articles():
    # top_n_favored_articles = get_top_n_favored_articles(
    #     target_collection="gossip", num_articles=10
    # )
    # db["Correct_Results"].insert_many(top_n_favored_articles)

    # correct_results = list(db[TARGET_COLLECTION].find({"favor_difference": 1}))
