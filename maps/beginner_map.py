"""Definition of the introductory map used by the game."""

from __future__ import annotations

from game_logic.simple_graph import Graph


def create_beginner_map() -> Graph:
    graph = Graph()

    for idx in range(0, 12):
        graph.add_node(f"A{idx}")

    for idx in range(0, 11):
        graph.add_edge(f"A{idx}", f"A{idx+1}")

    # annotate special zones
    for idx in range(1, 8):
        graph.nodes[f"A{idx}"]["encounter"] = True
    graph.nodes["A3"]["shop"] = True
    graph.nodes["A4"]["fishing"] = True
    graph.nodes["A5"]["city"] = True
    graph.nodes["A7"]["transition"] = "intermediate"

    return graph

