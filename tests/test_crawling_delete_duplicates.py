from config import db, TARGET_COLLECTION
from src.crawler.dags.dag_crawling import delete_duplicates


def test_delete_duplicates_with_duplicates():
    db[TARGET_COLLECTION].insert_many(
        [
            {
                "_id": "duplicate_1",
                "article_url": "https://www.ptt.cc/bbs/HatePolitics/M.1695225784.A.A25.html",
            },
            {
                "_id": "duplicate_2",
                "article_url": "https://www.ptt.cc/bbs/HatePolitics/M.1695225784.A.A25.html",
            },
        ]
    )
    delete_duplicates(TARGET_COLLECTION)
    assert (
        len(
            list(
                db[TARGET_COLLECTION].find(
                    {
                        "article_url": "https://www.ptt.cc/bbs/HatePolitics/M.1695225784.A.A25.html"
                    }
                )
            )
        )
        == 1
    )
    db[TARGET_COLLECTION].delete_many({"_id": {"$regex": "^duplicate_"}})


def test_delete_duplicates_no_duplicates():
    db[TARGET_COLLECTION].insert_many(
        [
            {
                "_id": "not_duplicate_1",
                "article_url": "https://www.ptt.cc/bbs/HatePolitics/M.1695225784.A.A99.html",
            },
            {
                "_id": "not_duplicate_2",
                "article_url": "https://www.ptt.cc/bbs/HatePolitics/M.1695225784.A.A98.html",
            },
        ]
    )
    delete_duplicates(TARGET_COLLECTION)
    assert (
        len(
            list(
                db[TARGET_COLLECTION].find(
                    {
                        "article_url": "https://www.ptt.cc/bbs/HatePolitics/M.1695225784.A.A99.html"
                    }
                )
            )
        )
        == 1
    )
    assert (
        len(
            list(
                db[TARGET_COLLECTION].find(
                    {
                        "article_url": "https://www.ptt.cc/bbs/HatePolitics/M.1695225784.A.A98.html"
                    }
                )
            )
        )
        == 1
    )
    db[TARGET_COLLECTION].delete_many({"_id": {"$regex": "^not_duplicate_"}})
