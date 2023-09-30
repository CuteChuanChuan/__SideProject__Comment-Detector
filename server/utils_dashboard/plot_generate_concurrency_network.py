import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from utils_dashboard.utils_mongodb import (query_articles_store_temp_collection,
                                           list_top_n_commenters_filtered_by_comment_type,
                                           generate_all_combinations, compute_concurrency,
                                           weight_to_color)

NUM_ARTICLES = 100


def preparation_network_graph(keyword: str, target_collection: str):
    temp_collection_id, board_name, keyword = query_articles_store_temp_collection(
        keyword=keyword, target_collection=target_collection
    )
    return temp_collection_id, board_name, keyword


def generate_concurrency_network_data(temp_collection_id: str, comment_type: str, num_commenters: int):
    top_n_commenters, num_commenters = list_top_n_commenters_filtered_by_comment_type(
        temp_collection=temp_collection_id, comment_type=comment_type, num_commenters=num_commenters
    )
    ids_combinations = generate_all_combinations(top_n_commenters)
    concurrency_list = []
    for combination in ids_combinations:
        concurrency = compute_concurrency(
            ids=combination, temp_collection=temp_collection_id, comment_type=comment_type)
        concurrency_list.append(concurrency)
    return concurrency_list


def create_network_graph(
        concurrency_list: list[tuple], board_name: str, keyword: str, num_commenters: int, comment_type: str
) -> go.Figure:

    g = nx.Graph()
    for data in concurrency_list:
        source, target, weight = data
        g.add_edge(source, target, weight=weight)
    
    pos = nx.spring_layout(g)
    node_x = [pos[node][0] for node in g.nodes()]
    node_y = [pos[node][1] for node in g.nodes()]
    weights = [g.edges[edge]["weight"] for edge in g.edges()]
    
    sorted_edges = sorted(g.edges(data=True), key=lambda x: x[2]["weight"])
    
    edge_traces = []
    for edge_data in sorted_edges:
        edge = edge_data[:2]
        weight = edge_data[2]["weight"]
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_color = weight_to_color(weight, weights, plt.cm.Blues)
        edge_traces.append(
            go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                line=dict(width=weight * 15, color=edge_color),
                mode="lines",
            )
        )
    
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        text=list(g.nodes()),
        mode="markers",
        marker=dict(size=10, color="red"),
        hoverinfo="text",
    )
    
    color_bar_trace = go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker=dict(
            colorscale="Blues",
            cmin=min(weights) * 100,
            cmax=max(weights) * 100,
            colorbar=dict(title="共同出現次數"),
            showscale=True,
        ),
    )
    board_name = "八卦" if board_name == "gossip" else "政黑"
    comment_type = "推文" if comment_type == "推" else "噓文"
    layout = go.Layout(
        title=f"{board_name}版，有關<{keyword}>的留言數量前 {NUM_ARTICLES} 名的文章中，"
        f"{comment_type}次數前 {num_commenters} 名的留言者帳號之間一起出現並留言的次數",
        showlegend=False,
        xaxis=dict(showticklabels=False, zeroline=False, showgrid=False),
        yaxis=dict(showticklabels=False, zeroline=False, showgrid=False),
    )
    fig = go.Figure(data=edge_traces + [node_trace, color_bar_trace], layout=layout)
    return fig
