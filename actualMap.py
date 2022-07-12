import networkx as nx
import matplotlib.pyplot as plt

G = nx.Graph()

for i in range(0, 24):
    # I am not sure how I want to number them... also how to embed labels in this format???
    G.add_edge(f"A{i}", f"A{i+1}")

# Add chest locations

print(G.nodes)

labeldict = {}

for i in range(0, 11):
    labeldict[f"A{i}"] = f"f-{i}"
labeldict["B4"] = "Chest1"
for i in range(11, 21):
    labeldict[f"A{i}"] = f"C-{i}"
labeldict["A21"] = "Town-1"
labeldict["A22"] = "Town-2"
labeldict["A23"] = "Town-3"
labeldict["A24"] = "LeaveTown"

print(labeldict)

G.add_edge('A4', 'B4')

nx.draw(G, labels=labeldict, with_labels=True)

plt.show()
