from classes.classes import Cleric, Enemy, Item, Mage, Player, Ranger
from classes.items import HealingItems


def test_player_inventory_management():
    player = Player("Hero", 1, 100, 10)
    sword = Item("Training Sword", level=1, slot="weapon", dmg=4)
    player.add_item(sword)
    assert "Training Sword" in player.inventory
    player.equip_item("Training Sword")
    assert player.equipment["weapon"].name == "Training Sword"


def test_use_potion_restores_resources():
    mage = Mage("Mage", 1, 60, 20, 8)
    potion = Item("Basic HP Potion", level=1, slot="potion", hp=25)
    mage.potions[potion.name] = potion
    mage.take_damage(30)
    mage.use_potion("Basic HP Potion")
    assert mage.hp == mage.max_hp - 5


def test_healing_item_helper():
    mage = Mage("Mage", 1, 50, 20, 8)
    item = HealingItems(20, 10)
    mage.take_damage(25)
    mage.mp = 5
    item.healPlayer(mage)
    assert mage.hp == mage.max_hp - 5
    assert mage.mp == 15


def test_ranger_abilities_consume_focus():
    ranger = Ranger("Archer", 5, 110, 18, focus=3)
    abilities = ranger.available_abilities()
    assert "power shot" in abilities
    assert "twin strike" in abilities
    damage, description = ranger.use_ability("power shot", Enemy("Dummy", 1, 80, 5))
    assert damage >= ranger.dmg  # ability hits harder than base attack
    assert "Power Shot" in description
    assert ranger.focus == 2


def test_cleric_spells_available_by_level():
    cleric = Cleric("Healer", 1, 90, 45, 10)
    spells = [spell.name for spell in cleric.available_spells()]
    assert "healing prayer" in spells
    assert "smite" in spells
    assert "radiance" not in spells
    cleric.level = 5
    cleric.mp = cleric.max_mp
    spells = [spell.name for spell in cleric.available_spells()]
    assert "radiance" in spells


def test_cleric_healing_spell_restores_hp():
    cleric = Cleric("Healer", 1, 90, 45, 10)
    cleric.take_damage(40)
    healed = cleric.cast_spell("healing prayer")
    assert healed > 0
    assert cleric.hp > cleric.max_hp - 40
