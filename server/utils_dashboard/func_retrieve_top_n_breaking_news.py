import time
import pandas as pd
from utils_mongodb import get_top_n_breaking_news


def update_breaking_news(ptt_board: str, num_news: int = 10) -> pd.DataFrame:
    start = time.time()
    articles = get_top_n_breaking_news(ptt_board, num_news)
    data = dict({"文章標題": [], "留言數": [], "文章連結": []})

    for article in articles:
        data["文章標題"].append(article["article_data"]["title"])
        data["留言數"].append(article["article_data"]["num_of_comment"])
        data["文章連結"].append(
            f"<a href='{article['article_url']}'>{article['article_url']}</a>"
        )

    df = pd.DataFrame(data)
    return df
