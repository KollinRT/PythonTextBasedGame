"""Definitions of items, shops and drop tables used throughout the game."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, List

from classes.classes import Item


POTION_LIBRARY: Dict[str, Item] = {
    "basic_hp": Item("Basic HP Potion", level=1, slot="potion", hp=25, value=25),
    "basic_mp": Item("Basic MP Potion", level=1, slot="potion", mp=25, value=30),
    "greater_hp": Item("Greater HP Potion", level=5, slot="potion", hp=50, value=75),
    "greater_mp": Item("Greater MP Potion", level=5, slot="potion", mp=50, value=80),
}


def create_potion(key: str, *, quantity: int = 1) -> Item:
    potion = POTION_LIBRARY[key]
    return potion.copy(quantity=quantity)


WEAPON_LIBRARY: Dict[str, Item] = {
    "training_sword": Item("Training Sword", level=1, slot="weapon", dmg=4, value=50),
    "oak_staff": Item("Oak Staff", level=1, slot="weapon", dmg=3, value=45),
    "iron_sword": Item("Iron Sword", level=3, slot="weapon", dmg=7, value=120),
}


ARMOR_LIBRARY: Dict[str, Item] = {
    "leather_armor": Item("Leather Armor", level=1, slot="armor", value=60),
    "apprentice_robe": Item("Apprentice Robe", level=1, slot="armor", value=55),
    "iron_mail": Item("Iron Mail", level=3, slot="armor", value=140),
}


def default_shop_stock() -> Dict[str, Item]:
    stock = {}
    for item in [
        create_potion("basic_hp", quantity=3),
        create_potion("basic_mp", quantity=3),
        WEAPON_LIBRARY["training_sword"].copy(),
        ARMOR_LIBRARY["leather_armor"].copy(),
    ]:
        stock[item.name] = item
    return stock


def random_loot_drop(level: int) -> Item:
    """Return an item appropriate for the player's level."""

    possible: List[Item] = [create_potion("basic_hp")]
    if level >= 3:
        possible.append(WEAPON_LIBRARY["iron_sword"].copy())
    if level >= 5:
        possible.append(create_potion("greater_hp"))
    return random.choice(possible)


def sort_items(items: Iterable[Item], key: str = "name") -> List[Item]:
    if key not in {"name", "level", "value"}:
        raise ValueError("key must be 'name', 'level' or 'value'")
    return sorted(items, key=lambda item: getattr(item, key))


@dataclass(slots=True)
class Shop:
    """Simple shop implementation with inventory and purchase support."""

    inventory: Dict[str, Item]

    @classmethod
    def default(cls) -> "Shop":
        return cls(default_shop_stock())

    def list_items(self) -> List[Item]:
        return list(self.inventory.values())

    def purchase(self, item_name: str, gold: int) -> Item:
        if item_name not in self.inventory:
            raise KeyError("Item not carried by shop")
        item = self.inventory[item_name]
        if gold < item.value:
            raise ValueError("Not enough gold to purchase item")
        self.inventory[item_name].quantity -= 1
        if self.inventory[item_name].quantity <= 0:
            del self.inventory[item_name]
        return item.copy(quantity=1)


@dataclass(slots=True)
class FishingCatch:
    name: str
    gold_reward: int
    xp_reward: int


FISHING_TABLE: List[FishingCatch] = [
    FishingCatch("Minnow", gold_reward=5, xp_reward=10),
    FishingCatch("River Trout", gold_reward=12, xp_reward=20),
    FishingCatch("Golden Carp", gold_reward=50, xp_reward=60),
]


def go_fishing(level: int) -> FishingCatch:
    weights = [0.6, 0.3, 0.1 if level >= 5 else 0.0]
    catch = random.choices(FISHING_TABLE, weights=weights, k=1)[0]
    return catch

