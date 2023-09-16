import os
import time
from dotenv import load_dotenv
from py2neo import Graph, Node, Relationship, NodeMatcher
from py2neo.bulk import create_nodes, create_relationships

from aggregate_mongo import extract_all_authors_accounts_and_ip

load_dotenv(verbose=True)

# Create a new graph client and connect to the server
graph = Graph(uri=f"{os.getenv('NEO4J_URL')}:7687",
              auth=(os.getenv("NEO4J_USERNAME", "YourAccount"), os.getenv("NEO4J_PASSWORD", "YourPassword")))

# matcher_1 = NodeMatcher(graph)
# node_1 = matcher_1.match()

start = time.time()
account_ids, account_ips = extract_all_authors_accounts_and_ip("gossip")
for account_id, account_ip in zip(account_ids, account_ips):
    if account_id is not None and account_ip is not None:
        id_node = Node("Account", id=account_id)
        ip_node = Node("IP", address=account_ip)
        graph.merge(id_node, "Account", "id")
        graph.merge(ip_node, "IP", "address")
        print(account_id, account_ip)
        rel = Relationship(id_node, "USES", ip_node)
        graph.create(rel)
print("-" * 50)
print(f"Time: {time.time() - start}")
print(graph.schema.node_labels)
print(graph.schema.relationship_types)
