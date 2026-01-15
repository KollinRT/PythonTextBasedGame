import random

import pytest

from classes.classes import Cleric, Enemy, Item, Mage, Player, Ranger
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


def test_start_battle_creates_active_battle(monkeypatch, tmp_path):
    engine = GameEngine(rng=random.Random(1), db_path=str(tmp_path / "game.db"))
    hero = Player("Hero", 1, 120, 20)
    engine.start_new_game(hero)

    enemies = [Enemy("Goblin", 1, 50, 5), Enemy("Goblin Chief", 2, 60, 7)]
    monkeypatch.setattr(engine, "_generate_enemies", lambda: enemies)

    event = engine._start_battle()
    assert engine.in_battle()
    assert event.kind == "battle"
    assert event.payload.startswith("Encountered")
    assert len(event.details) >= len(enemies)
    for idx, enemy in enumerate(enemies):
        assert enemy.name in event.details[idx]


def test_perform_player_action_attack_awards_victory(monkeypatch, tmp_path):
    engine = GameEngine(rng=random.Random(2), db_path=str(tmp_path / "game.db"))
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


def test_perform_player_action_potion_triggers_enemy_turn(monkeypatch, tmp_path):
    engine = GameEngine(rng=random.Random(3), db_path=str(tmp_path / "game.db"))
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
    assert any("Awaiting command" in line for line in event.details)
    assert "Basic HP Potion" not in hero.potions
    assert hero.hp > 80


def test_cleric_can_heal_specific_ally(monkeypatch, tmp_path):
    engine = GameEngine(rng=random.Random(11), db_path=str(tmp_path / "game.db"))
    cleric = Cleric("Seren", 3, 90, 40, 12)
    ally = Player("Bran", 3, 120, 18)
    engine.start_new_game(cleric)
    engine.recruit_ally(ally)
    ally.take_damage(45)

    enemy = Enemy("Ogre", 3, 110, 10)
    monkeypatch.setattr(engine, "_generate_enemies", lambda: [enemy])
    engine._start_battle()

    assert engine.battle is not None
    battle = engine.battle
    battle._turn_queue = [
        (0.9, cleric),
        (0.8, ally),
        (0.7, enemy),
    ]
    battle._turn_index = 0

    previous_hp = ally.hp
    event = engine.perform_player_action(
        "spell",
        name="Healing Prayer",
        target_kind="ally",
        target_name=ally.name,
    )

    assert ally.hp > previous_hp
    assert any(ally.name in line for line in event.details)
    assert any("healing prayer" in line.lower() for line in event.details)


def test_pet_can_receive_manual_commands(tmp_path):
    engine = GameEngine(rng=random.Random(9), db_path=str(tmp_path / "game.db"))
    ranger = Ranger("Robin", 3, 120, 18)
    engine.start_new_game(ranger)
    engine._refresh_party()
    enemy = Enemy("Bandit", 2, 55, 8)
    battle = Battle(engine.player_party, [enemy], rng=random.Random(4))
    battle._turn_queue = [
        (0.9, ranger.pet),
        (0.8, ranger),
        (0.7, enemy),
    ]
    battle._turn_index = 0
    engine.battle = battle

    event = engine.perform_player_action("attack", actor_name=ranger.pet.name)
    assert event.payload == "Battle continues"
    assert any(ranger.pet.name in line for line in event.details)
    assert enemy.hp < enemy.max_hp


def test_pet_command_rejected_outside_turn(tmp_path):
    engine = GameEngine(rng=random.Random(10), db_path=str(tmp_path / "game.db"))
    ranger = Ranger("Robin", 3, 120, 18)
    engine.start_new_game(ranger)
    engine._refresh_party()
    enemy = Enemy("Bandit", 2, 55, 8)
    battle = Battle(engine.player_party, [enemy], rng=random.Random(5))
    battle._turn_queue = [
        (0.8, ranger),
        (0.7, ranger.pet),
        (0.6, enemy),
    ]
    battle._turn_index = 0
    engine.battle = battle

    with pytest.raises(ValueError):
        engine.perform_player_action("attack", actor_name=ranger.pet.name)



def test_handle_node_stops_for_battle(monkeypatch, tmp_path):
    engine = GameEngine(rng=random.Random(2), db_path=str(tmp_path / "game.db"))
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


def test_generate_new_map_adds_to_engine(tmp_path):
    engine = GameEngine(rng=random.Random(4), db_path=str(tmp_path / "game.db"))
    hero = Player("Hero", 1, 110, 15)
    engine.start_new_game(hero)
    existing_maps = set(engine.maps.keys())
    event = engine.generate_new_map(size=8)
    assert event.payload
    new_maps = set(engine.maps.keys()) - existing_maps
    assert new_maps


def test_save_and_load_game_roundtrip(tmp_path):
    db_path = tmp_path / "game.db"
    engine = GameEngine(rng=random.Random(5), db_path=str(db_path))
    hero = Player("Hero", 1, 120, 18)
    engine.start_new_game(hero)
    ally = Player("Scout", 1, 90, 12)
    engine.recruit_ally(ally)
    hero.gain_exp(250)
    engine.save_game("slot1")

    restored = GameEngine(rng=random.Random(6), db_path=str(db_path))
    restored.load_game("slot1")
    assert restored.hero is not None
    assert restored.hero.name == "Hero"
    assert any(member.name == "Scout" for member in restored.player_party)
    assert restored.hero.level >= hero.level


def test_recruit_ally_extends_party(tmp_path):
    engine = GameEngine(rng=random.Random(7), db_path=str(tmp_path / "game.db"))
    hero = Player("Hero", 1, 110, 16)
    engine.start_new_game(hero)
    ally = engine._spawn_ally({"name": "Aria", "class": "cleric", "level_bonus": 0})
    event = engine.recruit_ally(ally)
    assert event.kind == "ally"
    assert any(member.name == "Aria" for member in engine.player_party)
