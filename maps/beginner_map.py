import networkx as nx

G = nx.Graph()

for i in range(0,23):
    G.add_node(f"A{i}") # I am not sure how I want to number them... also how to embed labels in this format???

for i in range(1,8):
    G.add_node(f"A{i}", encounterArea="Encounter Zone!") # Nodes don't have weights... edges do! I forgot lol.
# Add chest locations

G.add_node("A9", shopArea="shopping Zone!") # Nodes don't have weights... edges do! I forgot lol.
G.add_node("A10", fishingArea="Fishing Zone!") # Nodes don't have weights... edges do! I forgot lol.
G.add_node("A11", cityArea="City Zone!") # Nodes don't have weights... edges do! I forgot lol.

for i in range(0,23):
    G.add_edge(f"A{i}", f"A{i+1}") # I am not sure how I want to number them... also how to embed labels in this format???


G.add_edge('A4', 'B4')

G.add_edge('A4', 'Z4')


# print(G.nodes)

# nx.draw(G)