import json
import os

import networkx as nx

MIN_SONGS = 2

with open("artists.json", encoding="utf-8") as f:
    artists = json.load(f)

with open("credits.json", encoding="utf-8") as f:
    credits = json.load(f)

names = {}
links = {}


def add_link(a, b, relation=None, songs=0):
    key = tuple(sorted((a, b)))
    entry = links.setdefault(key, {"relation": None, "songs": 0})
    if relation:
        entry["relation"] = relation
    entry["songs"] = max(entry["songs"], songs)


for artist in artists:
    names[artist["id"]] = artist["name"]
    for rel in artist["relations"]:
        names[rel["other_id"]] = rel["other_name"]
        add_link(artist["id"], rel["other_id"], relation=rel["type"])

for seed_id, entry in credits.items():
    names[seed_id] = entry["name"]
    for other_id, info in entry["collaborators"].items():
        if info["count"] >= MIN_SONGS:
            names[other_id] = info["name"]
            add_link(seed_id, other_id, songs=info["count"])

graph = nx.Graph()
for (a, b), info in links.items():
    graph.add_edge(a, b, **info)

largest = max(nx.connected_components(graph), key=len)
web = graph.subgraph(largest)

nodes = [{"id": n, "name": names[n], "degree": web.degree[n]} for n in web.nodes]
edges = [
    {"source": a, "target": b, "type": d["relation"] or "credited together", "songs": d["songs"]}
    for a, b, d in web.edges(data=True)
]

with open("graph.json", "w", encoding="utf-8") as f:
    json.dump({"nodes": nodes, "edges": edges}, f, separators=(",", ":"))

size_mb = os.path.getsize("graph.json") / 1_000_000
print(f"Before trimming: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
print(f"Exported {len(nodes)} nodes and {len(edges)} edges to graph.json ({size_mb:.1f} MB)")