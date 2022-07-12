import networkx as nx

G = nx.Graph()
G.add_edge(1, 2) # default edge data=1
G.add_edge(2, 3, weight=0.9) # specify edge data
import math
G.add_edge('y', 'x', function=math.cos)
G.add_node(math.cos) # any hashable can be a node

X = nx.Graph()
X.add_edge(1,2)
X.add_edge(1,3)
X.add_edge(1,4, weight=0.2)

X.add_edge(2,4)

print(X.adj)

for edges in X.edges:
    print(edges)

nx.draw(G)
