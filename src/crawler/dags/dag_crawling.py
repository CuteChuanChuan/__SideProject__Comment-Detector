import os
import bs4
import json
import time
import pytz
import logging
import requests
import urllib.parse
import configparser
from airflow import DAG
from loguru import logger
import google.cloud.logging
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pymongo import MongoClient
from fake_useragent import UserAgent
from datetime import datetime, timedelta
from typing import Union, Dict, Tuple, Any, List
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from google.oauth2.service_account import Credentials

SLEEP_INTERVAL_BETWEEN_ARTICLES = 4.0
SLEEP_INTERVAL_BETWEEN_PAGES = 9.0
SLEEP_INTERVAL_IF_GET_CAUGHT = 60.0
TAIPEI_TIMEZONE = pytz.timezone("Asia/Taipei")

PAGE_GENERATION_LATEST = 1
PAGE_GENERATION_MIDDLE = 5
PAGE_GENERATION_ANCIENT = 5000
PAGE_GENERATION_EARLIEST = 40000

load_dotenv(verbose=True)

default_args = {
    "owner": "Raymond",
    "start_date": datetime(2023, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 5,
    "retry_delay": timedelta(minutes=5),
}

uri = os.getenv("ATLAS_URI", "None")
client = MongoClient(uri)
db = client.ptt

current_dir = os.path.dirname(os.path.abspath(__file__))
ini_file_path = os.path.join(current_dir, 'config.ini')
config = configparser.ConfigParser()
config.read(ini_file_path)
environment = config["settings"]["environment"]

ua = UserAgent()
cookies = {"from": "/bbs/Gossiping/index.html", "yes": "yes"}

logger.add(
    sink="logs/airflow_crawler_{time}.log",
    rotation="00:00",
    retention="14 days",
    level="DEBUG",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} {function}() | {message}",
    enqueue=True,
    serialize=True,
    backtrace=True,
    diagnose=True,
)

if environment == "production":
    gcp_key_path = os.environ.get("AIRFLOW__LOGGING__GOOGLE_KEY_PATH")
    credentials = Credentials.from_service_account_file(gcp_key_path)
    client = google.cloud.logging.Client(credentials=credentials)
    client.setup_logging()

logger_gossip_from_latest_to_middle = logging.getLogger(
    "logger_gossip_from_latest_to_middle"
)
logger_gossip_from_middle_to_ancient = logging.getLogger(
    "logger_gossip_from_middle_to_ancient"
)
logger_gossip_from_ancient_to_earliest = logging.getLogger(
    "logger_gossip_from_ancient_to_earliest"
)
logger_politic_from_latest_to_middle = logging.getLogger(
    "logger_politic_from_latest_to_middle"
)
logger_politic_from_middle_to_ancient = logging.getLogger(
    "logger_politic_from_middle_to_ancient"
)
logger_politic_from_ancient_to_earliest = logging.getLogger(
    "logger_politic_from_ancient_to_earliest"
)


def decide_ptt_board(url: str) -> str:
    """
    decide mongoDB collection
    :base_url: article url
    :return: mongoDB collection (either gossip or politics)
    """
    return "gossip" if "Gossiping" in url else "politics"


def is_article_existing(article_url: str, target_collection: str) -> bool:
    """
    check whether article already exists in mongodb
    :param target_collection: target collection
    :param article_url: article url
    :return: True if article exists, False otherwise
    """
    return (
        True if db[target_collection].find_one({"article_url": article_url}) else False
    )


def update_article(
    article_url: str, new_data: dict, previous_num_comments: int, target_collection: str
):
    """
    update article data in mongodb
    :param target_collection: target collection
    :param article_url: article url
    :param new_data: new data
    :param previous_num_comments: previous number of comments
    """
    num_of_favor = new_data["num_of_favor"]
    num_of_against = new_data["num_of_against"]
    num_of_arrow = new_data["num_of_arrow"]
    num_of_comment = num_of_favor + num_of_against + num_of_arrow
    new_comments = new_data["comments"][previous_num_comments:]

    db[target_collection].update_one(
        {"article_url": article_url},
        {
            "$set": {
                "article_data.last_crawled_datetime": datetime.now().timestamp(),
                "article_data.num_of_favor": num_of_favor,
                "article_data.num_of_against": num_of_against,
                "article_data.num_of_arrow": num_of_arrow,
                "article_data.num_of_comment": num_of_comment,
            }
        },
    )

    for comment in new_comments:
        db[target_collection].update_one(
            {"article_url": article_url}, {"$push": {"article_data.comments": comment}}
        )


def get_article_num_of_comments(article_url: str, target_collection: str) -> int:
    """
    get number of comments for article
    :param target_collection: target collection
    :param article_url: article url
    :return: number of comments
    """
    return db[target_collection].find_one({"article_url": article_url})["article_data"][
        "num_of_comment"
    ]


def update_wrong_ip(target_collection: str):
    """
    find out documents with error ip including space at the end before update the ip address
    :param target_collection: target collection
    """
    results = list(
        db[target_collection].find({"article_data.ipaddress": {"$regex": "\\s"}})
    )
    for result in results:
        new_ip = result["article_data"]["ipaddress"].split(" ")[0]
        new_ip_values = {"$set": {"article_data.ipaddress": new_ip}}
        db[target_collection].update_one(
            {"article_data.ipaddress": {"$regex": "\\s"}}, new_ip_values
        )


def delete_duplicates(target_collection: str):
    """
    delete duplicated articles in mongodb
    :param target_collection: target collection
    """
    pipeline = [
        {
            "$group": {
                "_id": "$article_url",
                "ids": {"$push": "$_id"},
                "count": {"$sum": 1},
            }
        },
        {"$match": {"count": {"$gt": 1}}},
    ]
    duplicates = db[target_collection].aggregate(pipeline)

    for duplicate in duplicates:
        article_url = duplicate["_id"]
        duplicate_ids = duplicate["ids"]
        logger.info(
            f"Article ({article_url}) appears {len(duplicate_ids)} times. Duplicates are deleted."
        )

        for _id in duplicate_ids[1:]:
            db[target_collection].delete_one({"_id": _id})


# --- Functions related to crawling ---
def get_article_info(meta_info: bs4.element.ResultSet, _idx: int) -> str:
    """
    get article information, for instance, author, title, and published time
    :param meta_info: article info part
    :param _idx: index
    :return: str
    """
    return meta_info[_idx].find("span", "article-meta-value").get_text()


def parse_basic_info(
    article_basic_info: bs4.element.ResultSet,
) -> dict[str, str] | tuple[str, str, str, datetime, Any]:
    """
    parse article basic info
    :param article_basic_info: article basic info part
    :return: tuple of article's title, author, published time and timestamp or error message
    """
    try:
        article_author = get_article_info(article_basic_info, 0)
        article_title = get_article_info(article_basic_info, 1)
        article_time = get_article_info(article_basic_info, 2)
    except IndexError as e:
        logger.exception(f"{e}: article author, title and time have problems")
        return {"error": "Article's info (author, title and time) is incomplete"}

    try:
        article_timestamp = datetime.strptime(article_time, "%a %b %d %H:%M:%S %Y")
    except ValueError:
        # to handle: https://www.ptt.cc/bbs/HatePolitics/M.1694139970.A.129.html (only occurred once)
        article_time = "Fri Sep 8 10:26:08 2023"
        article_timestamp = datetime.strptime(article_time, "%a %b %d %H:%M:%S %Y")
    localized_article_timestamp = TAIPEI_TIMEZONE.localize(
        article_timestamp
    ).timestamp()

    return (
        article_author,
        article_title,
        article_time,
        article_timestamp,
        localized_article_timestamp,
    )


def parse_article_content_and_ip(
    soup: bs4.BeautifulSoup, article_time: str
) -> tuple[str | None, str | None] | dict[str, str]:
    """
    parse article content and ip
    :param soup: bs4.BeautifulSoup
    :param article_time: article time
    :return: tuple of article content and ip or error message
    """
    main_content, article_ip = None, None
    try:
        if soup.find("div", id="main-content") is not None:
            bottom_text = (
                soup.find("div", id="main-content")
                .get_text()
                .split("--\n※ 發信站: 批踢踢實業坊(ptt.cc), 來自: ")
            )
            if len(bottom_text) == 2:
                main_content = bottom_text[0].split(article_time)[1]
                article_ip = bottom_text[1].split(" ")[0].strip()

            # to handle: https://www.ptt.cc/bbs/Gossiping/M.1694539823.A.DEE.html (no --\n※ 發信站:)
            # to handle: https://www.ptt.cc/bbs/Gossiping/M.1694532584.A.102.html (--\n\n※ 發信站:)
            # to handle: https://www.ptt.cc/bbs/Gossiping/M.1694678215.A.764.html (no --\n※ 發信站:)
            # to handle: https://www.ptt.cc/bbs/Gossiping/M.1694572013.A.B01.html
            # to handle: https://www.ptt.cc/bbs/Gossiping/M.1694694211.A.8CB.html
            # to handle: https://www.ptt.cc/bbs/HatePolitics/M.1695217763.A.386.html
            else:
                ending_signals_potential_variants = [
                    "--\n※ 編輯: ",
                    "--\n\n※ 發信站: 批踢踢實業坊(ptt.cc), 來自: ",
                    "※ 發信站: 批踢踢實業坊(ptt.cc), 來自: ",
                ]

                for signal in ending_signals_potential_variants:
                    bottom_text = (
                        soup.find("div", id="main-content").get_text().split(signal)
                    )
                    if len(bottom_text) == 2:
                        main_content = bottom_text[0].split(article_time)[1]
                        if signal == "--\n※ 編輯: ":
                            article_ip = bottom_text[1].split(" ")[1][1:]
                        else:
                            article_ip = bottom_text[1].split(" ")[0].strip()
                        break
        return main_content, article_ip
    except IndexError as e:
        logger.exception(f"{e}: Article's content and IP have problems.")
        return {"error": "Article's content and IP are incomplete."}


def parse_comments(
    soup: bs4.BeautifulSoup, article_time: str, article_timestamp
) -> tuple[int, int, int, list[dict]]:
    """
    parse article comments
    :param soup: bs4.BeautifulSoup
    :param article_time: article time
    :param article_timestamp: article timestamp
    :return: article comments
    """
    favor, against, arrow = 0, 0, 0
    comments = []
    article_comments = soup.find_all("div", "push")
    if article_comments:
        for comment in article_comments:
            if "warning-box" in comment.get("class"):
                continue
            commenter_info = (
                comment.find("span", class_="push-ipdatetime")
                .get_text()
                .strip()
                .split(" ")
            )

            # to handle author's sign having comments of another article
            if len(commenter_info) < 3:
                continue

            commenter_id = comment.find("span", class_="push-userid").get_text()
            comment_type = comment.find("span", class_="push-tag").get_text(strip=True)
            favor += 1 if comment_type == "推" else 0
            arrow += 1 if comment_type == "→" else 0
            against += 1 if comment_type == "噓" else 0

            month_date, commenter_ip, localized_timestamp = None, None, None
            if len(commenter_info) == 3 and article_time is not None:
                # Sometimes the commenter ip has not been recorded yet
                commenter_ip = commenter_info[-3] if len(commenter_info) >= 3 else None
                month_date = (
                    commenter_info[-2].split("/") if len(commenter_info) >= 3 else None
                )
                if month_date is not None:
                    comment_date = (
                        f"{article_time[-4:]}-{month_date[0]}-{month_date[1]}"
                    )
                    comment_time = commenter_info[-1].strip()
                    # to process article like: https://www.ptt.cc/bbs/Gossiping/M.1694607629.A.B47.html
                    if len(comment_time) != 5:
                        comment_time = comment_time[:5]
                    # to process article: https://www.ptt.cc/bbs/Gossiping/M.1695070048.A.60B.html (cpmmenter: funeasy)
                    if len(comment_time) < 5:
                        if len(comments) != 0:
                            comment_time = datetime.fromtimestamp(
                                comments[-1]["comment_time"]
                            ).strftime("%H:%M")
                        else:
                            # to handle: https://www.ptt.cc/bbs/HatePolitics/M.1693407881.A.DDD.html
                            # to handle: https://www.ptt.cc/bbs/Gossiping/M.1694656103.A.27D.html
                            if article_timestamp is not None:
                                comment_time = article_timestamp.strftime("%H:%M")
                    # to handle: https://www.ptt.cc/bbs/Gossiping/M.1692381678.A.441.html
                    if comment_time == "2023-08-19 02:l1":
                        comment_time = "2023-08-19 02:10"
                    try:
                        comment_timestamp = datetime.strptime(
                            f"{comment_date} {comment_time}", "%Y-%m-%d %H:%M"
                        )
                        localized_timestamp = TAIPEI_TIMEZONE.localize(
                            comment_timestamp
                        )
                    except ValueError as e:
                        # to handle: https://www.ptt.cc/bbs/HatePolitics/M.1574178562.A.4EE.html
                        logger.exception(f"{e}: Comment's timestamp is incomplete")
                        continue

            comment_content = (
                comment.find("span", class_="push-content").get_text().strip(": ")
            )
            comments.append(
                {
                    "commenter_id": commenter_id,
                    "commenter_ip": commenter_ip,
                    "comment_time": localized_timestamp.timestamp() + 59
                    if localized_timestamp
                    else None,
                    "comment_type": comment_type,
                    "comment_content": comment_content,
                }
            )
    return favor, against, arrow, comments


def create_page_idx(soup: BeautifulSoup, start_page: int) -> tuple[int, int]:
    """
    create page index with start page
    :param soup: bs4.BeautifulSoup
    :param start_page: start page
    :return: latest page and start page index
    """
    for trying in range(5):
        try:
            if soup.find_all("a", "btn wide")[1] is not None:
                # using previous button to get index
                prev_page_link = soup.find_all("a", "btn wide")[1].get("href")
                prev_idx = prev_page_link[
                    (prev_page_link.find("index") + 5): prev_page_link.find(".html")
                ]
                latest_page = int(prev_idx) + 1
                start_idx = int(prev_idx) + 1 - (start_page - 1)
                return latest_page, start_idx
        except IndexError as e:
            logger.exception(f"{e}: cannot find the previous page button.")


def get_num_announcements(soup: BeautifulSoup) -> int:
    """
    get num of announcement
    :param soup: bs4.BeautifulSoup
    :return: num of announcement
    """
    sep_div = soup.find("div", class_="r-list-sep")
    return len(sep_div.find_all_next("div", class_="r-ent")) if sep_div else 0


def exclude_announcements_from_titles(
    title_collections: bs4.element.ResultSet, num_announcement: int
) -> list:
    """
    get titles excluding announcement
    :param title_collections: list of title
    :param num_announcement: num of announcement
    :return: list of titles excluding announcement
    """
    return title_collections[:-num_announcement] if num_announcement > 0 else title_collections


def parse_article(page_response: requests.models.Response) -> dict:
    """
    parsing article including comments
    :param page_response: response object of page response
    :return: dict containing article information
    """

    soup = BeautifulSoup(page_response.text, "lxml")

    basic_info = parse_basic_info(
        article_basic_info=soup.find_all("div", "article-metaline")
    )
    if isinstance(basic_info, tuple):
        (
            article_author,
            article_title,
            article_time,
            article_timestamp,
            localized_article_timestamp,
        ) = basic_info
    else:
        (
            article_author,
            article_title,
            article_time,
            article_timestamp,
            localized_article_timestamp,
        ) = (None, None, None, None, None)

    content_and_ip = parse_article_content_and_ip(soup=soup, article_time=article_time)
    if isinstance(content_and_ip, tuple):
        main_content, article_ip = content_and_ip
    else:
        main_content, article_ip = (None, None)

    favor, against, arrow, comments = parse_comments(
        soup=soup, article_time=article_time, article_timestamp=article_timestamp
    )

    article_info = {
        "author": article_author,
        "ipaddress": article_ip,
        "title": article_title,
        "time": localized_article_timestamp,
        "main_content": main_content,
        "last_crawled_datetime": datetime.now().timestamp(),
        "num_of_comment": favor + against + arrow,
        "num_of_favor": favor,
        "num_of_against": against,
        "num_of_arrow": arrow,
        "comments": comments,
    }
    return article_info


def crawl_articles(
    base_url: str, start_page: int, pages: int, crawling_logger: logging.Logger = None
):
    """
    crawl articles from ptt
    :param base_url: original url
    :param start_page: crawling start page (1 = the last page)
    :param pages: crawling how many pages
    :param crawling_logger: logger
    :return: list of articles
    """
    if pages > start_page:
        logger.info("Page Error: pages > start_page")
        return None
    else:
        headers = {"user-agent": ua.random}
        current_session = requests.session()
        current_request = current_session.get(base_url, headers=headers)

        if "over18" in current_request.url:
            current_session.post("https://www.ptt.cc/ask/over18", data=cookies)
            current_request = current_session.get(base_url, headers=headers)

        soup = BeautifulSoup(current_request.text, "lxml")

        latest_page, start_idx = create_page_idx(soup=soup, start_page=start_page)

        crawling_results = []
        idx_collections = [i for i in range(start_idx, start_idx + pages)]
        for idx in idx_collections:
            num_insert, num_update, num_ignore = 0, 0, 0
            current_page_url = (
                f"{base_url[:-5]}{idx}.html" if idx != latest_page else base_url
            )

            soup = BeautifulSoup(
                current_session.get(current_page_url, headers=headers).text, "lxml"
            )
            current_page_title_collections = soup.find_all("div", "r-ent")

            # check whether this page has announcement
            num_announcement = get_num_announcements(soup=soup)
            current_page_title_collections_excluding_announcement = (
                exclude_announcements_from_titles(
                    title_collections=current_page_title_collections,
                    num_announcement=num_announcement,
                )
            )

            logger.info(
                f"-- start crawling: page {idx} (current_page_url: {current_page_url}) --"
            )

            for title in current_page_title_collections_excluding_announcement:
                title_link = title.find("a")
                if title_link:
                    article_url = urllib.parse.urljoin(
                        current_page_url, title_link.get("href")
                    )
                    ptt_board = decide_ptt_board(url=article_url)

                    if crawling_logger.name == "logger_test_integration":
                        ptt_board = "testing_collection"

                    if not is_article_existing(
                        target_collection=ptt_board, article_url=article_url
                    ):
                        for i in range(5):
                            try:
                                if (
                                    parse_article(
                                        current_session.get(
                                            article_url, headers=headers
                                        )
                                    )
                                    is not None
                                ):
                                    break
                            except requests.exceptions.ConnectionError as e:
                                logger.error(
                                    f"{e}: cannot connect to the server - wait 60 seconds to restart."
                                )
                                time.sleep(SLEEP_INTERVAL_IF_GET_CAUGHT)
                                headers = {"user-agent": ua.random}

                        parsing_result = parse_article(current_session.get(article_url))
                        if "error" in parsing_result.keys():
                            logger.error(
                                f"Error: {parsing_result['error']} - {article_url}."
                            )

                        num_insert += 1
                        logger.debug(f"Insert: {article_url}")

                        article_data = {
                            "article_page_idx": idx,
                            "article_url": article_url,
                            "article_data": parsing_result,
                        }
                        crawling_results.append(article_data)
                    else:
                        num_comments = get_article_num_of_comments(
                            target_collection=ptt_board, article_url=article_url
                        )
                        parsing_result = parse_article(current_session.get(article_url))
                        if "error" in parsing_result.keys():
                            logger.error(
                                f"Error: {parsing_result['error']} - {article_url}."
                            )
                        else:
                            if parsing_result["num_of_comment"] != num_comments:
                                num_update += 1
                                logger.debug(f"Update: {article_url}")

                                update_article(
                                    target_collection=ptt_board,
                                    article_url=article_url,
                                    new_data=parsing_result,
                                    previous_num_comments=num_comments,
                                )
                            else:
                                num_ignore += 1
                                logger.debug(f"Ignore: {article_url}")

                time.sleep(SLEEP_INTERVAL_BETWEEN_ARTICLES)

            crawling_logs = {
                "crawler": crawling_logger.name,
                "current_page_url": current_page_url,
                "crawling_data_insert": num_insert,
                "crawling_data_update": num_update,
                "crawling_data_ignore": num_ignore,
            }

            crawling_logger.info(json.dumps(crawling_logs))
            time.sleep(SLEEP_INTERVAL_BETWEEN_PAGES)
        return crawling_results


def set_range_and_crawl(
    base_url: str,
    ptt_board: str,
    logger_assigned,
    start_generation: int,
    end_generation: int,
):
    for i in range(start_generation, end_generation):
        crawl_results = crawl_articles(base_url, i, 1, crawling_logger=logger_assigned)
        if crawl_results:
            collection = db[ptt_board]
            collection.insert_many(crawl_results)


def create_dag_from_latest_to_middle(
    dag_id: str,
    schedule: Union[str, timedelta],
    base_url: str,
    logger_assigned,
):
    ptt_board = decide_ptt_board(url=base_url)

    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        schedule=schedule,
        catchup=False,
    )

    start = EmptyOperator(task_id="start", dag=dag)

    crawl = PythonOperator(
        task_id="crawl",
        python_callable=set_range_and_crawl,
        op_args=[
            base_url,
            ptt_board,
            logger_assigned,
            PAGE_GENERATION_LATEST,
            PAGE_GENERATION_MIDDLE,
        ],
        dag=dag,
    )

    check_ip = PythonOperator(
        task_id="check_ip",
        python_callable=update_wrong_ip,
        op_args=[ptt_board],
        dag=dag,
    )

    remove_duplicate = PythonOperator(
        task_id="remove_duplicate",
        python_callable=delete_duplicates,
        op_args=[ptt_board],
        dag=dag,
    )

    end = EmptyOperator(task_id="end", dag=dag)

    start >> crawl >> check_ip >> remove_duplicate >> end

    return dag


def create_dag_from_middle_to_ancient(
    dag_id: str,
    schedule: Union[str, timedelta],
    base_url: str,
    logger_assigned,
):
    ptt_board = decide_ptt_board(url=base_url)

    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        schedule=schedule,
        catchup=False,
    )

    start = EmptyOperator(task_id="start", dag=dag)

    crawl = PythonOperator(
        task_id="crawl",
        python_callable=set_range_and_crawl,
        op_args=[
            base_url,
            ptt_board,
            logger_assigned,
            PAGE_GENERATION_MIDDLE,
            PAGE_GENERATION_ANCIENT,
        ],
        dag=dag,
    )

    end = EmptyOperator(task_id="end", dag=dag)

    start >> crawl >> end

    return dag


def create_dag_from_ancient_to_earliest(
    dag_id: str,
    schedule: Union[str, timedelta],
    base_url: str,
    logger_assigned,
):
    ptt_board = decide_ptt_board(url=base_url)

    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        schedule=schedule,
        catchup=False,
    )

    start = EmptyOperator(task_id="start", dag=dag)

    crawl = PythonOperator(
        task_id="crawl",
        python_callable=set_range_and_crawl,
        op_args=[
            base_url,
            ptt_board,
            logger_assigned,
            PAGE_GENERATION_ANCIENT,
            PAGE_GENERATION_EARLIEST,
        ],
        dag=dag,
    )

    end = EmptyOperator(task_id="end", dag=dag)

    start >> crawl >> end

    return dag


dag_gossips_from_latest_to_middle = create_dag_from_latest_to_middle(
    dag_id="crawl_ptt_gossips_from_latest_to_middle",
    schedule="*/10 * * * *",
    base_url="https://www.ptt.cc/bbs/Gossiping/index.html",
    logger_assigned=logger_gossip_from_latest_to_middle,
)

dag_politic_from_latest_to_middle = create_dag_from_latest_to_middle(
    dag_id="crawl_ptt_politic_from_latest_to_middle",
    schedule="*/10 * * * *",
    base_url="https://www.ptt.cc/bbs/HatePolitics/index.html",
    logger_assigned=logger_politic_from_latest_to_middle,
)

dag_gossips_from_middle_to_ancient = create_dag_from_middle_to_ancient(
    dag_id="crawl_ptt_gossips_from_middle_to_ancient",
    schedule=timedelta(days=1),
    base_url="https://www.ptt.cc/bbs/Gossiping/index.html",
    logger_assigned=logger_gossip_from_middle_to_ancient,
)

dag_politic_from_middle_to_ancient = create_dag_from_middle_to_ancient(
    dag_id="crawl_ptt_politic_from_middle_to_ancient",
    schedule=timedelta(days=1),
    base_url="https://www.ptt.cc/bbs/HatePolitics/index.html",
    logger_assigned=logger_politic_from_middle_to_ancient,
)

dag_gossips_from_ancient_to_earliest = create_dag_from_ancient_to_earliest(
    dag_id="crawl_ptt_gossips_from_ancient_to_earliest",
    schedule=timedelta(days=2),
    base_url="https://www.ptt.cc/bbs/Gossiping/index.html",
    logger_assigned=logger_gossip_from_ancient_to_earliest,
)

dag_politic_from_ancient_to_earliest = create_dag_from_ancient_to_earliest(
    dag_id="crawl_ptt_politic_from_ancient_to_earliest",
    schedule=timedelta(days=2),
    base_url="https://www.ptt.cc/bbs/HatePolitics/index.html",
    logger_assigned=logger_politic_from_ancient_to_earliest,
)
