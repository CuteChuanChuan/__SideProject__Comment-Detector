from config import db, TARGET_COLLECTION
from src.crawler.dags.dag_crawling import update_wrong_ip


def test_update_ip_with_error_ip():
    db[TARGET_COLLECTION].insert_many(
        [
            {
                "_id": "wrong_ip_1",
                "article_data": {"ipaddress": "192.168.0.1"},
            },
            {
                "_id": "wrong_ip_2",
                "article_data": {"ipaddress": "192.168.0.2 "},
            },
            {
                "_id": "wrong_ip_3",
                "article_data": {"ipaddress": "192.168.0.3 "},
            },
            {
                "_id": "wrong_ip_4",
                "article_data": {"ipaddress": "192.168.0.4"},
            },
        ]
    )

    update_wrong_ip(TARGET_COLLECTION)
    documents = list(db[TARGET_COLLECTION].find({"_id": {"$regex": "^wrong_ip_"}}))

    for idx, document in enumerate(documents, start=1):
        assert document["article_data"]["ipaddress"] == f"192.168.0.{idx}"

    db[TARGET_COLLECTION].delete_many({"_id": {"$regex": "^wrong_ip_"}})
