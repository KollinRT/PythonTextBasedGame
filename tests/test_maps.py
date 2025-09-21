from maps.beginner_map import create_beginner_map
from maps.intermediate_map import create_intermediate_map


def test_beginner_map_has_transition():
    graph = create_beginner_map()
    assert graph.nodes["A7"]["transition"] == "intermediate"


def test_intermediate_map_round_trip():
    graph = create_intermediate_map()
    assert graph.nodes["B7"]["transition"] == "beginner"
