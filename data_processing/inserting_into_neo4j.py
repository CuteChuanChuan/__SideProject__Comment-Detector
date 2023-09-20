import os
import time
from dotenv import load_dotenv
from py2neo import Graph, Node, Relationship
from py2neo.bulk import merge_nodes, merge_relationships
from aggregate_mongo import (extract_all_authors_accounts_and_ip,
                             extract_all_commenters_accounts_and_ip,
                             retrieve_article)

load_dotenv(verbose=True)

graph = Graph(uri=f"{os.getenv('NEO4J_URL')}:7687",
              auth=(os.getenv("NEO4J_USERNAME", "YourAccount"), os.getenv("NEO4J_PASSWORD", "YourPassword")))


# account_ids, account_ips = extract_all_commenters_accounts_and_ip("gossip")
# account_ids = account_ids[:20]
# account_ips = account_ips[:20]
#
start = time.time()
# for account_id in account_ids:
#     account_node = Node("Account", id=account_id)
#     graph.create(account_node)
#
# id_keys = ["id"]
# id_data = account_ids
# merge_nodes(graph.auto(), id_data, ("Account", "id"), keys=id_keys)
#
# print(len(account_ids), len(account_ips))
# for account_id, account_ip in zip(account_ids, account_ips):
#     if account_id is not None and account_ip is not None:
#         id_node = Node("Account", id=account_id)
#         ip_node = Node("IP", address=account_ip)
#         graph.merge(id_node, "Account", "id")
#         graph.merge(ip_node, "IP", "address")
#         print(account_id, account_ip)
#         rel = Relationship(id_node, "USES", ip_node)
#         graph.create(rel)


def analyze_article(article_info: dict) -> list[dict]:
    analyzed_results = []
    for comments in article_info["article_data"]["comments"]:
        analyzed_results.append({"commenter_id": comments["commenter_id"],
                                 "commenter_ip": comments["commenter_ip"],
                                 "article_url": article_info["article_url"]})
    return analyzed_results


article_a = retrieve_article(target_collection="gossip",
                             search_url="https://www.ptt.cc/bbs/Gossiping/M.1694741448.A.CCB.html")
article_b = retrieve_article(target_collection="gossip",
                             search_url="https://www.ptt.cc/bbs/Gossiping/M.1694956794.A.F1A.html")
article_c = retrieve_article(target_collection="gossip",
                             search_url="https://www.ptt.cc/bbs/Gossiping/M.1694952559.A.90D.html")
article_d = retrieve_article(target_collection="gossip",
                             search_url="https://www.ptt.cc/bbs/Gossiping/M.1694846678.A.101.html")
article_e = retrieve_article(target_collection="gossip",
                             search_url="https://www.ptt.cc/bbs/Gossiping/M.1694829290.A.9F1.html")
article_f = retrieve_article(target_collection="gossip",
                             search_url="https://www.ptt.cc/bbs/Gossiping/M.1694819452.A.AF0.html")

for comments_info in analyze_article(article_f):
    print(comments_info)
    print("=" * 50)
    neo_script = f"""
    MERGE (a:Commenter_id {{id: "{comments_info["commenter_id"]}"}})\
    MERGE (b:Commenter_ip {{ip: "{comments_info["commenter_ip"]}"}})\
    MERGE (c:Article {{article: "{comments_info["article_url"]}"}})\
    MERGE (a)-[:USES]->(b)\
    MERGE (a)-[:RESPONDS]->(c)
    RETURN *;
    """
    graph.run(neo_script)


# query = '''
# MATCH (a1:Article {article: 'https://www.ptt.cc/bbs/Gossiping/M.1694741448.A.CCB.html'})
# MATCH (commenter:Commenter_id)-[:RESPONDS]->(a1)
# WITH commenter, a1
# MATCH (a2:Article {article: 'https://www.ptt.cc/bbs/Gossiping/M.1694956794.A.F1A.html'})
# MATCH (commenter)-[:RESPONDS]->(a2)
# MATCH (commenter)-[:USES]->(ip:Commenter_ip)
# RETURN *
# '''
#
# result = graph.run(query)
# i = 0
# for _ in result:
#     print(type(_))
#     i += 1
# print(i)


# print(analyze_article(article_a))
print("-" * 50)

print(f"Time: {time.time() - start}")
print(graph.schema.node_labels)
print(graph.schema.relationship_types)
