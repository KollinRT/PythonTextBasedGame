"""Second map unlocked during progression."""

from __future__ import annotations

from game_logic.simple_graph import Graph


def create_intermediate_map() -> Graph:
    graph = Graph()

    for idx in range(0, 8):
        graph.add_node(f"B{idx}")

    for idx in range(0, 7):
        graph.add_edge(f"B{idx}", f"B{idx+1}")

    for idx in range(0, 8, 2):
        graph.nodes[f"B{idx}"]["encounter"] = True
    graph.nodes["B1"]["shop"] = True
    graph.nodes["B3"]["fishing"] = True
    graph.nodes["B5"]["city"] = True
    graph.nodes["B5"]["transition"] = "advanced"
    graph.nodes["B7"]["transition"] = "beginner"

    return graph

