import random

from classes.classes import Enemy, Mage, Player
from game_logic.core import Battle, dealDamage, roll


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
