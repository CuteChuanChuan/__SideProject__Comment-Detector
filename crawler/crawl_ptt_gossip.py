import time
import logging
import requests
import urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime
from fake_useragent import UserAgent
from operations_mongo import article_existing, check_article_comments_num, delete_article

cookies = {"from": "/bbs/Gossiping/index.html", "yes": "yes"}

ua = UserAgent()


def parse_article(page_response: requests.models.Response) -> dict:
    """
    analyze article including comments
    :param page_response: response object of page response
    :return: dict containing article information
    """
    soup = BeautifulSoup(page_response.text, "lxml")

    article_meta_info = soup.find_all("div", "article-metaline")
    try:
        article_author = article_meta_info[0].find("span", "article-meta-value").get_text()
        article_title = article_meta_info[1].find("span", "article-meta-value").get_text()
        article_time = article_meta_info[2].find("span", "article-meta-value").get_text()
        article_time_timestamp = datetime.strptime(article_time, '%a %b %d %H:%M:%S %Y').timestamp()

        # print(f"{article_author} - {article_title} - {article_time}")
    except IndexError as e:
        print(e)
        article_author, article_title, article_time, article_time_timestamp = None, None, None, None

    try:
        soup.find("div", id="main-content")
        bottom_text = soup.find("div", id="main-content").get_text().split("--\n※ 發信站: 批踢踢實業坊(ptt.cc), 來自: ")

        # to handle: https://www.ptt.cc/bbs/Gossiping/M.1694539823.A.DEE.html (no --\n※ 發信站:)
        # to handle: https://www.ptt.cc/bbs/Gossiping/M.1694532584.A.102.html (--\n\n※ 發信站:)
        # to handle: https://www.ptt.cc/bbs/Gossiping/M.1694678215.A.764.html (no --\n※ 發信站:)
        # to handle: https://www.ptt.cc/bbs/Gossiping/M.1694572013.A.B01.html
        # to handle: https://www.ptt.cc/bbs/Gossiping/M.1694694211.A.8CB.html
        if len(bottom_text) == 2:
            main_content = bottom_text[0].split(article_time)[1]
            article_ip = bottom_text[1].split(" ")[0].strip()
        else:
            bottom_text = soup.find("div", id="main-content").get_text().split("--\n※ 編輯: ")
            if len(bottom_text) == 2:
                main_content = bottom_text[0].split(article_time)[1]
                print(f"main_content: {main_content}")
                article_ip = bottom_text[1].split(" ")[1][1:]
                print(f"article_ip: {article_ip}")
            else:
                bottom_text = soup.find("div", id="main-content").get_text().split("--\n\n※ 發信站: 批踢踢實業坊(ptt.cc), 來自: ")
                main_content = bottom_text[0].split(article_time)[1]
                article_ip = bottom_text[1].split(" ")[0].strip()
                print(f"main_content: {main_content}")
                print(f"article_ip: {article_ip}")

    except IndexError as e:
        print(f"Main content and Article IP error: {e}")
        main_content, article_ip = None, None

    favor, against, arrow = 0, 0, 0
    comments = []

    article_comments = soup.find_all("div", "push")
    if article_comments:
        for comment in article_comments:
            if "warning-box" in comment.get("class"):
                continue
            commenter_info = comment.find("span", class_="push-ipdatetime").get_text().strip().split(" ")

            # to handle author's sign having comments of another article
            if len(commenter_info) < 3:
                continue
            commenter_id = comment.find("span", class_="push-userid").get_text()
            comment_type = comment.find("span", class_="push-tag").get_text(strip=True)

            favor += 1 if comment_type == "推" else 0
            arrow += 1 if comment_type == "→" else 0
            against += 1 if comment_type == "噓" else 0

            if len(commenter_info) == 3 and article_time is not None:
                # Sometimes the commenter ip has not been recorded yet
                commenter_ip = commenter_info[-3] if len(commenter_info) >= 3 else None
                month_date = commenter_info[-2].split("/") if len(commenter_info) >= 3 else None
                if month_date is not None:
                    comment_date = f"{article_time[-4:]}-{month_date[0]}-{month_date[1]}"
                    comment_time = commenter_info[-1].strip()

                    # to process article like: https://www.ptt.cc/bbs/Gossiping/M.1694607629.A.B47.html
                    if len(comment_time) != 5:
                        comment_time = comment_time[:5]
                    comment_timestamp = datetime.strptime(f"{comment_date} {comment_time}", '%Y-%m-%d %H:%M').timestamp() + 59
                else:
                    month_date, comment_timestamp = None, None

            else:
                commenter_ip, comment_timestamp = None, None
            comment_content = comment.find("span", class_="push-content").get_text().strip(": ")
            comments.append({"commenter_id": commenter_id,
                             "commenter_ip": commenter_ip,
                             "comment_time": comment_timestamp,
                             # "comment_latency": comment_timestamp - article_time_timestamp,
                             "comment_type": comment_type,
                             "comment_content": comment_content})
    article_info = {"author": article_author, "ipaddress": article_ip,
                    "title": article_title, "time": article_time_timestamp,
                    "main_content": main_content,
                    "last_crawled_datetime": datetime.now().timestamp(),
                    "num_of_comment": favor + against + arrow,
                    "num_of_favor": favor,
                    "num_of_against": against,
                    "num_of_arrow": arrow,
                    "comments": comments}
    return article_info


def crawl_articles(base_url: str, start_page: int, pages: int):
    """
    crawl articles from ptt
    :param base_url: original url
    :param start_page: crawling start page (1 = the last page)
    :param pages: crawling how many pages
    :return: list of articles
    """
    if pages > start_page:
        print("Page Error!")
        return None
    else:
        headers = {'user-agent': ua.random}
        current_session = requests.session()
        current_request = current_session.get(base_url, headers=headers)

        if "over18" in current_request.url:
            current_session.post("https://www.ptt.cc/ask/over18", data=cookies)
            current_request = current_session.get(base_url)

        soup = BeautifulSoup(current_request.text, "lxml")
        for trying in range(5):
            try:
                if soup.find_all("a", "btn wide")[1] is not None:
                    break
            except IndexError as e:
                print(e)
                continue
        previous_page_link = soup.find_all("a", "btn wide")[1].get("href")  # using previous button to get index
        previous_idx = previous_page_link[(previous_page_link.find("index") + 5): previous_page_link.find(".html")]
        latest_page = int(previous_idx) + 1
        start_idx = int(previous_idx) + 1 - (start_page - 1)
        # if (BeautifulSoup(current_session.get(base_url[:-5] + str(start_idx) + ".html").text, "lxml")
        #         .find(string="500 - Internal Server Error")):
        #     start_idx -= 1

        crawling_results = []
        idx_list = [i for i in range(start_idx, start_idx + pages)]

        for idx in idx_list:
            current_page_url = f"{base_url[:-5]}{idx}.html" if idx != latest_page else base_url
            current_page_request = current_session.get(current_page_url, headers=headers)
            soup = BeautifulSoup(current_page_request.text, "lxml")

            # check whether this page has announcement
            sep_div = soup.find('div', class_='r-list-sep')
            number_of_announcement = len(sep_div.find_all_next('div', class_='r-ent')) if sep_div else 0
            current_page_title_list = soup.find_all("div", "r-ent")
            current_page_title_list_excluding_announcement = current_page_title_list[:-number_of_announcement] \
                if number_of_announcement > 0 else current_page_title_list

            print(f"--- start crawling: page {idx} (current_page_url: {current_page_url}) ---")
            for title in current_page_title_list_excluding_announcement:
                title_link = title.find("a")
                if title_link:
                    article_url = urllib.parse.urljoin(current_page_url, title_link.get("href"))
                    ptt_board = "gossip" if "Gossiping" in article_url else "politics"

                    if not article_existing(target_collection=ptt_board, search_url=article_url):
                        for i in range(5):
                            try:
                                parsed_data = parse_article(current_session.get(article_url, headers=headers))
                            except requests.exceptions.ConnectionError as e:
                                print(e)
                                time.sleep(75)
                                headers = {"user-agent": ua.random}
                            else:
                                article_data = {"article_page_idx": idx,
                                                "article_url": article_url,
                                                "article_data": parsed_data}
                                break
                        print(f"Prepared to add Article {article_url}.")
                    else:
                        num_comments = check_article_comments_num(target_collection=ptt_board, search_url=article_url)
                        parsing_result = parse_article(current_session.get(article_url))
                        if parsing_result["num_of_comment"] != num_comments:
                            delete_article(target_collection=ptt_board, target_url=article_url)
                            article_data = {"article_page_idx": idx,
                                            "article_url": article_url,
                                            "article_data": parsing_result}
                            print(f"Deleted and Re-Inserted Article {article_url}.")
                        else:
                            print(f"Ignore Article {article_url} for no changes have been made.")
                            continue
                    crawling_results.append(article_data)
                time.sleep(5.0)
            print(f"--- finish crawling: page {idx} ---")
            time.sleep(20.0)
        return crawling_results


if __name__ == "__main__":
    base_url = "https://www.ptt.cc/bbs/Gossiping/index.html"
    ptt_board = "gossip" if "Gossiping" in base_url else "politics"
    # for i in range(291, 366):
    crawl_results = crawl_articles(base_url, 328, 1)
    # results = crawl_articles("https://www.ptt.cc/bbs/Gossiping/index.html", 265, 5)

