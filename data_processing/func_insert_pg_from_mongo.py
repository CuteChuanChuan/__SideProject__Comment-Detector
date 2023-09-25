import os
import time
import psycopg2
from dotenv import load_dotenv
from pymongo import MongoClient
from configuration import PostgresConfig, LoggingConfig

load_dotenv(verbose=True)

postgres_config = PostgresConfig()
# conn = psycopg2.connect(**postgres_config.config)

uri = os.getenv('ATLAS_URI', None)
client = MongoClient(uri)
db = client.ptt

pg_log_config = LoggingConfig("postgres")
pg_logger = pg_log_config.configure()


def connect_db_with_retry(connector, config: dict, retry_n_times: int, retry_backoff: int = 5):
    """
    Tries to establish the connection to the <connector> retrying <retry_n_times> times,
    and waiting <retry_backoff> seconds between attempts.

    If it can connect, return the connection object.
    If it is not possible to connect after the retries have been exhausted, return ``ConnectionError``.

    :param connector: An object with a ``.connect()`` method.
    :param config: A dictionary of connection parameters.
    :param retry_n_times: The number of times to retry to call ``connector.connect()``.
    :param retry_backoff: The time-lapse between retry call.
    """
    for _ in range(retry_n_times):
        try:
            return connector.connect(**config)
        except ConnectionError as e:
            pg_logger.info(f"{e}: attempting new connection in {retry_backoff} seconds")
            time.sleep(retry_backoff)
    exc = ConnectionError(f"Could not connect after {retry_n_times} attempts")
    pg_logger.exception(exc)
    raise exc


def get_all_article_with_keyword(target_collection: str, key_word: str, num_articles: int) -> list[tuple]:
    pipelines = [
        {"$match": {"article_data.title": {"$regex": key_word, "$options": "i"}}},
        {"$sort": {"article_data.num_of_comments": -1}},
        {"$limit": num_articles},
        {"$project": {"_id": 0, "article_url": 1, "article_data.title": 1,
                      "article_data.author": 1, "article_data.ipaddress": 1, "article_data.time": 1,
                      "article_data.num_of_comment": 1}}
    ]
    all_article_data = []
    mongo_cursor = db[target_collection].aggregate(pipelines)
    for _ in mongo_cursor:
        all_article_data.append((_["article_url"], _["article_data"]["title"], _["article_data"]["author"],
                                 _["article_data"]["ipaddress"], _["article_data"]["time"],
                                 _["article_data"]["num_of_comment"]))
    return all_article_data


def query_article_id_and_time(connection, article_url: str):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id, article_time FROM comment.article_info WHERE url = '{article_url}'")
        return cursor.fetchone()


def insert_table_article(connection, data: list[tuple]):
    with connection.cursor() as cursor:
        cursor.executemany(f"INSERT INTO comment.article_info(url, title, author_id, author_ip, "
                           f"article_time, num_comments) "
                           f"VALUES(%s, %s, %s, %s, %s, %s)", data,)
    pg_conn.commit()


def get_all_comments_in_selected_articles(target_collection: str, selected_articles: list) -> list[tuple]:
    selected_articles_url = [article[0] for article in selected_articles]
    for each_url in selected_articles_url:
        all_comments = []
        articles_id_and_time = query_article_id_and_time(pg_conn, each_url)
        pipelines = [
            {"$match": {"article_url": each_url}},
            {"$project": {"_id": 0, "article_url": 1, "article_data.comments": 1}},
            {"$unwind": "$article_data.comments"}
        ]
        mongo_cursor = db[target_collection].aggregate(pipelines)
        for _ in mongo_cursor:
            all_comments.append((articles_id_and_time[0],
                                 _["article_data"]["comments"]["commenter_id"],
                                 _["article_data"]["comments"]["commenter_ip"],
                                 "回" if _["article_data"]["comments"]["comment_type"] == "→" else _["article_data"]["comments"]["comment_type"],
                                 _["article_data"]["comments"]["comment_time"],
                                 _["article_data"]["comments"]["comment_time"] - articles_id_and_time[1]))
        insert_table_comments(pg_conn, all_comments)


def insert_table_comments(connection, data: list[tuple]):
    with connection.cursor() as cursor:
        cursor.executemany(f"INSERT INTO comment.comment_info(article_id, commenter_id, commenter_ip, comment_type, "
                           f"comment_time, comment_lapse) "
                           f"VALUES(%s, %s, %s, %s, %s, %s)", data,
        )
    pg_conn.commit()


pg_conn = connect_db_with_retry(connector=psycopg2, config=postgres_config.config, retry_n_times=5, retry_backoff=5)
pg_conn.autocommit = False


if __name__ == "__main__":
    start = time.time()
    articles_info = get_all_article_with_keyword(target_collection="gossip", key_word="雞蛋", num_articles=20)
    print(f"time: {time.time() - start}")

    start = time.time()
    insert_table_article(connection=pg_conn, data=articles_info)
    print(f"time: {time.time() - start}")

    start = time.time()
    res = get_all_comments_in_selected_articles(target_collection="gossip", selected_articles=articles_info)
    print(f"time: {time.time() - start}")

