import json
import os
import bs4
import time
import pytz
import logging
import requests
import urllib.parse
from airflow import DAG
from typing import Union
from loguru import logger
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pymongo import MongoClient
from fake_useragent import UserAgent
from config_crawl import default_args
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

load_dotenv(verbose=True)
uri = os.getenv("ATLAS_URI", "None")
client = MongoClient(uri)
db = client.ptt

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
    diagnose=False,
)

crawler_gossip_latest = logging.getLogger("crawler_gossip_latest")
crawler_gossip_earlier = logging.getLogger("crawler_gossip_earlier")
crawler_gossip_much_earlier = logging.getLogger("crawler_gossip_much_earlier")
crawler_politic_latest = logging.getLogger("crawler_politic_latest")
crawler_politic_earlier = logging.getLogger("crawler_politic_earlier")
crawler_politic_much_earlier = logging.getLogger("crawler_politic_much_earlier")


# --- Functions related to mongodb ---
def article_existing(search_url: str, target_collection: str) -> bool:
    """
    check whether article already exists in mongodb
    :param target_collection: target collection
    :param search_url: article url
    :return: True if article exists, False otherwise
    """
    return (
        True if db[target_collection].find_one({"article_url": search_url}) else False
    )


def update_article(
    search_url: str, new_data: dict, previous_num_comments: int, target_collection: str
):
    """
    update article in mongodb
    :param target_collection: target collection
    :param search_url: article url
    :param new_data: new data
    :param previous_num_comments: previous number of comments
    """
    num_of_favor = new_data["num_of_favor"]
    num_of_against = new_data["num_of_against"]
    num_of_arrow = new_data["num_of_arrow"]
    num_of_comment = num_of_favor + num_of_against + num_of_arrow
    new_comments = new_data["comments"][previous_num_comments:]

    db[target_collection].update_one(
        {"article_url": search_url},
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
            {"article_url": search_url}, {"$push": {"article_data.comments": comment}}
        )


def check_article_comments_num(search_url: str, target_collection: str) -> int:
    """
    get number of comments for article
    :param target_collection: target collection
    :param search_url: article url
    :return: number of comments
    """
    return db[target_collection].find_one({"article_url": search_url})["article_data"][
        "num_of_comment"
    ]


def update_wrong_ip(target_collection: str):
    """
    find out documents with error ip which includes space at the end before update the ip address
    """
    result = list(
        db[target_collection].find({"article_data.ipaddress": {"$regex": "\s"}})
    )
    for _ in result:
        new_ip = _["article_data"]["ipaddress"].split(" ")[0]
        new_ip_values = {"$set": {"article_data.ipaddress": new_ip}}
        db[target_collection].update_many(
            {"article_data.ipaddress": {"$regex": "\s"}}, new_ip_values
        )


def delete_duplicates(target_collection: str):
    """
    delete duplicated articles in mongodb
    :param target_collection: target collection
    """
    collection = db[target_collection]
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
    duplicates = collection.aggregate(pipeline)

    for duplicate in duplicates:
        article_url = duplicate["_id"]
        duplicate_ids = duplicate["ids"]
        logger.info(f"Duplicate article_url: {article_url}, count: {len(duplicate_ids)}")

        for id_to_delete in duplicate_ids[1:]:
            collection.delete_one({"_id": id_to_delete})


# --- Functions related to crawling ---
def get_article_info(meta_info: bs4.element.ResultSet, _idx: int) -> str:
    """
    get article information
    :param meta_info: article info part
    :param _idx: index
    :return: str
    """
    return meta_info[_idx].find("span", "article-meta-value").get_text()


def parse_article(page_response: requests.models.Response) -> dict:
    """
    analyze article including comments
    :param page_response: response object of page response
    :return: dict containing article information
    """
    taipei = pytz.timezone("Asia/Taipei")

    soup = BeautifulSoup(page_response.text, "lxml")

    article_meta_info = soup.find_all("div", "article-metaline")

    article_author, article_title, article_time, localized_article_timestamp = (
        None,
        None,
        None,
        None,
    )
    try:
        article_author = get_article_info(article_meta_info, 0)
        article_title = get_article_info(article_meta_info, 1)
        article_time = get_article_info(article_meta_info, 2)
        try:
            article_timestamp = datetime.strptime(article_time, "%a %b %d %H:%M:%S %Y")
        except ValueError:
            # to handle: https://www.ptt.cc/bbs/HatePolitics/M.1694139970.A.129.html (only occurred once)
            # print("ERROR: === Article TIme -> Manually insert value ===")
            article_time = "Fri Sep 8 10:26:08 2023"
            article_timestamp = datetime.strptime(article_time, "%a %b %d %H:%M:%S %Y")
        localized_article_timestamp = taipei.localize(article_timestamp).timestamp()
    except IndexError as e:
        logger.exception(f"{e}: article author, title and time is not found")
        return {"error": "Not ordinary article"}

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
                bottom_text = (
                    soup.find("div", id="main-content").get_text().split("--\n※ 編輯: ")
                )
                if len(bottom_text) == 2:
                    main_content = bottom_text[0].split(article_time)[1]
                    article_ip = bottom_text[1].split(" ")[1][1:]
                else:
                    bottom_text = (
                        soup.find("div", id="main-content")
                        .get_text()
                        .split("--\n\n※ 發信站: 批踢踢實業坊(ptt.cc), 來自: ")
                    )
                    if len(bottom_text) == 2:
                        main_content = bottom_text[0].split(article_time)[1]
                        article_ip = bottom_text[1].split(" ")[0].strip()
                    else:
                        bottom_text = (
                            soup.find("div", id="main-content")
                            .get_text()
                            .split("※ 發信站: 批踢踢實業坊(ptt.cc), 來自: ")
                        )
                        if len(bottom_text) == 2:
                            main_content = bottom_text[0].split(article_time)[1]
                            article_ip = bottom_text[1].split(" ")[0].strip()
    except IndexError as e:
        logger.exception(f"{e}: Main content and Article IP error")

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
                        localized_timestamp = taipei.localize(comment_timestamp)
                    except ValueError as e:
                        # to handle: https://www.ptt.cc/bbs/HatePolitics/M.1574178562.A.4EE.html
                        logger.exception(f"{e}: comment_timestamp error")
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
                    # "comment_latency": comment_timestamp - article_time_timestamp,
                    "comment_content": comment_content,
                }
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


def crawl_articles(base_url: str, start_page: int, pages: int, crawling_logger: logging.Logger = None):
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

        prev_page_link, prev_idx, latest_page, start_idx = None, None, None, None
        for trying in range(5):
            try:
                if soup.find_all("a", "btn wide")[1] is not None:
                    # using previous button to get index
                    prev_page_link = soup.find_all("a", "btn wide")[1].get("href")
                    prev_idx = prev_page_link[
                        (prev_page_link.find("index") + 5) : prev_page_link.find(
                            ".html"
                        )
                    ]
                    latest_page = int(prev_idx) + 1
                    start_idx = int(prev_idx) + 1 - (start_page - 1)
                    break
            except IndexError as e:
                logger.exception(f"{e}: cannot find the previous page button.")
                continue

        # if (BeautifulSoup(current_session.get(base_url[:-5] + str(start_idx) + ".html").text, "lxml")
        #         .find(string="500 - Internal Server Error")):
        #     start_idx -= 1

        crawling_results = []
        idx_list = [i for i in range(start_idx, start_idx + pages)]
        for idx in idx_list:
            num_insert, num_update, num_ignore = 0, 0, 0

            current_page_url = (
                f"{base_url[:-5]}{idx}.html" if idx != latest_page else base_url
            )
            current_page_request = current_session.get(
                current_page_url, headers=headers
            )
            soup = BeautifulSoup(current_page_request.text, "lxml")

            # check whether this page has announcement
            sep_div = soup.find("div", class_="r-list-sep")
            num_announcement = (
                len(sep_div.find_all_next("div", class_="r-ent")) if sep_div else 0
            )
            current_page_title_list = soup.find_all("div", "r-ent")
            current_page_title_list_excluding_announcement = (
                current_page_title_list[:-num_announcement]
                if num_announcement > 0
                else current_page_title_list
            )

            logger.info(
                f"-- start crawling: page {idx} (current_page_url: {current_page_url}) --"
            )

            for title in current_page_title_list_excluding_announcement:
                title_link = title.find("a")
                if title_link:
                    article_url = urllib.parse.urljoin(
                        current_page_url, title_link.get("href")
                    )
                    ptt_board = "gossip" if "Gossiping" in article_url else "politics"

                    if not article_existing(
                        target_collection=ptt_board, search_url=article_url
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
                                logger.exception(
                                    f"{e}: cannot connect to the server - wait 60 seconds to restart."
                                )
                                time.sleep(60)
                                headers = {"user-agent": ua.random}
                        parsing_result = parse_article(current_session.get(article_url))
                        if "error" in parsing_result.keys():
                            logger.error(
                                f"Error: {parsing_result['error']} - {article_url}."
                            )
                            continue

                        num_insert += 1
                        logger.debug(f"Insert: {article_url}")

                        article_data = {
                            "article_page_idx": idx,
                            "article_url": article_url,
                            "article_data": parsing_result,
                        }
                        crawling_results.append(article_data)
                    else:
                        num_comments = check_article_comments_num(
                            target_collection=ptt_board, search_url=article_url
                        )
                        parsing_result = parse_article(current_session.get(article_url))
                        if "error" in parsing_result.keys():
                            logger.error(
                                f"Error: {parsing_result['error']} - {article_url}."
                            )
                            continue
                        if parsing_result["num_of_comment"] != num_comments:
                            num_update += 1
                            logger.debug(f"Update: {article_url}")

                            update_article(
                                target_collection=ptt_board,
                                search_url=article_url,
                                new_data=parsing_result,
                                previous_num_comments=num_comments,
                            )
                        else:
                            num_ignore += 1
                            logger.debug(f"Ignore: {article_url}")
                            continue
                time.sleep(4.0)
            crawling_logs = {"crawler": crawling_logger.name,
                             "current_page_url": current_page_url,
                             "crawling_data_insert": num_insert,
                             "crawling_data_update": num_update,
                             "crawling_data_ignore": num_ignore}
            crawling_logger.info(
                json.dumps(crawling_logs)
            )
            # logger.info(
            #     f"-- finish crawling: page {idx} [Insert: {num_insert}, Update: {num_update}, Ignore: {num_ignore}] --"
            # )

            time.sleep(9.0)
        return crawling_results


def crawl_ptt_latest(base_url: str, ptt_board: str, logger_assigned):
    """ """
    for i in range(1, 5):
        crawl_results = crawl_articles(base_url, i, 1, crawling_logger=logger_assigned)
        if crawl_results:
            collection = db[ptt_board]
            collection.insert_many(crawl_results)


def crawl_ptt_history(base_url: str, ptt_board: str, logger_assigned):
    for i in range(5, 5000):
        crawl_results = crawl_articles(base_url, i, 1, crawling_logger=logger_assigned)
        if crawl_results:
            collection = db[ptt_board]
            collection.insert_many(crawl_results)


def crawl_ptt_history_more_earlier(base_url: str, ptt_board: str, logger_assigned):
    for i in range(5000, 12000):
        crawl_results = crawl_articles(base_url, i, 1, crawling_logger=logger_assigned)
        if crawl_results:
            collection = db[ptt_board]
            collection.insert_many(crawl_results)


def create_dag_historical_data(
    dag_id: str, schedule_interval: Union[str, timedelta], base_url: str, logger_assigned
):
    ptt_board = "gossip" if "Gossiping" in base_url else "politics"

    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        schedule_interval=schedule_interval,
        catchup=False,
    )

    start = EmptyOperator(task_id="start", dag=dag)

    crawl = PythonOperator(
        task_id="crawl",
        python_callable=crawl_ptt_history,
        op_args=[base_url, ptt_board, logger_assigned],
        dag=dag,
    )

    end = EmptyOperator(task_id="end", dag=dag)

    start >> crawl >> end

    return dag


def create_dag_historical_data_more_earlier(
    dag_id: str, schedule_interval: Union[str, timedelta], base_url: str, logger_assigned
):
    ptt_board = "gossip" if "Gossiping" in base_url else "politics"

    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        schedule_interval=schedule_interval,
        catchup=False,
    )

    start = EmptyOperator(task_id="start", dag=dag)

    crawl = PythonOperator(
        task_id="crawl",
        python_callable=crawl_ptt_history_more_earlier,
        op_args=[base_url, ptt_board, logger_assigned],
        dag=dag,
    )

    end = EmptyOperator(task_id="end", dag=dag)

    start >> crawl >> end

    return dag


def create_dag_latest_data(
    dag_id: str, schedule_interval: Union[str, timedelta], base_url: str, logger_assigned
):
    ptt_board = "gossip" if "Gossiping" in base_url else "politics"

    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        schedule_interval=schedule_interval,
        catchup=False,
    )

    start = EmptyOperator(task_id="start", dag=dag)

    crawl = PythonOperator(
        task_id="crawl",
        python_callable=crawl_ptt_latest,
        op_args=[base_url, ptt_board, logger_assigned],
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


dag_gossips_history = create_dag_historical_data(
    dag_id="crawl_ptt_gossips_history",
    schedule_interval=timedelta(days=1),
    base_url="https://www.ptt.cc/bbs/Gossiping/index.html",
    logger_assigned=crawler_gossip_earlier
)

dag_politic_history = create_dag_historical_data(
    dag_id="crawl_ptt_politic_history",
    schedule_interval=timedelta(days=1),
    base_url="https://www.ptt.cc/bbs/HatePolitics/index.html",
    logger_assigned=crawler_politic_earlier
)

dag_gossips_latest = create_dag_latest_data(
    dag_id="crawl_ptt_gossips_latest",
    schedule_interval="*/10 * * * *",
    base_url="https://www.ptt.cc/bbs/Gossiping/index.html",
    logger_assigned=crawler_gossip_latest
)

dag_politic_latest = create_dag_latest_data(
    dag_id="crawl_ptt_politic_latest",
    schedule_interval="*/10 * * * *",
    base_url="https://www.ptt.cc/bbs/HatePolitics/index.html",
    logger_assigned=crawler_politic_latest
)

dag_gossips_history_more_earlier = create_dag_historical_data_more_earlier(
    dag_id="crawl_ptt_gossips_history_more_earlier",
    schedule_interval=timedelta(days=1),
    base_url="https://www.ptt.cc/bbs/Gossiping/index.html",
    logger_assigned=crawler_gossip_much_earlier
)

dag_politic_history_more_earlier = create_dag_historical_data_more_earlier(
    dag_id="crawl_ptt_politic_history_more_earlier",
    schedule_interval=timedelta(days=1),
    base_url="https://www.ptt.cc/bbs/HatePolitics/index.html",
    logger_assigned=crawler_politic_much_earlier
)

# if __name__ == "__main__":
#     crawl_articles("https://www.ptt.cc/bbs/Gossiping/index.html", 1224, 1)
