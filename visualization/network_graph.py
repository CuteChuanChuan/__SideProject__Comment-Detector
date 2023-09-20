import json
import urllib.request
import igraph as ig
import networkx as nx
import plotly.express as px
from data_processing.aggregate_mongo import retrieve_article

article_a = retrieve_article(target_collection="gossip",
                             search_url="https://www.ptt.cc/bbs/Gossiping/M.1694741448.A.CCB.html")
G = nx.Graph()

comments = article_a["article_data"]["comments"]
print(comments)
print("==" * 50)
commenter_id = [_id for _id in comments["commenter_id"]]
print(commenter_id)
# commenter_ip = [person for person in comments["commenter_ip"]]

print(commenter_id)
for _ in range(len(commenter_id)):
    _id = commenter_id[_]
    _ip = commenter_ip[_]
    G.add_node(_id)
    G.add_node(_ip)
    G.add_edge(_id, _ip)

pos = nx.spring_layout(G, k=0.5, iterations=50)
print(pos)
for n, p in pos.items():
    G.nodes[n]['pos'] = p
