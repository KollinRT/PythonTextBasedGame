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

from classes.classes import Cleric, Enemy, Mage, Player, Ranger, Item
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

    def player_action(
        self,
        player: Player,
        action: Tuple[str, Optional[str], Optional[int]] | None = None,
    ) -> Optional[BattleEvent]:
        """Execute a player's action.

        ``action`` is a tuple ``(kind, name, target_index)`` where ``kind`` is one of
        ``"attack"``, ``"spell"`` or ``"ability"``.  When ``action`` is ``None`` the
        player performs a default basic attack against the first living enemy.
        """

        if not player.is_alive():
            return
        living_enemies = self._living_enemies()
        if not living_enemies:
            return
        kind = "attack"
        name: Optional[str] = None
        target_index = 0
        if action:
            kind, name, target_index = action
        target_index = max(0, min(target_index if target_index is not None else 0, len(living_enemies) - 1))
        target = living_enemies[target_index]

        if kind == "spell" and isinstance(player, Mage) and name:
            damage = player.cast_spell(name, target)
            description = f"casts {name} for {damage} damage ({target.hp}/{target.max_hp} HP left)"
        elif kind == "ability" and hasattr(player, "use_ability") and name:
            damage, extra = player.use_ability(name, target)  # type: ignore[attr-defined]
            description = f"{extra} ({target.hp}/{target.max_hp} HP left)"
        else:
            damage = player.attack_damage()
            target.take_damage(damage)
            description = f"attacks for {damage} damage ({target.hp}/{target.max_hp} HP left)"
        event = BattleEvent(player.name, target.name, description)
        self.events.append(event)
        return event

    def enemy_turn(self) -> List[BattleEvent]:
        events: List[BattleEvent] = []
        for enemy in self._living_enemies():
            players = self._living_players()
            if not players:
                break
            target = enemy.decide_target(players)
            damage = enemy.attack_damage()
            target.take_damage(damage)
            description = f"attacks for {damage} damage ({target.hp}/{target.max_hp} HP left)"
            event = BattleEvent(enemy.name, target.name, description)
            self.events.append(event)
            events.append(event)
        return events

    def resolve(self, player_actions: Optional[Dict[str, Tuple[str, Optional[str], Optional[int]]]] = None) -> BattleResult:
        """Resolve the battle until one side is defeated."""

        result = BattleResult(events=list(self.events))
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

    def build_result(self) -> BattleResult:
        result = BattleResult(events=list(self.events))
        if not any(enemy.is_alive() for enemy in self.enemies):
            for enemy in self.enemies:
                result.xp_gained += enemy.exp_worth
                result.gold_gained += enemy.gp_worth
        return result


@dataclass
class NodeEvent:
    kind: str
    payload: Optional[str] = None
    details: List[str] = field(default_factory=list)
    game_over: bool = False


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
    # Helpers
    # ------------------------------------------------------------------
    def in_battle(self) -> bool:
        return self.battle is not None

    def _format_event(self, event: BattleEvent) -> str:
        return f"{event.source} -> {event.target}: {event.description}"

    def _format_enemy_status(self, index: int, enemy: Enemy) -> str:
        status = "defeated" if not enemy.is_alive() else f"{enemy.hp}/{enemy.max_hp} HP"
        return f"{index}. {enemy.name} - {status}"

    def list_player_actions(self) -> List[Tuple[str, Optional[str]]]:
        if not self.player_party:
            return []
        player = next((member for member in self.player_party if member.is_alive()), None)
        if not player:
            return []
        actions: List[Tuple[str, Optional[str]]] = [("attack", None)]
        if isinstance(player, Mage):
            actions.extend(("spell", spell.name) for spell in player.available_spells())
        if hasattr(player, "available_abilities"):
            abilities = player.available_abilities()  # type: ignore[attr-defined]
            actions.extend(("ability", ability) for ability in abilities)
        return actions

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
        if self.battle:
            raise RuntimeError("Cannot move while a battle is active")
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
                battle_event = self._start_battle()
                events.append(battle_event)
                return events
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
        for player in self.player_party:
            if isinstance(player, Ranger):
                player.reset_focus()
        self.battle = Battle(self.player_party, enemies, rng=self.rng)
        summary = "Encountered " + ", ".join(enemy.name for enemy in enemies)
        details = [self._format_enemy_status(idx, enemy) for idx, enemy in enumerate(enemies, 1)]
        self.event_log.append(summary)
        return NodeEvent("battle", payload=summary, details=details)

    def perform_player_action(
        self,
        action: str,
        *,
        target_index: int = 0,
        name: Optional[str] = None,
    ) -> NodeEvent:
        if not self.battle:
            raise RuntimeError("No active battle")
        player = next((member for member in self.player_party if member.is_alive()), None)
        if not player:
            raise RuntimeError("All party members are down")
        battle = self.battle
        events: List[BattleEvent] = []

        action = action.lower()

        if action == "potion":
            if not name:
                raise ValueError("Potion name required")
            player.use_potion(name)
            description = f"uses {name} ({player.hp}/{player.max_hp} HP)"
            if isinstance(player, Mage):
                description += f" ({player.mp}/{player.max_mp} MP)"
            event = BattleEvent(player.name, player.name, description)
            battle.events.append(event)
            events.append(event)
        else:
            living_enemies = battle._living_enemies()
            if not living_enemies:
                return self._finalize_battle(events)
            target_index = max(0, min(target_index, len(living_enemies) - 1))
            if action == "spell" and not isinstance(player, Mage):
                raise ValueError("This character cannot cast spells")
            if action == "ability" and not hasattr(player, "use_ability"):
                raise ValueError("No abilities available")
            normalized_name = name.lower() if name else None
            descriptor = (action, normalized_name, target_index)
            event = battle.player_action(player, descriptor)
            if event:
                events.append(event)

        if battle.is_over():
            return self._finalize_battle(events)

        enemy_events = battle.enemy_turn()
        events.extend(enemy_events)
        if battle.is_over():
            return self._finalize_battle(events)

        details = [self._format_event(evt) for evt in events]
        if details:
            self.event_log.extend(details)
        return NodeEvent("battle", payload="Battle continues", details=details)

    def _finalize_battle(self, round_events: List[BattleEvent]) -> NodeEvent:
        if not self.battle:
            raise RuntimeError("No battle to finalize")
        battle = self.battle
        event_lines = [self._format_event(event) for event in round_events]
        if event_lines:
            self.event_log.extend(event_lines)
        result = battle.build_result()
        players_alive = any(player.is_alive() for player in self.player_party)
        enemies_alive = any(enemy.is_alive() for enemy in battle.enemies)
        victory = players_alive and not enemies_alive
        details = self._record_battle_outcome(result, victory=victory, recent_events=event_lines)
        summary = "Party was defeated" if not players_alive else f"Defeated {len(battle.enemies)} enemies"
        self.event_log.append(summary)
        self.battle = None
        return NodeEvent("battle", payload=summary, details=details, game_over=not players_alive)

    def _record_battle_outcome(
        self,
        result: BattleResult,
        *,
        victory: bool,
        recent_events: Optional[List[str]] = None,
    ) -> List[str]:
        details: List[str] = []
        if recent_events:
            details.extend(recent_events)
        elif result.events:
            event_lines = [self._format_event(event) for event in result.events]
            details.extend(event_lines)
            if event_lines:
                self.event_log.extend(event_lines)
        if not victory:
            return details

        if result.xp_gained:
            for player in self.player_party:
                player.gain_exp(result.xp_gained)
            details.append(f"Gained {result.xp_gained} XP")
            self.event_log.append(f"Gained {result.xp_gained} XP")
        if result.gold_gained:
            for player in self.player_party:
                player.add_gold(result.gold_gained)
            details.append(f"Collected {result.gold_gained} gold")
            self.event_log.append(f"Collected {result.gold_gained} gold")
        if self.player_party:
            loot_item = random_loot_drop(max(player.level for player in self.player_party))
            self.player_party[0].add_item(loot_item)
            loot_message = f"Looted {loot_item.name}"
            details.append(loot_message)
            self.event_log.append(loot_message)
        return details

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
        return Mage(player_name, 1, 90, 45, 12)
    if player_class == "ranger":
        return Ranger(player_name, 1, 110, 14)
    if player_class == "cleric":
        return Cleric(player_name, 1, 95, 50, 11)
    return Player(player_name, 1, 120, 15)

