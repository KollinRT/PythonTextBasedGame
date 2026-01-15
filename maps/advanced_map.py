"""Challenging late-game region with multiple branching paths."""

from __future__ import annotations

from typing import Dict

from game_logic.simple_graph import Graph


def _ally(name: str, klass: str, *, level_bonus: int = 0, personality: str = "steadfast") -> Dict[str, object]:
    return {
        "name": name,
        "class": klass,
        "level_bonus": level_bonus,
        "personality": personality,
    }


def create_advanced_map() -> Graph:
    """Return a handcrafted map that links frontier regions together."""

    graph = Graph()

    for idx in range(0, 12):
        graph.add_node(f"C{idx}")

    # Primary loop
    for idx in range(0, 11):
        graph.add_edge(f"C{idx}", f"C{idx+1}")
    graph.add_edge("C0", "C6")
    graph.add_edge("C3", "C9")
    graph.add_edge("C4", "C10")

    # Encounters are plentiful in the frontier
    for idx in range(1, 12):
        graph.nodes[f"C{idx}"]["encounter"] = True

    # Points of interest
    graph.nodes["C2"]["shop"] = True
    graph.nodes["C5"]["fishing"] = True
    graph.nodes["C7"]["city"] = True
    graph.nodes["C8"]["ally"] = _ally("Valeera", "ranger", level_bonus=1, personality="fierce")
    graph.nodes["C10"]["ally"] = _ally("Eldros", "mage", level_bonus=2, personality="mysterious")

    # Transitions keep the world connected
    graph.nodes["C0"]["transition"] = "intermediate"
    graph.nodes["C11"]["transition"] = "auto"

    return graph

