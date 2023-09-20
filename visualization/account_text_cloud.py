import os
import jieba
import jieba.analyse
from dotenv import load_dotenv
from wordcloud import WordCloud
from pymongo.mongo_client import MongoClient
import matplotlib.pyplot as plt

load_dotenv(verbose=True)

uri = os.getenv("ATLAS_URI", "None")
client = MongoClient(uri)
db = client[os.getenv("ATLAS_DATABASE", "ptt")]

DICT_FILE = "tc_dict.txt"
STOP_FILE = "stopwords.txt"
TC_FONT_PATH = "NotoSerifTC-Regular.otf"

jieba.set_dictionary(DICT_FILE)
jieba.analyse.set_stop_words(STOP_FILE)


def account_text_cloud(account_id: str):
    """
    generate text cloud of comments with account id
    :param account_id: ptt account id
    """
    gossip_collection, politics_collection, all_comments = db["gossip"], db["politics"], []

    gossip_cursor = gossip_collection.find({"article_data.comments.commenter_id": account_id},
                                           {'article_data.comments': 1, "article_url": 1, "_id": 0})
    politic_cursor = politics_collection.find({"article_data.comments.commenter_id": account_id},
                                              {'article_data.comments': 1, "article_url": 1, "_id": 0})

    for article in gossip_cursor:
        for comment in article["article_data"]["comments"]:
            if comment["commenter_id"] == account_id:
                all_comments.append(comment["comment_content"])

    for article in politic_cursor:
        for comment in article["article_data"]["comments"]:
            if comment["commenter_id"] == account_id:
                all_comments.append(comment["comment_content"])

    WordCloud(font_path=TC_FONT_PATH, margin=2, background_color="white", max_font_size=150,
              width=1280, height=720).generate(" ".join(all_comments)).to_file(f"{account_id}.png")


account_text_cloud(account_id="ZhanPeng")
