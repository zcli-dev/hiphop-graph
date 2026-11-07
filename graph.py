import json

import networkx as nx

with open("artists.json", encoding="utf-8") as f:
    artists = json.load(f)

graph = nx.Graph()

for artist in artists:
    graph.add_node(artist["id"], name=artist["name"])
    for rel in artist["relations"]:
        graph.add_node(rel["other_id"], name=rel["other_name"])
        graph.add_edge(artist["id"], rel["other_id"], type=rel["type"])

print(f"{graph.number_of_nodes()} artists and groups, {graph.number_of_edges()} connections")

parts = list(nx.connected_components(graph))
print(f"{len(parts)} separate clusters, largest has {len(max(parts, key=len))} nodes")

most_connected = sorted(graph.degree, key=lambda pair: pair[1], reverse=True)[:5]
print("Most connected:")
for node_id, count in most_connected:
    print(f"  {graph.nodes[node_id]['name']}: {count} connections")


def simplify(text):
    return "".join(c for c in text.lower() if c.isalnum())


def find_id(name):
    wanted = simplify(name)
    for node_id, data in graph.nodes(data=True):
        if simplify(data["name"]) == wanted:
            return node_id
    return None

start = find_id(input("First artist: "))
end = find_id(input("Second artist: "))

if start is None or end is None:
    print("One of those names isn't in the data yet.")
elif not nx.has_path(graph, start, end):
    print("No connection found in the data.")
else:
    path = nx.shortest_path(graph, start, end)
    print(" -> ".join(graph.nodes[n]["name"] for n in path))