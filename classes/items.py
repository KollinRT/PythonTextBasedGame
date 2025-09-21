"""Utility classes representing consumable items used by the game logic."""

from __future__ import annotations

from dataclasses import dataclass

from classes.classes import Mage, Player


@dataclass(slots=True)
class HealingItems:
    """Simple healing consumable used by the potion system."""

    HPrest: int = 0
    MPrest: int = 0

    def healPlayer(self, player: Player) -> None:
        player.heal(self.HPrest)
        if isinstance(player, Mage) and self.MPrest:
            player.mp = min(player.max_mp, player.mp + self.MPrest)

