"""Procedural map generation utilities for creating endless worlds."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from game_logic.simple_graph import Graph

ALLY_PROFILES: List[Dict[str, Iterable[str]]] = [
    {"class": "player", "names": ["Borin", "Kaia", "Mira", "Thalen"]},
    {"class": "ranger", "names": ["Lyra", "Finn", "Selene", "Rowan"]},
    {"class": "cleric", "names": ["Aria", "Lucan", "Seren", "Moira"]},
    {"class": "mage", "names": ["Eldrin", "Cira", "Varis", "Ilyana"]},
]

NODE_FEATURE_WEIGHTS: Dict[str, float] = {
    "encounter": 0.75,
    "shop": 0.15,
    "fishing": 0.1,
    "city": 0.12,
    "transition": 0.08,
    "ally": 0.12,
}


@dataclass
class MapBlueprint:
    """Serializable representation of a generated map."""

    key: str
    name: str
    nodes: Dict[str, Dict[str, object]]
    edges: List[Tuple[str, str]]

    def to_graph(self) -> Graph:
        graph = Graph()
        for node, data in self.nodes.items():
            graph.add_node(node)
            graph.nodes[node].update(data)
        for node_a, node_b in self.edges:
            graph.add_edge(node_a, node_b)
        return graph

    def to_dict(self) -> Dict[str, object]:
        return {
            "key": self.key,
            "name": self.name,
            "nodes": self.nodes,
            "edges": self.edges,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "MapBlueprint":
        key = str(data["key"])
        name = str(data.get("name", key))
        nodes_raw = data.get("nodes", {})
        edges_raw = data.get("edges", [])
        nodes: Dict[str, Dict[str, object]] = {
            node: dict(metadata) for node, metadata in dict(nodes_raw).items()
        }
        edges: List[Tuple[str, str]] = [tuple(edge) for edge in edges_raw]  # type: ignore[arg-type]
        return cls(key=key, name=name, nodes=nodes, edges=edges)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, payload: str) -> "MapBlueprint":
        return cls.from_dict(json.loads(payload))


def _generate_node_features(
    rng: random.Random,
    *,
    base_level: int,
    ensure_transition: bool = False,
    ensure_ally: bool = False,
) -> Dict[str, object]:
    features: Dict[str, object] = {}
    for feature, weight in NODE_FEATURE_WEIGHTS.items():
        if rng.random() < weight:
            if feature == "ally":
                features[feature] = _generate_ally_blueprint(rng, base_level)
            elif feature == "transition":
                features[feature] = "auto"
            else:
                features[feature] = True
    if ensure_transition:
        features["transition"] = "auto"
    if ensure_ally:
        features["ally"] = _generate_ally_blueprint(rng, base_level)
    if "encounter" not in features:
        features["encounter"] = True
    return features


def _generate_ally_blueprint(rng: random.Random, base_level: int) -> Dict[str, object]:
    profile = rng.choice(ALLY_PROFILES)
    name = rng.choice(list(profile["names"]))
    level_bonus = rng.randint(-1, 1)
    return {
        "name": name,
        "class": str(profile["class"]),
        "level_bonus": level_bonus,
        "personality": rng.choice(["cautious", "bold", "curious", "stoic"]),
    }


def generate_blueprint(
    key: str,
    *,
    size: int = 12,
    base_level: int = 1,
    rng: Optional[random.Random] = None,
) -> MapBlueprint:
    """Generate a new map blueprint using a random walk with heuristics.

    The generator ensures that the resulting graph is connected and contains at
    least one city node, one ally opportunity and one transition to keep the
    world expanding.
    """

    rng = rng or random.Random()
    nodes: Dict[str, Dict[str, object]] = {}
    edges: List[Tuple[str, str]] = []

    next_id = 1

    def _next_node() -> str:
        nonlocal next_id
        value = str(next_id)
        next_id += 1
        return value

    start_node = _next_node()
    nodes[start_node] = {"city": True, "encounter": True}
    created_nodes = [start_node]

    must_have_transition = True
    must_have_ally = True

    while len(created_nodes) < size:
        node_name = _next_node()
        ensure_transition = must_have_transition and len(created_nodes) >= size // 2
        ensure_ally = must_have_ally and len(created_nodes) >= size // 3
        features = _generate_node_features(
            rng,
            base_level=base_level,
            ensure_transition=ensure_transition,
            ensure_ally=ensure_ally,
        )
        if "transition" in features:
            must_have_transition = False
        if "ally" in features:
            must_have_ally = False
        nodes[node_name] = features
        target = rng.choice(created_nodes)
        edges.append((node_name, target))
        if rng.random() < 0.35:
            other = rng.choice(created_nodes)
            if other != target:
                edges.append((node_name, other))
        created_nodes.append(node_name)

    if must_have_transition:
        node = rng.choice(created_nodes)
        nodes[node]["transition"] = "auto"
    if must_have_ally:
        node = rng.choice(created_nodes)
        nodes[node]["ally"] = _generate_ally_blueprint(rng, base_level)

    slug = key.split("_")[-1].upper()
    name = f"Frontier {slug}"
    return MapBlueprint(key=key, name=name, nodes=nodes, edges=edges)


def blueprint_from_graph(key: str, graph: Graph) -> MapBlueprint:
    """Convert an in-memory graph into a blueprint suitable for persistence."""

    nodes = {node: dict(data) for node, data in graph.nodes.items()}
    edges: List[Tuple[str, str]] = []
    seen: set[Tuple[str, str]] = set()
    for node, neighbors in graph._adjacency.items():  # type: ignore[attr-defined]
        for neighbor in neighbors:
            edge = tuple(sorted((node, neighbor)))
            if edge in seen:
                continue
            seen.add(edge)
            edges.append((node, neighbor))
    return MapBlueprint(key=key, name=key, nodes=nodes, edges=edges)
