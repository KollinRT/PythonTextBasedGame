"""Simple search algorithms used for documentation and testing."""

from __future__ import annotations

from typing import Iterable, Sequence


def binary_search(sequence: Sequence[int], target: int) -> int | None:
    low = 0
    high = len(sequence) - 1
    while low <= high:
        mid = (low + high) // 2
        value = sequence[mid]
        if value == target:
            return mid
        if value < target:
            low = mid + 1
        else:
            high = mid - 1
    return None


def insertion_index(sequence: Sequence[int], target: int) -> int:
    low = 0
    high = len(sequence)
    while low < high:
        mid = (low + high) // 2
        if sequence[mid] < target:
            low = mid + 1
        else:
            high = mid
    return low

