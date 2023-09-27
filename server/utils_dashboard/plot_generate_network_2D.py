import networkx as nx
import plotly.graph_objects as go
from collections import defaultdict
from utils_dashboard.utils_mongodb import (extract_author_info_from_articles_title_having_keywords,
                                                  extract_commenter_info_from_article_with_article_url,
                                                  summarize_commenters_metadata,
                                                  convert_commenters_metadata_to_dataframe,
                                                  extract_top_freq_commenter_id,
                                                  check_commenter_in_article_filter_by_article_url)


def draw_network_2d(article_author_data: list, keyword: str, num_articles: int):
    g = nx.Graph()
    for article_author in article_author_data:
        g.add_node(article_author[0], node_type="author")

        for i in commenters:
            print(f"---commenter: {i} ---")
            g.add_node(i, node_type="commenter")
            if check_commenter_in_article_filter_by_article_url(
                target_collection="gossip", commenter_id=i, article_url=article_author[2]
            ):
                g.add_edges_from([(article_author[0], i)])

    pos = nx.spring_layout(g, k=0.5, iterations=100)

    for n, p in pos.items():
        g.nodes[n]["pos"] = p

    edge_trace = go.Scatter(
        x=[], y=[], line=dict(width=0.5, color="#888"), hoverinfo="none", mode="lines"
    )

    for edge in g.edges():
        x0, y0 = g.nodes[edge[0]]["pos"]
        x1, y1 = g.nodes[edge[1]]["pos"]
        edge_trace["x"] += tuple([x0, x1, None])
        edge_trace["y"] += tuple([y0, y1, None])

    node_trace = go.Scatter(
        x=[],
        y=[],
        text=[],
        mode="markers",
        hoverinfo="text",
        marker=dict(
            showscale=False,
            colorscale="RdBu",
            reversescale=True,
            color=[],
            size=15,
            colorbar=dict(
                thickness=10,
                title="Node Connections",
                xanchor="left",
                titleside="right",
            ),
            line=dict(width=0),
        ),
    )

    for node, adjacencies in enumerate(g.adjacency()):
        node_trace["marker"]["color"] += tuple([len(adjacencies[1])])
        node_info = adjacencies[0] + " # of connections: " + str(len(adjacencies[1]))
        node_trace["text"] += tuple([node_info])

    author_color = "#FF0000"  # Orange color for authors
    commenter_color = "#0000FF"  # Green color for commenters
    node_colors = []

    for node in g.nodes(data=True):
        x, y = g.nodes[node[0]]["pos"]
        node_trace["x"] += tuple([x])
        node_trace["y"] += tuple([y])
        if node[1]["node_type"] == "author":
            node_colors.append(author_color)
        else:
            node_colors.append(commenter_color)
    node_trace["marker"]["color"] = node_colors

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=f"{keyword} - 留言數最多的前 {num_articles} 篇文章",
            titlefont=dict(size=16),
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[dict(text="", showarrow=False, xref="paper", yref="paper")],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )

    return fig


if __name__ == "__main__":
    target_collection = "gossip"
    keyword = "雞蛋"
    num_articles = 400

    # Rationale: filter n articles which include keywords in title
    raw_article_info = extract_author_info_from_articles_title_having_keywords(
        target_collection="gossip", keyword=keyword, num_articles=num_articles
    )
    
    # Rationale: extract all commenters from articles selected in above
    all_commenters_descriptive_info = defaultdict(lambda: defaultdict(float))
    for article in raw_article_info:
        raw_commenters_info = extract_commenter_info_from_article_with_article_url(
            target_collection=target_collection, article_data=article
        )
        all_commenters_descriptive_info = summarize_commenters_metadata(
            raw_commenters_info, all_commenters_descriptive_info
        )
    
    df = convert_commenters_metadata_to_dataframe(all_commenters_descriptive_info)
    
    organized_authors_info = [
        (
            author["article_data"]["author"],
            author["article_data"]["ipaddress"],
            author["article_url"],
            "author",
        )
        for author in raw_article_info
    ]
    
    commenters = extract_top_freq_commenter_id(df, 5)

    network_plot = draw_network_2d(article_author_data=organized_authors_info, keyword="雞蛋", num_articles=400)
    network_plot.show()
