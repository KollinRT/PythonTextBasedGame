"""High level game logic including movement, encounters and combat.

The original project kept the bulk of the game flow in a long procedural module.
For the new requirements we expose a ``GameEngine`` that can be used by both the
text interface and the pygame user interface.  The engine is intentionally
stateless regarding input handling – callers provide commands and receive events
that describe what happened during the turn.  This makes the code easy to test
and enables richer front-ends in the future.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from classes.classes import Enemy, Mage, Player
from game_logic.simple_graph import Graph
from items.items import FishingCatch, Shop, go_fishing, random_loot_drop
from maps.beginner_map import create_beginner_map
from maps.intermediate_map import create_intermediate_map


def roll(rng: Optional[random.Random] = None) -> int:
    """Return a percentile roll between 0 and 100 (inclusive)."""

    rng = rng or random
    return int(rng.random() * 100)


def dealDamage(player: Player, enemy: Enemy, rng: Optional[random.Random] = None) -> int:
    """Deal physical damage from ``player`` to ``enemy`` and return the amount."""

    rng = rng or random
    damage = player.dmg
    if rng.random() < player.crit_chance:
        damage = int(damage * player.crit_dmg)
    enemy.take_damage(damage)
    return damage


@dataclass(slots=True)
class BattleEvent:
    """A single action performed during a battle."""

    source: str
    target: str
    description: str


@dataclass(slots=True)
class BattleResult:
    """Outcome of a battle resolution."""

    xp_gained: int = 0
    gold_gained: int = 0
    loot: List[str] = field(default_factory=list)
    events: List[BattleEvent] = field(default_factory=list)


@dataclass
class Battle:
    """Manage turn based combat supporting multiple enemies."""

    players: List[Player]
    enemies: List[Enemy]
    rng: random.Random = field(default_factory=random.Random)
    events: List[BattleEvent] = field(default_factory=list)

    def is_over(self) -> bool:
        return not any(p.is_alive() for p in self.players) or not any(e.is_alive() for e in self.enemies)

    def _living_players(self) -> List[Player]:
        return [player for player in self.players if player.is_alive()]

    def _living_enemies(self) -> List[Enemy]:
        return [enemy for enemy in self.enemies if enemy.is_alive()]

    def player_action(self, player: Player, action: Tuple[str, Optional[str], Optional[int]] | None = None) -> None:
        """Execute a player's action.

        ``action`` is a tuple ``(kind, spell_name, target_index)`` where ``kind`` is
        either ``"attack"`` or ``"spell"``.  When ``action`` is ``None`` the player
        performs a default basic attack against the first living enemy.
        """

        if not player.is_alive():
            return
        living_enemies = self._living_enemies()
        if not living_enemies:
            return
        kind = "attack"
        spell_name: Optional[str] = None
        target_index = 0
        if action:
            kind, spell_name, target_index = action
        target_index = max(0, min(target_index if target_index is not None else 0, len(living_enemies) - 1))
        target = living_enemies[target_index]

        if kind == "spell" and isinstance(player, Mage) and spell_name:
            damage = player.cast_spell(spell_name, target)
            description = f"casts {spell_name} for {damage} damage"
        else:
            damage = player.attack_damage()
            target.take_damage(damage)
            description = f"attacks for {damage} damage"
        self.events.append(BattleEvent(player.name, target.name, description))

    def enemy_turn(self) -> None:
        for enemy in self._living_enemies():
            players = self._living_players()
            if not players:
                return
            target = enemy.decide_target(players)
            damage = enemy.attack_damage()
            target.take_damage(damage)
            self.events.append(BattleEvent(enemy.name, target.name, f"attacks for {damage} damage"))

    def resolve(self, player_actions: Optional[Dict[str, Tuple[str, Optional[str], Optional[int]]]] = None) -> BattleResult:
        """Resolve the battle until one side is defeated."""

        result = BattleResult(events=self.events)
        while not self.is_over():
            for player in self.players:
                action = None
                if player_actions and player.name in player_actions:
                    action = player_actions[player.name]
                self.player_action(player, action)
            if self.is_over():
                break
            self.enemy_turn()
        if not any(enemy.is_alive() for enemy in self.enemies):
            for enemy in self.enemies:
                result.xp_gained += enemy.exp_worth
                result.gold_gained += enemy.gp_worth
            return result
        else:
            return result


@dataclass
class NodeEvent:
    kind: str
    payload: Optional[str] = None


class GameEngine:
    """High level orchestrator for world traversal and encounters."""

    def __init__(self, rng: Optional[random.Random] = None) -> None:
        self.rng = rng or random.Random()
        self.maps: Dict[str, Graph] = {
            "beginner": create_beginner_map(),
            "intermediate": create_intermediate_map(),
        }
        self.current_map_key = "beginner"
        self.active_map = self.maps[self.current_map_key]
        self.current_node = "A0"
        self.player_party: List[Player] = []
        self.shop = Shop.default()
        self.event_log: List[str] = []
        self.battle: Optional[Battle] = None

    # ------------------------------------------------------------------
    # Game setup
    # ------------------------------------------------------------------
    def start_new_game(self, player: Player) -> None:
        self.player_party = [player]
        self.current_map_key = "beginner"
        self.active_map = self.maps[self.current_map_key]
        self.current_node = "A0"
        self.event_log.clear()
        self.event_log.append(f"{player.name} enters the realm at {self.current_node}.")

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------
    def neighbors(self) -> List[str]:
        return list(self.active_map.neighbors(self.current_node))

    def move_to(self, node: str) -> List[NodeEvent]:
        if node not in self.neighbors():
            raise ValueError(f"Cannot move to {node} from {self.current_node}")
        self.current_node = node
        self.event_log.append(f"Moved to {node}")
        return self._handle_node()

    # ------------------------------------------------------------------
    # Node interactions
    # ------------------------------------------------------------------
    def _handle_node(self) -> List[NodeEvent]:
        node_data = self.active_map.nodes[self.current_node]
        events: List[NodeEvent] = []
        if node_data.get("encounter"):
            if self.rng.random() < 0.35:
                events.append(self._start_battle())
        if node_data.get("shop"):
            events.append(NodeEvent("shop"))
        if node_data.get("fishing"):
            catch = self.handle_fishing()
            events.append(NodeEvent("fishing", payload=f"Caught {catch.name}"))
        if node_data.get("city"):
            events.append(NodeEvent("city", payload="Safe to rest"))
        if transition := node_data.get("transition"):
            events.append(self.transition_map(transition))
        return [event for event in events if event]

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------
    def _generate_enemies(self) -> List[Enemy]:
        base_level = max(player.level for player in self.player_party)
        count = self.rng.randint(1, 3)
        enemies = []
        for idx in range(count):
            level = max(1, base_level + self.rng.randint(-1, 1))
            hp = 40 + level * 10
            dmg = 5 + level * 3
            enemy = Enemy(name=f"Goblin {idx+1}", level=level, hp=hp, dmg=dmg, exp_worth=150 + level * 25, gp_worth=8 + level * 3)
            enemies.append(enemy)
        return enemies

    def _start_battle(self) -> NodeEvent:
        enemies = self._generate_enemies()
        self.battle = Battle(self.player_party, enemies, rng=self.rng)
        result = self.battle.resolve()
        self._apply_battle_rewards(result)
        description = f"Defeated {len(enemies)} enemies" if not any(e.is_alive() for e in enemies) else "Party was defeated"
        return NodeEvent("battle", payload=description)

    def _apply_battle_rewards(self, result: BattleResult) -> None:
        if result.events:
            self.event_log.extend(f"{event.source} -> {event.target}: {event.description}" for event in result.events)
        if result.xp_gained:
            for player in self.player_party:
                player.gain_exp(result.xp_gained)
        if result.gold_gained:
            for player in self.player_party:
                player.add_gold(result.gold_gained)
        if not result.events:
            return
        if not any(enemy.is_alive() for enemy in self.battle.enemies):
            loot_item = random_loot_drop(max(player.level for player in self.player_party))
            self.player_party[0].add_item(loot_item)
            self.event_log.append(f"Looted {loot_item.name}")

    # ------------------------------------------------------------------
    # Fishing and shop interactions
    # ------------------------------------------------------------------
    def handle_fishing(self) -> FishingCatch:
        player = self.player_party[0]
        catch = go_fishing(player.level)
        player.add_gold(catch.gold_reward)
        player.gain_exp(catch.xp_reward)
        self.event_log.append(f"Fishing success: {catch.name}")
        return catch

    def purchase_item(self, item_name: str) -> Item:
        player = self.player_party[0]
        item = self.shop.purchase(item_name, player.gp)
        player.spend_gold(item.value)
        player.add_item(item)
        self.event_log.append(f"Purchased {item_name}")
        return item

    # ------------------------------------------------------------------
    # Map transitions
    # ------------------------------------------------------------------
    def transition_map(self, key: str) -> NodeEvent:
        if key not in self.maps:
            raise KeyError(f"Unknown map '{key}'")
        self.current_map_key = key
        self.active_map = self.maps[key]
        self.current_node = next(iter(self.active_map.nodes))
        self.event_log.append(f"Traveled to {key} map")
        return NodeEvent("transition", payload=key)


def startGame(player_name: str, player_class: str) -> Player:
    """Factory used by the CLI entry point to create a player instance."""

    player_class = player_class.lower()
    if player_class == "mage":
        return Mage(player_name, 1, 100, 40, 12)
    return Player(player_name, 1, 120, 15)

