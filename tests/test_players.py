from classes.classes import Item, Mage, Player
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
