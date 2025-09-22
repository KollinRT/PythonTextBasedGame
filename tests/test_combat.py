import random

from classes.classes import Enemy, Item, Mage, Player
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


def test_start_battle_creates_active_battle(monkeypatch):
    engine = GameEngine(rng=random.Random(1))
    hero = Player("Hero", 1, 120, 20)
    engine.start_new_game(hero)

    enemies = [Enemy("Goblin", 1, 50, 5), Enemy("Goblin Chief", 2, 60, 7)]
    monkeypatch.setattr(engine, "_generate_enemies", lambda: enemies)

    event = engine._start_battle()
    assert engine.in_battle()
    assert event.kind == "battle"
    assert event.payload.startswith("Encountered")
    assert len(event.details) == len(enemies)


def test_perform_player_action_attack_awards_victory(monkeypatch):
    engine = GameEngine(rng=random.Random(2))
    hero = Player("Hero", 1, 150, 35)
    engine.start_new_game(hero)

    enemy = Enemy("Goblin", 1, 20, 1, exp_worth=80, gp_worth=12)
    monkeypatch.setattr(engine, "_generate_enemies", lambda: [enemy])
    engine._start_battle()

    event = engine.perform_player_action("attack")
    assert event.payload.startswith("Defeated")
    assert any("Hero" in line for line in event.details)
    assert hero.exp >= 80
    assert hero.gp >= 12
    assert not engine.in_battle()


def test_perform_player_action_potion_triggers_enemy_turn(monkeypatch):
    engine = GameEngine(rng=random.Random(3))
    hero = Player("Hero", 1, 120, 10)
    engine.start_new_game(hero)
    potion = Item("Basic HP Potion", level=1, slot="potion", hp=30)
    hero.potions[potion.name] = potion
    hero.take_damage(40)

    enemy = Enemy("Goblin", 1, 45, 6, exp_worth=40, gp_worth=5)
    monkeypatch.setattr(engine, "_generate_enemies", lambda: [enemy])
    engine._start_battle()

    event = engine.perform_player_action("potion", name="Basic HP Potion")
    assert event.payload == "Battle continues"
    assert any("uses Basic HP Potion" in line for line in event.details)
    assert any("Goblin" in line for line in event.details)
    assert "Basic HP Potion" not in hero.potions
    assert hero.hp > 80



def test_handle_node_stops_for_battle(monkeypatch):
    engine = GameEngine(rng=random.Random(2))
    hero = Player("Hero", 1, 100, 10)
    engine.start_new_game(hero)
    node = engine.current_node
    engine.active_map.nodes[node]["encounter"] = True
    engine.active_map.nodes[node]["shop"] = True
    engine.active_map.nodes[node]["fishing"] = True
    battle_event = NodeEvent("battle", payload="Encountered test", game_over=False)
    monkeypatch.setattr(engine, "_start_battle", lambda: battle_event)
    monkeypatch.setattr(engine.rng, "random", lambda: 0.0)
    events = engine._handle_node()
    assert events == [battle_event]
