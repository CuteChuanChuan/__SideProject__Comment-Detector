import json
import jieba.analyse
from utils_dashboard.utils_mongodb import redis_conn

DICT_FILE = "utils_dashboard/tc_dict.txt"
STOP_FILE = "utils_dashboard/stopwords.txt"
TC_FONT_PATH = "utils_dashboard/NotoSerifTC-Regular.otf"

jieba.set_dictionary(DICT_FILE)
jieba.analyse.set_stop_words(STOP_FILE)


NUM_KEYWORDS = 5


def extract_top_n_keywords(text_data: list[dict], n_keywords: int) -> list[tuple]:
    """
    return top n keywords with their weights
    :param text_data: text data
    :param n_keywords: number of keywords
    """
    unwanted_words = ["XD"]
    for word in unwanted_words:
        jieba.del_word(word)

    combined_text = " ".join([text["article_text"] for text in text_data if "https://" not in text["article_text"]])
    segmented_text = " ".join(jieba.cut(combined_text))
    keywords_with_weights = jieba.analyse.extract_tags(segmented_text, topK=n_keywords, withWeight=True)
    return keywords_with_weights


def store_top_n_keywords():
    title_gossip_days_1 = extract_top_n_keywords(
        text_data=json.loads(redis_conn.get(name="past_n_days_article_title_gossip_1").decode("utf-8")),
        n_keywords=NUM_KEYWORDS
    )
    title_gossip_days_3 = extract_top_n_keywords(
        text_data=json.loads(redis_conn.get(name="past_n_days_article_title_gossip_3").decode("utf-8")),
        n_keywords=NUM_KEYWORDS
    )
    title_gossip_days_7 = extract_top_n_keywords(
        text_data=json.loads(redis_conn.get(name="past_n_days_article_title_gossip_7").decode("utf-8")),
        n_keywords=NUM_KEYWORDS
    )
    title_politics_days_1 = extract_top_n_keywords(
        text_data=json.loads(redis_conn.get(name="past_n_days_article_title_politics_1").decode("utf-8")),
        n_keywords=NUM_KEYWORDS
    )
    title_politics_days_3 = extract_top_n_keywords(
        text_data=json.loads(redis_conn.get(name="past_n_days_article_title_politics_3").decode("utf-8")),
        n_keywords=NUM_KEYWORDS
    )
    title_politics_days_7 = extract_top_n_keywords(
        text_data=json.loads(redis_conn.get(name="past_n_days_article_title_politics_7").decode("utf-8")),
        n_keywords=NUM_KEYWORDS
    )
    redis_conn.set("keyword_title_gossip_1", json.dumps(title_gossip_days_1))
    redis_conn.set("keyword_title_gossip_3", json.dumps(title_gossip_days_3))
    redis_conn.set("keyword_title_gossip_7", json.dumps(title_gossip_days_7))
    redis_conn.set("keyword_title_politics_1", json.dumps(title_politics_days_1))
    redis_conn.set("keyword_title_politics_3", json.dumps(title_politics_days_3))
    redis_conn.set("keyword_title_politics_7", json.dumps(title_politics_days_7))

    comment_gossip_days_1 = extract_top_n_keywords(
        text_data=json.loads(redis_conn.get(name="past_n_days_comments_gossip_1").decode("utf-8")),
        n_keywords=NUM_KEYWORDS
    )
    comment_gossip_days_3 = extract_top_n_keywords(
        text_data=json.loads(redis_conn.get(name="past_n_days_comments_gossip_3").decode("utf-8")),
        n_keywords=NUM_KEYWORDS
    )
    comment_gossip_days_7 = extract_top_n_keywords(
        text_data=json.loads(redis_conn.get(name="past_n_days_comments_gossip_7").decode("utf-8")),
        n_keywords=NUM_KEYWORDS
    )
    comment_politics_days_1 = extract_top_n_keywords(
        text_data=json.loads(redis_conn.get(name="past_n_days_comments_politics_1").decode("utf-8")),
        n_keywords=NUM_KEYWORDS
    )
    comment_politics_days_3 = extract_top_n_keywords(
        text_data=json.loads(redis_conn.get(name="past_n_days_comments_politics_3").decode("utf-8")),
        n_keywords=NUM_KEYWORDS
    )
    comment_politics_days_7 = extract_top_n_keywords(
        text_data=json.loads(redis_conn.get(name="past_n_days_comments_politics_7").decode("utf-8")),
        n_keywords=NUM_KEYWORDS
    )
    redis_conn.set("keyword_comments_gossip_1", json.dumps(comment_gossip_days_1))
    redis_conn.set("keyword_comments_gossip_3", json.dumps(comment_gossip_days_3))
    redis_conn.set("keyword_comments_gossip_7", json.dumps(comment_gossip_days_7))
    redis_conn.set("keyword_comments_politics_1", json.dumps(comment_politics_days_1))
    redis_conn.set("keyword_comments_politics_3", json.dumps(comment_politics_days_3))
    redis_conn.set("keyword_comments_politics_7", json.dumps(comment_politics_days_7))


def retrieve_top_n_keywords(target_collection: str, n_days: int, source: str):
    source = "title" if source == "標題" else "comments"
    return json.loads(redis_conn.get(f"keyword_{source}_{target_collection}_{n_days}").decode("utf-8"))


if __name__ == '__main__':
    # store_top_n_keywords()
    print(retrieve_top_n_keywords(target_collection="gossip", n_days=1, source="標題"))
