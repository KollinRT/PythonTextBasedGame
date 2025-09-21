"""A tiny undirected graph helper to avoid external dependencies."""

from __future__ import annotations

from typing import Dict, Iterable, Iterator, List, MutableMapping, Set


class Graph:
    def __init__(self) -> None:
        self._adjacency: Dict[str, Set[str]] = {}
        self.nodes: Dict[str, MutableMapping[str, object]] = {}

    def add_node(self, node: str) -> None:
        self._adjacency.setdefault(node, set())
        self.nodes.setdefault(node, {})

    def add_edge(self, node_a: str, node_b: str) -> None:
        self.add_node(node_a)
        self.add_node(node_b)
        self._adjacency[node_a].add(node_b)
        self._adjacency[node_b].add(node_a)

    def neighbors(self, node: str) -> Iterator[str]:
        return iter(self._adjacency.get(node, ()))

