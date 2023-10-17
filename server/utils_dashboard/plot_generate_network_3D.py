import numpy as np
import pandas as pd
import networkx as nx
import plotly.express as px
import plotly.graph_objects as go


# def get_all_relevant_articles():
#     with pg_conn.cursor() as cursor:
#         cursor.execute("SELECT id, author_id, author_ip FROM comment.article_info")
#         all_authors = cursor.fetchall()
#         return all_authors
#
#
# def get_all_relevant_comments(article_id: int):
#     with pg_conn.cursor() as cursor:
#         cursor.execute(f"SELECT commenter_id, commenter_ip FROM comment.comment_info WHERE article_id = {article_id}")
#         all_commenters = cursor.fetchall()
#         return all_commenters


# if __name__ == "__main__":
# G = nx.Graph()
# all_authors_info = get_all_relevant_articles()
# print(all_authors_info)
# print(f"---author: {all_authors_info[0]} ---")
# for article_author in all_authors_info:
#     G.add_node(article_author[1])
#
#     all_commenters_info = get_all_relevant_comments(article_author[0])
#     for i in all_commenters_info:
#         print(f"---commenter: {i[0]} ---")
#         G.add_node(i[0])
#         G.add_edges_from([(article_author[1], i[0])])
#
# pos = nx.spring_layout(G, dim=3, k=0.5, iterations=100)
# Xn = [pos[node][0] for node in G.nodes()]
# Yn = [pos[node][1] for node in G.nodes()]
# Zn = [pos[node][2] for node in G.nodes()]
#
# Xe = []
# Ye = []
# Ze = []
#
# for e in G.edges():
#     Xe += [pos[e[0]][0], pos[e[1]][0], None]
#     Ye += [pos[e[0]][1], pos[e[1]][1], None]
#     Ze += [pos[e[0]][2], pos[e[1]][2], None]
#
# # Define the trace for edges
# trace_edge = go.Scatter3d(x=Xe,
#                           y=Ye,
#                           z=Ze,
#                           mode='lines',
#                           line=dict(color='rgb(125,125,125)', width=1),
#                           hoverinfo='none'
#                           )
#
# # Define the trace for nodes
# trace_node = go.Scatter3d(x=Xn,
#                           y=Yn,
#                           z=Zn,
#                           mode='markers',
#                           name='actors',
#                           marker=dict(symbol='circle',
#                                       size=6,
#                                       colorscale='Viridis',
#                                       showscale=True,
#                                       line=dict(color='rgb(50,50,50)', width=0.5)
#                                       ),
#                           text=list(G.nodes()),
#                           hoverinfo='text'
#                           )
#
# axis = dict(showbackground=False,
#             showline=False,
#             zeroline=False,
#             showgrid=False,
#             showticklabels=False,
#             title=''
#             )
#
# layout = go.Layout(
#     title="Network of coappearances of characters in Victor Hugo's novel<br> Les Miserables (3D visualization)",
#     width=1000,
#     height=1000,
#     showlegend=False,
#     scene=dict(
#         xaxis=dict(axis),
#         yaxis=dict(axis),
#         zaxis=dict(axis),
#     ),
#     margin=dict(
#         t=100
#     ),
#     hovermode='closest',
#     annotations=[
#         dict(
#             showarrow=False,
#             xref='paper',
#             yref='paper',
#             x=0,
#             y=0.1,
#             xanchor='left',
#             yanchor='bottom',
#             font=dict(
#                 size=14
#             )
#         )
#     ],
# )
#
# data = [trace_edge, trace_node]
# fig = go.Figure(data=data, layout=layout)
#
# fig.show()
