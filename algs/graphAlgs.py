"""Minimal graph algorithms used by the project tests."""

from __future__ import annotations

from collections import deque
from typing import Dict, Hashable, Iterable, List


class Stack:
    def __init__(self) -> None:
        self._items: List[Hashable] = []

    def push(self, value: Hashable) -> None:
        self._items.append(value)

    def pop(self) -> Hashable:
        if not self._items:
            raise RuntimeError("Stack is empty")
        return self._items.pop()

    def is_empty(self) -> bool:
        return not self._items


class Queue:
    def __init__(self) -> None:
        self._items: deque[Hashable] = deque()

    def enqueue(self, value: Hashable) -> None:
        self._items.append(value)

    def dequeue(self) -> Hashable:
        if not self._items:
            raise RuntimeError("Queue is empty")
        return self._items.popleft()

    def is_empty(self) -> bool:
        return not self._items


def dfs_search(graph: Dict[Hashable, Iterable[Hashable]], source: Hashable) -> Dict[Hashable, Hashable]:
    marked: Dict[Hashable, bool] = {source: True}
    node_from: Dict[Hashable, Hashable] = {}
    stack = Stack()
    stack.push(source)

    while not stack.is_empty():
        vertex = stack.pop()
        for neighbor in graph[vertex]:
            if neighbor not in marked:
                node_from[neighbor] = vertex
                marked[neighbor] = True
                stack.push(neighbor)
    return node_from


def bfs_search(graph: Dict[Hashable, Iterable[Hashable]], source: Hashable) -> Dict[Hashable, Hashable]:
    marked: Dict[Hashable, bool] = {source: True}
    node_from: Dict[Hashable, Hashable] = {}
    queue = Queue()
    queue.enqueue(source)

    while not queue.is_empty():
        vertex = queue.dequeue()
        for neighbor in graph[vertex]:
            if neighbor not in marked:
                node_from[neighbor] = vertex
                marked[neighbor] = True
                queue.enqueue(neighbor)
    return node_from


def path_to(node_from: Dict[Hashable, Hashable], source: Hashable, target: Hashable) -> List[Hashable]:
    if target not in node_from and target != source:
        raise ValueError("Unreachable")
    path = [target]
    while path[-1] != source:
        path.append(node_from[path[-1]])
    path.reverse()
    return path

