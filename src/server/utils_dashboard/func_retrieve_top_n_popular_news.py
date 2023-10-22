import pandas as pd
from .utils_mongodb import get_top_n_favored_articles


def update_popular_news(ptt_board: str, num_news: int = 10) -> pd.DataFrame:
    popular_news = get_top_n_favored_articles(ptt_board, num_news)
    data = dict({"文章標題": [], "作者": [], "留言數": [], "文章連結": []})

    for news in popular_news:
        data["文章標題"].append(news["article_data"]["title"])
        data["作者"].append(news["article_data"]["author"])
        data["留言數"].append(news["article_data"]["num_of_comment"])
        data["文章連結"].append(
            f"<a href='{news['article_url']}'>{news['article_url']}</a>"
        )

    return pd.DataFrame(data)
