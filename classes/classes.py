"""Core character classes for the adventure game.

The original project exposed a couple of loosely connected classes that kept
their state in module level globals.  For the refactor required by the new
features we provide a small collection of data classes and helpers that make the
rest of the codebase easier to reason about.  All entities now keep their state
locally which makes them reusable both by the text engine and by the pygame
front-end introduced in this change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(slots=True)
class Item:
    """Representation of an inventory item.

    Attributes
    ----------
    name:
        Human readable name of the item.
    level:
        Minimum level required to make use of the item.
    slot:
        Slot type (``weapon``, ``armor``, ``shield`` or ``potion``).
    dmg / hp / mp:
        Numeric modifiers used by the combat and utility systems.
    value:
        Gold value of the item when sold or purchased from the shop.
    quantity:
        Stack size for consumables.  Equipment is treated as a quantity of 1.
    """

    name: str
    level: int = 1
    slot: str = "misc"
    dmg: int = 0
    hp: int = 0
    mp: int = 0
    value: int = 0
    quantity: int = 1

    def copy(self, *, quantity: Optional[int] = None) -> "Item":
        return Item(
            name=self.name,
            level=self.level,
            slot=self.slot,
            dmg=self.dmg,
            hp=self.hp,
            mp=self.mp,
            value=self.value,
            quantity=self.quantity if quantity is None else quantity,
        )


@dataclass(slots=True)
class Spell:
    name: str
    level_req: int
    mp_cost: int
    damage: int = 0
    healing: int = 0


class Player:
    """Base player class supporting inventory, levelling and combat helpers."""

    exp_to_level: List[int] = [
        0,
        200,
        500,
        900,
        1400,
        2000,
        2700,
        3500,
        4400,
        5400,
        6500,
        7700,
        9000,
        10400,
        11900,
    ]

    def __init__(
        self,
        name: str,
        level: int,
        hp: int,
        dmg: int,
        *,
        crit_dmg: float = 1.25,
        crit_chance: float = 0.1,
        exp: int = 0,
        gp: int = 0,
    ) -> None:
        self.name = name
        self.level = level
        self.max_hp = hp
        self.hp = hp
        self.dmg = dmg
        self.crit_dmg = crit_dmg
        self.crit_chance = crit_chance
        self.exp = exp
        self.gp = gp
        self.inventory: Dict[str, Item] = {}
        self.potions: Dict[str, Item] = {}
        self.equipment: Dict[str, Item] = {}
        self.following: List[Player] = []
        self.levels_attained: List[int] = []

    # ------------------------------------------------------------------
    # Basic combat helpers
    # ------------------------------------------------------------------
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: float) -> int:
        self.hp = max(0, int(self.hp - amount))
        return self.hp

    def heal(self, amount: float) -> int:
        self.hp = min(self.max_hp, int(self.hp + amount))
        return self.hp

    def attack_damage(self) -> int:
        damage = self.dmg
        if random.random() < self.crit_chance:
            damage = int(damage * self.crit_dmg)
        return damage

    def gain_exp(self, amount: int) -> None:
        self.exp += amount
        self._process_level_ups()

    def add_gold(self, amount: int) -> None:
        self.gp += amount

    def spend_gold(self, amount: int) -> None:
        if amount > self.gp:
            raise ValueError("Not enough gold")
        self.gp -= amount

    # ------------------------------------------------------------------
    # Inventory management
    # ------------------------------------------------------------------
    def add_item(self, item: Item, *, to_potions: bool = False) -> None:
        target = self.potions if (to_potions or item.slot == "potion") else self.inventory
        stored = target.get(item.name)
        if stored:
            stored.quantity += item.quantity
        else:
            target[item.name] = item.copy()

    def remove_item(self, name: str, *, from_potions: bool = False) -> None:
        target = self.potions if from_potions else self.inventory
        if name not in target:
            raise KeyError(f"{name} not in inventory")
        target[name].quantity -= 1
        if target[name].quantity <= 0:
            del target[name]

    def sort_inventory(self, *, key: str = "name") -> List[Item]:
        if key not in {"name", "level", "value"}:
            raise ValueError("key must be one of 'name', 'level', 'value'")
        return sorted(self.inventory.values(), key=lambda item: getattr(item, key))

    def use_potion(self, name: str) -> None:
        if name not in self.potions:
            raise KeyError(f"Potion {name} not in inventory")
        potion = self.potions[name]
        if self.level < potion.level:
            raise ValueError("Level too low to use potion")
        self.heal(potion.hp)
        if hasattr(self, "mp") and potion.mp:
            self.mp = min(self.max_mp, int(self.mp + potion.mp))
        self.remove_item(name, from_potions=True)

    # ------------------------------------------------------------------
    # Levelling
    # ------------------------------------------------------------------
    def _process_level_ups(self) -> None:
        while self.level < len(self.exp_to_level) and self.exp >= self.exp_to_level[self.level]:
            self._level_up()

    def _level_up(self) -> None:
        self.level += 1
        self.max_hp += random.randint(2, 8)
        self.hp = self.max_hp
        self.dmg += random.randint(1, 4)

    # ------------------------------------------------------------------
    # Equipment helpers
    # ------------------------------------------------------------------
    def equip_item(self, name: str) -> None:
        item = self.inventory.get(name)
        if not item:
            raise KeyError(f"{name} not in inventory")
        if self.level < item.level:
            raise ValueError("Level too low to equip item")
        previous = self.equipment.get(item.slot)
        if previous:
            self.add_item(previous)
        self.equipment[item.slot] = item.copy(quantity=1)
        self.remove_item(name)

    def unequip_item(self, slot: str) -> None:
        item = self.equipment.pop(slot, None)
        if item:
            self.add_item(item)


class Enemy(Player):
    """Extension of :class:`Player` tailored for opponents."""

    def __init__(
        self,
        name: str,
        level: int,
        hp: int,
        dmg: int,
        *,
        crit_dmg: float = 1.1,
        crit_chance: float = 0.05,
        exp_worth: int = 250,
        gp_worth: int = 10,
    ) -> None:
        super().__init__(
            name,
            level,
            hp,
            dmg,
            crit_dmg=crit_dmg,
            crit_chance=crit_chance,
        )
        self.exp_worth = exp_worth
        self.gp_worth = gp_worth

    def level_up(self) -> None:  # pragma: no cover - enemies are usually spawned at level
        super()._level_up()
        self.exp_worth += 50
        self.gp_worth += 20

    def decide_target(self, players: Iterable[Player]) -> Player:
        living = [player for player in players if player.is_alive()]
        return random.choice(living)


class Mage(Player):
    default_spells: List[Spell] = [
        Spell("fireball", level_req=1, mp_cost=3, damage=12),
        Spell("gust", level_req=5, mp_cost=6, damage=22),
        Spell("blizzard", level_req=10, mp_cost=10, damage=30),
    ]

    def __init__(
        self,
        name: str,
        level: int,
        hp: int,
        mp: int,
        dmg: int,
        *,
        crit_dmg: float = 1.25,
        crit_chance: float = 0.1,
        exp: int = 0,
        gp: int = 0,
        spells: Optional[Iterable[Spell]] = None,
    ) -> None:
        super().__init__(
            name,
            level,
            hp,
            dmg,
            crit_dmg=crit_dmg,
            crit_chance=crit_chance,
            exp=exp,
            gp=gp,
        )
        self.max_mp = mp
        self.mp = mp
        base_spells = list(spells) if spells is not None else list(self.default_spells)
        self.spells: Dict[str, Spell] = {spell.name: spell for spell in base_spells}

    def restore_resources(self, hp_ratio: float = 0.05, mp_ratio: float = 0.3) -> None:
        self.heal(self.max_hp * hp_ratio)
        self.mp = min(self.max_mp, int(self.mp + self.max_mp * mp_ratio))

    def spend_mp(self, amount: int) -> None:
        if amount > self.mp:
            raise ValueError("Not enough MP")
        self.mp -= amount

    def available_spells(self) -> List[Spell]:
        return [spell for spell in self.spells.values() if spell.level_req <= self.level and spell.mp_cost <= self.mp]

    def cast_spell(self, name: str, target: Player | Enemy | None = None) -> int:
        spell = self.spells.get(name)
        if not spell:
            raise KeyError(f"Unknown spell {name}")
        if spell.level_req > self.level:
            raise ValueError("Level too low to cast spell")
        if spell.mp_cost > self.mp:
            raise ValueError("Not enough MP to cast spell")
        self.spend_mp(spell.mp_cost)
        if spell.healing > 0:
            # Healing spells default to restoring the caster if no explicit target
            ally = target if isinstance(target, Player) else self
            before = ally.hp
            ally.heal(spell.healing)
            return ally.hp - before
        if not isinstance(target, Enemy):
            raise ValueError("A damage spell requires an enemy target")
        damage = spell.damage
        if random.random() < self.crit_chance:
            damage = int(damage * self.crit_dmg)
        target.take_damage(damage)
        return damage

    def _level_up(self) -> None:
        super()._level_up()
        mp_increase = random.randint(2, 6)
        self.max_mp += mp_increase
        self.mp = self.max_mp


class Ranger(Player):
    """Agile ranged fighter with a focus resource for abilities."""

    def __init__(
        self,
        name: str,
        level: int,
        hp: int,
        dmg: int,
        *,
        crit_dmg: float = 1.5,
        crit_chance: float = 0.18,
        exp: int = 0,
        gp: int = 0,
        focus: int = 2,
    ) -> None:
        super().__init__(
            name,
            level,
            hp,
            dmg,
            crit_dmg=crit_dmg,
            crit_chance=crit_chance,
            exp=exp,
            gp=gp,
        )
        self.max_focus = focus
        self.focus = focus

    def reset_focus(self) -> None:
        self.focus = self.max_focus

    def available_abilities(self) -> List[str]:
        abilities: List[str] = []
        if self.focus >= 1:
            abilities.append("power shot")
        if self.focus >= 2 and self.level >= 5:
            abilities.append("twin strike")
        return abilities

    def use_ability(self, name: str, target: Enemy) -> Tuple[int, str]:
        ability = name.lower()
        if ability == "power shot":
            if self.focus < 1:
                raise ValueError("Not enough focus to use power shot")
            self.focus -= 1
            damage = int(self.dmg * 1.5)
            if random.random() < self.crit_chance:
                damage = int(damage * self.crit_dmg)
            target.take_damage(damage)
            return damage, f"uses Power Shot for {damage} damage"
        if ability == "twin strike":
            if self.level < 5:
                raise ValueError("Level too low to use twin strike")
            if self.focus < 2:
                raise ValueError("Not enough focus to use twin strike")
            self.focus -= 2
            first = self.attack_damage()
            second = self.attack_damage()
            total = first + second
            target.take_damage(total)
            return total, f"unleashes Twin Strike for {total} total damage"
        raise KeyError(f"Unknown ability {name}")

    def _level_up(self) -> None:
        super()._level_up()
        if self.level % 3 == 0:
            self.max_focus += 1
        self.focus = self.max_focus


class Cleric(Mage):
    """Holy spellcaster with restorative-oriented spell list."""

    default_spells: List[Spell] = [
        Spell("healing prayer", level_req=1, mp_cost=6, healing=32),
        Spell("smite", level_req=1, mp_cost=4, damage=14),
        Spell("radiance", level_req=4, mp_cost=6, damage=20),
        Spell("divine storm", level_req=8, mp_cost=10, damage=32),
    ]
