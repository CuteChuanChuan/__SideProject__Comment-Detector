import pandas as pd
from .utils_mongodb import get_top_n_breaking_news


def update_breaking_news(ptt_board: str, num_news: int = 10) -> pd.DataFrame:
    breaking_news = get_top_n_breaking_news(ptt_board, num_news)
    data = dict({"文章標題": [], "作者": [], "留言數": [], "文章連結": []})

    for news in breaking_news:
        data["文章標題"].append(news["article_data"]["title"])
        data["作者"].append(news["article_data"]["author"])
        data["留言數"].append(news["article_data"]["num_of_comment"])
        data["文章連結"].append(
            f"<a href='{news['article_url']}'>{news['article_url']}</a>"
        )

    return pd.DataFrame(data)
