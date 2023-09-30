import time
import networkx as nx
from utils_mongo import db
import matplotlib.pyplot as plt
import plotly.graph_objects as go

NUM_ARTICLES = 100


# ----------------------------- functions under testing -----------------------------
def extract_top_n_commenters_by_frequency(
    keyword: str, target_collection: str, num_commenters: int
):
    # pipelines = [
    #     {"$match": {"article_data.title": {"$regex": keyword, "$options": "i"}}},
    #     {"$sort": {"article_data.num_of_comments": -1}},
    #     {"$limit": NUM_ARTICLES},
    #     {"$unwind": "$article_data.comments"},
    #     {
    #         "$project": {
    #             "_id": 0,
    #             "commenter_id": "$article_data.comments.commenter_id",
    #             "article_url": 1,
    #             "article_data.author": 1,
    #             "article_data.time": 1,
    #             "article_data.comments": 1,
    #         }
    #     },
    #     {
    #         "$addFields": {
    #             "time_difference": {"$subtract": ["$article_data.comments.comment_time", "$article_data.time"]}
    #         }
    #     },
    #     {
    #         "$group": {
    #             "_id": "$commenter_id",
    #             "count": {"$sum": 1},
    #             "article_urls": {"$push": "$article_url"},
    #             "comments_type": {"$push": "$article_data.comments.comment_type"},
    #             "comments_latency": {"$push": "$time_difference"},
    #         }
    #     },
    #     {"$sort": {"count": -1}},
    #     {"$limit": 20},
    # ]

    pipelines = [
        {"$match": {"article_data.title": {"$regex": keyword, "$options": "i"}}},
        {"$sort": {"article_data.num_of_comments": -1}},
        {"$limit": NUM_ARTICLES},
        {"$unwind": "$article_data.comments"},
        {
            "$project": {
                "_id": 0,
                "commenter_id": "$article_data.comments.commenter_id",
                "article_url": 1,
                "article_data.author": 1,
                "article_data.time": 1,
                "article_data.comments": 1,
            }
        },
        {
            "$addFields": {
                "time_difference": {
                    "$subtract": [
                        "$article_data.comments.comment_time",
                        "$article_data.time",
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$commenter_id",
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": num_commenters},
    ]

    cursor = db[target_collection].aggregate(pipelines)
    return list(cursor)


def extract_top_n_commenters_by_comment_type(
    keyword: str, target_collection: str, num_commenters: int, comment_type: str
):
    pipelines = [
        {"$match": {"article_data.title": {"$regex": keyword, "$options": "i"}}},
        {"$sort": {"article_data.num_of_comments": -1}},
        {"$limit": NUM_ARTICLES},
        {"$unwind": "$article_data.comments"},
        {"$match": {"article_data.comments.comment_type": comment_type}},
        {
            "$project": {
                "_id": 0,
                "commenter_id": "$article_data.comments.commenter_id",
                "article_url": 1,
                "article_data.author": 1,
                "article_data.time": 1,
                "article_data.comments": 1,
            }
        },
        {
            "$addFields": {
                "time_difference": {
                    "$subtract": [
                        "$article_data.comments.comment_time",
                        "$article_data.time",
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$commenter_id",
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": num_commenters},
    ]
    cursor = db[target_collection].aggregate(pipelines)
    return list(cursor)


def preparation_time_diff(
    keyword: str, target_collection: str, num_commenters: int, comment_type: str
):
    pipelines = [
        {"$match": {"article_data.title": {"$regex": keyword, "$options": "i"}}},
        {"$sort": {"article_data.num_of_comments": -1}},
        {"$limit": NUM_ARTICLES},
        {"$unwind": "$article_data.comments"},
        {"$match": {"article_data.comments.comment_type": comment_type}},
        {
            "$project": {
                "_id": 0,
                "commenter_id": "$article_data.comments.commenter_id",
                "article_url": 1,
                "article_data.author": 1,
                "article_data.time": 1,
                "article_data.comments": 1,
            }
        },
        {
            "$addFields": {
                "time_difference": {
                    "$subtract": [
                        "$article_data.comments.comment_time",
                        "$article_data.time",
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$commenter_id",
                "count": {"$sum": 1},
                "article_urls": {"$push": "$article_url"},
                "comments_type": {"$push": "$article_data.comments.comment_type"},
                "comments_latency": {"$push": "$time_difference"},
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": num_commenters},
    ]
    cursor = db[target_collection].aggregate(pipelines)
    return list(cursor)



# def compute_concurrency(
#     freq_commenters: list[dict],
#     agree_commenters: list[dict],
#     disagree_commenters: list[dict],
# ):
#     unique_ids = set()
#     for freq_commenter in freq_commenters:
#         unique_ids.add(freq_commenter["_id"])
#     for agree_commenter in agree_commenters:
#         unique_ids.add(agree_commenter["_id"])
#     for disagree_commenter in disagree_commenters:
#         unique_ids.add(disagree_commenter["_id"])
#     return len(unique_ids)


if __name__ == "__main__":
    # start = time.time()
    # #
    # # top_20_commenters_agreement = list_top_n_commenters_filtered_by_comment_type(
    # #     keyword="雞蛋", target_collection="gossip", comment_type="推", num_commenters=10
    # # )
    # # # print(top_20_commenters_agreement)
    # # ids_combinations = generate_all_combinations(top_20_commenters_agreement)
    # # concurrency_list = []
    # # for combination in ids_combinations:
    # #     concurrency = compute_concurrency(combination)
    # #     print(concurrency)
    # #     concurrency_list.append(compute_concurrency(combination))
    # # print(concurrency_list)
    # # # print(
    # # #     count_top_n_commenters_filtered_by_comment_type(
    # # #         keyword="雞蛋",
    # # #         target_collection="gossip",
    # # #         comment_type="噓",
    # # #         num_commenters=20,
    # # #     )
    # # # )
    # # print(time.time() - start)
    # # print(compute_concurrency(ids=("coffee112", "miliq")))
    # # print(list(db.gossip.aggregate([
    # #     {"$match": {"article_data.title": {"$regex": "雞蛋", "$options": "i"}}},
    # #     {"$sort": {"article_data.num_of_comment": -1}},
    # #     {"$limit": NUM_ARTICLES},
    # #     {"$match": {"article_data.comments": {"$elemMatch": {"commenter_id": "miliq", "comment_type": "推"}}}},
    # #     {"$project": {"_id": 0, "article_url": 1}}
    # # ])))
    #
    # temp_collection_id, board_name, keyword = query_articles_store_temp_collection(
    #     keyword="違建", target_collection="gossip")
    #
    # top_20_commenters_agreement, num_commenters = list_top_n_commenters_filtered_by_comment_type(
    #     temp_collection=temp_collection_id,
    #     comment_type="推", num_commenters=20
    # )
    # ids_combinations = generate_all_combinations(top_20_commenters_agreement)
    # concurrency_list = []
    # for combination in ids_combinations:
    #     concurrency = compute_concurrency(
    #         ids=combination, temp_collection=temp_collection_id)
    #     concurrency_list.append(concurrency)
    # print(concurrency_list)
    # print(time.time() - start)
    #
    # G = nx.Graph()
    # for data in concurrency_list:
    #     source, target, weight = data
    #     G.add_edge(source, target, weight=weight)
    #
    # pos = nx.spring_layout(G)
    # node_x = [pos[node][0] for node in G.nodes()]
    # node_y = [pos[node][1] for node in G.nodes()]
    # weights = [G.edges[edge]["weight"] for edge in G.edges()]
    #
    # sorted_edges = sorted(G.edges(data=True), key=lambda x: x[2]["weight"])
    #
    # edge_traces = []
    # for edge_data in sorted_edges:
    #     edge = edge_data[:2]
    #     weight = edge_data[2]["weight"]
    #     x0, y0 = pos[edge[0]]
    #     x1, y1 = pos[edge[1]]
    #     edge_color = weight_to_color(weight, weights, plt.cm.Blues)
    #     edge_traces.append(
    #         go.Scatter(
    #             x=[x0, x1, None],
    #             y=[y0, y1, None],
    #             line=dict(width=weight * 15, color=edge_color),
    #             mode="lines",
    #         )
    #     )
    #
    # node_trace = go.Scatter(
    #     x=node_x,
    #     y=node_y,
    #     text=list(G.nodes()),
    #     mode="markers",
    #     marker=dict(size=10, color="red"),
    #     hoverinfo="text",
    # )
    #
    # color_bar_trace = go.Scatter(
    #     x=[None],
    #     y=[None],
    #     mode="markers",
    #     marker=dict(
    #         colorscale="Blues",
    #         cmin=min(weights) * 100,
    #         cmax=max(weights) * 100,
    #         colorbar=dict(title="共同出現次數"),
    #         showscale=True,
    #     ),
    # )
    # board_name = "八卦" if board_name == "gossip" else "政黑"
    # layout = go.Layout(title=f"{board_name}版，有關<{keyword}>的留言數量前 {NUM_ARTICLES} 名的文章中，"
    #                          f"留言次數前 {num_commenters} 名的留言者帳號",
    #                    showlegend=False,
    #                    xaxis=dict(showticklabels=False, zeroline=False, showgrid=False),
    #                    yaxis=dict(showticklabels=False, zeroline=False, showgrid=False),
    #                    annotations=[
    #                        dict(
    #                            text=f"{NUM_ARTICLES} 篇文章中帳號一起出現並留言的次數",
    #                            xref="paper",
    #                            yref="paper",
    #                            x=0,
    #                            y=1.05,
    #                            showarrow=False,
    #                            font=dict(size=14),  # adjusting the font size for subtitle
    #                        )
    #                    ]
    #                    )
    # fig = go.Figure(data=edge_traces + [node_trace, color_bar_trace], layout=layout)
    #
    # fig.show()

    print(preparation_time_diff(keyword="雞蛋", target_collection="gossip", num_commenters=20, comment_type="推"))

