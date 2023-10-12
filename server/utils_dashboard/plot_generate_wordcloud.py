from loguru import logger
from wordcloud import WordCloud
from .config_dashboard import db

TC_FONT_PATH = "utils_dashboard/NotoSerifTC-Regular.otf"


def wordcloud_graph(account_id):
    """
    generate text cloud of comments with account id
    :param account_id: ptt account id
    """
    gossip_collection, politics_collection, all_comments = (
        db["gossip"],
        db["politics"],
        [],
    )

    gossip_cursor = gossip_collection.find(
        {"article_data.comments.commenter_id": account_id},
        {"article_data.comments": 1, "article_url": 1, "_id": 0},
    )
    politic_cursor = politics_collection.find(
        {"article_data.comments.commenter_id": account_id},
        {"article_data.comments": 1, "article_url": 1, "_id": 0},
    )

    for article in gossip_cursor:
        for comment in article["article_data"]["comments"]:
            if comment["commenter_id"] == account_id:
                all_comments.append(comment["comment_content"])

    for article in politic_cursor:
        for comment in article["article_data"]["comments"]:
            if comment["commenter_id"] == account_id:
                all_comments.append(comment["comment_content"])

    # comments_cleaned = [comment for comment in all_comments if "https://" not in comment]
    comments_cleaned = [comment for comment in all_comments if "http" not in comment]
    if len(comments_cleaned) > 0:
        wc = WordCloud(
            font_path=TC_FONT_PATH,
            margin=2,
            background_color="white",
            max_font_size=150,
            width=980,
            height=600,
        ).generate(" ".join(comments_cleaned))

        return wc.to_image()
    return "查無資料"


if __name__ == "__main__":
    wordcloud_graph(account_id="coffee112")
