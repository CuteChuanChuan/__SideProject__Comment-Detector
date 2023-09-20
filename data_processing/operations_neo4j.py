import os
from typing import Optional
from dotenv import load_dotenv
from py2neo import Graph, Node, Relationship
from aggregate_mongo import extract_all_authors_accounts_and_ip

load_dotenv(verbose=True)

graph = Graph(uri=f"{os.getenv('NEO4J_URL')}:7687",
              auth=(os.getenv("NEO4J_USERNAME", "YourAccount"), os.getenv("NEO4J_PASSWORD", "YourPassword")))


def get_account_ip(_id: str) -> Optional[list[str]]:
    # results = graph.run(f'MATCH p=({{id:"{_id}"}})--() RETURN *')
    results = graph.run(f'MATCH (a:Account {{id:"{_id}"}})-[:USES]->(ip:IP) RETURN ip.address')
    for ip in results:
        print(ip)
    ip_collections = []
    # if results:
    #     for record in results:
    #         ip_collections.append(record[0].nodes[1]["address"])
    #     return ip_collections
    # return None


def get_ip_account(_ip: str) -> Optional[list[str]]:
    query = f"MATCH (n)-->({{address:'{_ip}'}}) RETURN n.id"
    ids = [record["n.id"] for record in graph.run(query)]
    return ids


if __name__ == "__main__":
    # ip_collections = get_account_ip(_id="nobody0303")
    # print(ip_collections)

    print(get_ip_account(_ip="131.179.58.17"))
