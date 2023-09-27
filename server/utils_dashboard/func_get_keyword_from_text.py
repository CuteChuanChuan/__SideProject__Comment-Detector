import jieba.analyse


DICT_FILE = "utils_dashboard/tc_dict.txt"
STOP_FILE = "utils_dashboard/stopwords.txt"
TC_FONT_PATH = "utils_dashboard/NotoSerifTC-Regular.otf"

jieba.set_dictionary(DICT_FILE)
jieba.analyse.set_stop_words(STOP_FILE)


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

#
# if __name__ == '__main__':
#     yesterday_data_title = get_past_n_days_article_title("gossip", 1)
#     yesterday_data_comments = get_past_n_days_comments("gossip", 1)
#
#     top_keywords_info = extract_top_n_keywords(yesterday_data_comments, 7)
#     for keyword, weight in top_keywords_info:
#         print(f"Keyword: {keyword}, Weight: {weight}")
#
#     print("----------------------\n\n----------------------------")
#
#     top_keywords_info = extract_top_n_keywords(yesterday_data_title, 7)
#     for keyword, weight in top_keywords_info:
#         print(f"Keyword: {keyword}, Weight: {weight}")
