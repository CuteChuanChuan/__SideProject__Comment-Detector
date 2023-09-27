import os
import re
import time
import jieba
import openai
import pandas as pd
import jieba.analyse
from keybert import KeyBERT
import plotly.offline as py
import plotly.express as px
from dotenv import load_dotenv
from pymongo import MongoClient
import plotly.graph_objects as go
from gensim import corpora, models
from collections import defaultdict
from datetime import timedelta, date
from datetime import datetime, timedelta, timezone
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from ckiptagger import data_utils, construct_dictionary, WS, POS, NER


load_dotenv(verbose=True)

uri = os.getenv("ATLAS_URI", "None")
client = MongoClient(uri)
db = client.ptt
openai.api_key = os.getenv("OPENAI_KEY")

# neo4j_url = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
# neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
# neo4j_password = os.environ.get("NEO4J_PASSWORD", "password")


def chatgpt_analyze_topic(prompt):
    if not openai.api_key:
        raise ValueError("Missing OpenAI API Key!")

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": f"給我下方文章的三個關鍵字，兩個指出當中的政治人物、一個指出文章主題，不要列點，不要頓號，只要用空格連結成一行"
                f"產出範例：柯文哲 蔡英文 進口蛋，"
                f"文章內文如下：\n{prompt}",
            }
        ],
    )
    return completion["choices"][0]["message"]["content"]


def get_article_content(target_collection: str, article_url: str):
    article = db[target_collection].find_one({"article_url": article_url})
    return article["article_data"]["main_content"][:400]


# article_manin_content = get_article_content(target_collection="politics",
#                                             article_url="https://www.ptt.cc/bbs/HatePolitics/M.1695225784.A.A25.html")
#
# results = chatgpt_analyze_topic(article_manin_content)
# print(results)
def timestamp_to_datetime(unix_timestamp: float) -> datetime:
    utc_8 = datetime.fromtimestamp(unix_timestamp, timezone.utc).astimezone(
        timezone(timedelta(hours=8))
    )
    return utc_8.replace(second=0, microsecond=0)
