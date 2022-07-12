import networkx as nx
import matplotlib.pyplot as plt

G = nx.Graph()

for i in range(0, 24):
    # I am not sure how I want to number them... also how to embed labels in this format???
    G.add_edge(f"A{i}", f"A{i+1}")

# Add chest locations

# print(G.nodes)

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

# print(labeldict)

G.add_edge('A4', 'B4')

# print(G.nodes)
# print(G.edges)

# def movement(dir):
#     for node in G.nodes:
#         for edge in G.edges:
#             print(f"nodes:{node}", f"edges: {edge}")

# for node in G.nodes:
#     for edge in G.edges:
#         if node ==

nodes = [node for node in G.nodes]
edges = [edge for edge in G.edges]
# print(nodes)
# print(edges)
# for node in nodes and edge in edges:
#     print(node,edge)
# go through all of the edges then up to the next node...

# for node in nodes:
#     if edge in edges:
#         print(node)

movePath = [] # to append nodes traveled to with last one in last/first slot [-1] or [0]? I think first might be cheaper but lowkey think the same...... 
# Need to find a way to compare proximity of nodes... If node exists & nodes are connected via edges defined in G.edges tuples.... (Node1, Node2)
def movementOfGraphs(direction):
    # Define list for path of nodes traversed
    movePath = []
    # Define a blank of nodes
    node = ['A0'] # initial starting position of the game...
    # Define a list of valid nodes and edges for movement restriction
    nodes = [node for node in G.nodes]
    edges = [edge for edge in G.edges]
    # Define logic for this... If nodes are next to/exist in edges... I think edges would work better since it would show adjacency better...
    if node in nodes:
        print("Exists!")
        

# movementOfGraphs(1)
#     if 

# if nodes in G.nodes:

node = ['A0'] # initial starting position of the game...
nodes = [node for node in G.nodes]
edges = [edge for edge in G.edges]
# Define logic for this... If nodes are next to/exist in edges... I think edges would work better since it would show adjacency better...
if node in nodes:
    print("Exists!")




# nx.draw(G, labels=labeldict, with_labels=True)

# plt.show()
