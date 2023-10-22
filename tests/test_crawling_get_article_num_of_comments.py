from config import db, TARGET_COLLECTION
from src.crawler.dags.dag_crawling import get_article_num_of_comments
from mock_data import mock_data_for_checking_getting_num_comments


ARTICLE_URL = mock_data_for_checking_getting_num_comments["article_url"]
PREVIOUS_NUM_COMMENTS = mock_data_for_checking_getting_num_comments["article_data"][
    "num_of_comment"
]

db[TARGET_COLLECTION].insert_one(mock_data_for_checking_getting_num_comments)


def test_get_article_num_of_comments():
    num_comments = get_article_num_of_comments(article_url=ARTICLE_URL, target_collection=TARGET_COLLECTION)
    assert (
        num_comments
        == mock_data_for_checking_getting_num_comments["article_data"]["num_of_comment"]
    )


db[TARGET_COLLECTION].delete_one({"_id": "getting_num_comments"})
