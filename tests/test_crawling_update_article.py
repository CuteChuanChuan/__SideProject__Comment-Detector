from config import db, TARGET_COLLECTION
from src.crawler.dags.dag_crawling import update_article
from mock_data import (
    mock_old_data_for_checking_updating,
    mock_new_data_for_checking_updating,
)

ARTICLE_URL = mock_old_data_for_checking_updating["article_url"]
PREVIOUS_NUM_COMMENTS = mock_old_data_for_checking_updating["article_data"][
    "num_of_comment"
]


def test_update_article_with_previous_comments():
    db[TARGET_COLLECTION].insert_one(mock_old_data_for_checking_updating)

    update_article(
        target_collection=TARGET_COLLECTION,
        article_url=ARTICLE_URL,
        new_data=mock_new_data_for_checking_updating,
        previous_num_comments=PREVIOUS_NUM_COMMENTS,
    )

    updated_article = db[TARGET_COLLECTION].find_one({"article_url": ARTICLE_URL})
    assert (
        updated_article["article_data"]["num_of_favor"]
        == mock_new_data_for_checking_updating["num_of_favor"]
    )
    assert (
        updated_article["article_data"]["num_of_against"]
        == mock_new_data_for_checking_updating["num_of_against"]
    )
    assert (
        updated_article["article_data"]["num_of_arrow"]
        == mock_new_data_for_checking_updating["num_of_arrow"]
    )
    assert (
        updated_article["article_data"]["num_of_comment"]
        == mock_new_data_for_checking_updating["num_of_comment"]
    )

    db[TARGET_COLLECTION].delete_one({"article_url": ARTICLE_URL})
