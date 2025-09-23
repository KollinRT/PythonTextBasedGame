import random

from game_logic.map_generation import generate_blueprint
from maps.beginner_map import create_beginner_map
from maps.intermediate_map import create_intermediate_map
from maps.advanced_map import create_advanced_map


def test_beginner_map_has_transition():
    graph = create_beginner_map()
    assert graph.nodes["A7"]["transition"] == "intermediate"


def test_intermediate_map_round_trip():
    graph = create_intermediate_map()
    assert graph.nodes["B5"]["transition"] == "advanced"
    assert graph.nodes["B7"]["transition"] == "beginner"


def test_advanced_map_links_regions():
    graph = create_advanced_map()
    assert graph.nodes["C0"]["transition"] == "intermediate"
    assert graph.nodes["C11"]["transition"] == "auto"


def test_generated_map_uses_numeric_nodes():
    blueprint = generate_blueprint("frontier_test", size=6, rng=random.Random(0))
    assert all(node.isdigit() for node in blueprint.nodes)
