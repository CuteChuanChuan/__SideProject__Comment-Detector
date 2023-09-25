import numpy as np
import pandas as pd
import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
from func_insert_pg_from_mongo import pg_conn


def get_all_relevant_articles():
    with pg_conn.cursor() as cursor:
        cursor.execute("SELECT id, author_id, author_ip FROM comment.article_info")
        all_authors = cursor.fetchall()
        return all_authors


def get_all_relevant_comments(article_id: int):
    with pg_conn.cursor() as cursor:
        cursor.execute(f"SELECT commenter_id, commenter_ip FROM comment.comment_info WHERE article_id = {article_id}")
        all_commenters = cursor.fetchall()
        return all_commenters


if __name__ == "__main__":
    G = nx.Graph()
    all_authors_info = get_all_relevant_articles()
    print(all_authors_info)
    print(f"---author: {all_authors_info[0]} ---")
    for article_author in all_authors_info:
        G.add_node(article_author[1])

        all_commenters_info = get_all_relevant_comments(article_author[0])
        for i in all_commenters_info:
            print(f"---commenter: {i[0]} ---")
            G.add_node(i[0])
            G.add_edges_from([(article_author[1], i[0])])

    pos = nx.spring_layout(G, k=0.5, iterations=100)
    print()

    for n, p in pos.items():
        G.nodes[n]["pos"] = p

    edge_trace = go.Scatter(
        x=[], y=[], line=dict(width=0.5, color="#888"), hoverinfo="none", mode="lines"
    )

    for edge in G.edges():
        x0, y0 = G.nodes[edge[0]]["pos"]
        x1, y1 = G.nodes[edge[1]]["pos"]
        edge_trace["x"] += tuple([x0, x1, None])
        edge_trace["y"] += tuple([y0, y1, None])

    node_trace = go.Scatter(
        x=[],
        y=[],
        text=[],
        mode="markers",
        hoverinfo="text",
        marker=dict(
            showscale=True,
            colorscale="RdBu",
            reversescale=True,
            color=[],
            size=15,
            colorbar=dict(
                thickness=10, title="Node Connections", xanchor="left", titleside="right"
            ),
            line=dict(width=0),
        ),
    )

    for node, adjacencies in enumerate(G.adjacency()):
        node_trace["marker"]["color"] += tuple([len(adjacencies[1])])
        node_info = adjacencies[0] + " # of connections: " + str(len(adjacencies[1]))
        node_trace["text"] += tuple([node_info])

    for node in G.nodes():
        x, y = G.nodes[node]["pos"]
        node_trace["x"] += tuple([x])
        node_trace["y"] += tuple([y])

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title="<br>AT&T network connections",
            titlefont=dict(size=16),
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(text="", showarrow=False, xref="paper", yref="paper")
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )

    fig.show()
