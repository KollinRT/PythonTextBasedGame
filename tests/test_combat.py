import random

from classes.classes import Enemy, Mage, Player
from game_logic.core import Battle, GameEngine, NodeEvent, dealDamage, roll


def test_roll_returns_percentage():
    value = roll(random.Random(0))
    assert 0 <= value <= 100


def test_deal_damage_reduces_enemy_hp():
    hero = Player("Hero", 1, 100, 15)
    foe = Enemy("Goblin", 1, 60, 5)
    original_hp = foe.hp
    damage = dealDamage(hero, foe, random.Random(1))
    assert foe.hp == original_hp - damage


def test_battle_handles_multiple_enemies():
    hero = Mage("Mage", 3, 90, 50, 12)
    enemies = [Enemy("Goblin 1", 2, 50, 6), Enemy("Goblin 2", 2, 50, 6)]
    battle = Battle([hero], enemies, rng=random.Random(2))
    result = battle.resolve()
    assert all(not enemy.is_alive() for enemy in enemies)
    assert result.xp_gained > 0


def test_battle_event_includes_details_and_rewards(monkeypatch):
    engine = GameEngine(rng=random.Random(1))
    hero = Player("Hero", 1, 200, 40)
    engine.start_new_game(hero)

    def fake_generate_enemies():
        return [Enemy("Goblin", 1, 40, 1, exp_worth=120, gp_worth=15)]

    monkeypatch.setattr(engine, "_generate_enemies", fake_generate_enemies)
    event = engine._start_battle()
    assert event.kind == "battle"
    assert event.payload.startswith("Defeated")
    assert any(line.startswith("Hero") for line in event.details)
    assert any("Gained" in line for line in event.details)
    assert hero.exp >= 120
    assert hero.gp >= 15


def test_handle_node_stops_after_defeat(monkeypatch):
    engine = GameEngine(rng=random.Random(2))
    hero = Player("Hero", 1, 100, 10)
    engine.start_new_game(hero)
    node = engine.current_node
    engine.active_map.nodes[node]["encounter"] = True
    engine.active_map.nodes[node]["shop"] = True
    engine.active_map.nodes[node]["fishing"] = True
    battle_event = NodeEvent("battle", payload="Party was defeated", game_over=True)
    monkeypatch.setattr(engine, "_start_battle", lambda: battle_event)
    monkeypatch.setattr(engine.rng, "random", lambda: 0.0)
    events = engine._handle_node()
    assert events == [battle_event]
