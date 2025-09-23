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
import uuid
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

from classes.classes import Cleric, Enemy, Mage, Player, Ranger, Item
from game_logic.map_generation import MapBlueprint, blueprint_from_graph, generate_blueprint
from game_logic.persistence import PersistenceManager, default_db_path
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
    _turn_queue: List[Tuple[float, Union[Player, Enemy]]] = field(default_factory=list)
    _turn_index: int = 0

    def is_over(self) -> bool:
        return not any(p.is_alive() for p in self.players) or not any(e.is_alive() for e in self.enemies)

    def _living_players(self) -> List[Player]:
        return [player for player in self.players if player.is_alive()]

    def _living_enemies(self) -> List[Enemy]:
        return [enemy for enemy in self.enemies if enemy.is_alive()]

    def _collect_combatants(self) -> List[Union[Player, Enemy]]:
        return self._living_players() + self._living_enemies()

    def _roll_initiative(self) -> None:
        combatants = self._collect_combatants()
        self._turn_queue = sorted(
            [
                (
                    self.rng.random() + getattr(combatant, "level", 1) * 0.01,
                    combatant,
                )
                for combatant in combatants
            ],
            key=lambda entry: entry[0],
            reverse=True,
        )
        self._turn_index = 0

    def current_actor(self) -> Optional[Union[Player, Enemy]]:
        if self.is_over():
            return None
        if not self._turn_queue or self._turn_index >= len(self._turn_queue):
            self._roll_initiative()
        while self._turn_queue:
            _, combatant = self._turn_queue[self._turn_index]
            if combatant.is_alive():
                return combatant
            self._turn_index += 1
            if self._turn_index >= len(self._turn_queue):
                self._roll_initiative()
        return None

    def advance_turn(self) -> None:
        if not self._turn_queue:
            self._roll_initiative()
            return
        self._turn_index += 1
        if self._turn_index >= len(self._turn_queue):
            self._roll_initiative()

    def ensure_initiative(self) -> None:
        if not self._turn_queue:
            self._roll_initiative()

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
            spell = player.spells.get(name)
            if spell and getattr(spell, "healing", 0) > 0:
                healed = player.cast_spell(name, player)
                description = (
                    f"casts {name} restoring {healed} HP "
                    f"({player.hp}/{player.max_hp} HP)"
                )
                target = player
            else:
                if not living_enemies:
                    return
                target_index = max(0, min(target_index, len(living_enemies) - 1))
                target = living_enemies[target_index]
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

    def enemy_action(self, enemy: Enemy) -> Optional[BattleEvent]:
        if not enemy.is_alive():
            return None
        players = self._living_players()
        if not players:
            return None
        target = enemy.decide_target(players)
        damage = enemy.attack_damage()
        target.take_damage(damage)
        description = f"attacks for {damage} damage ({target.hp}/{target.max_hp} HP left)"
        event = BattleEvent(enemy.name, target.name, description)
        self.events.append(event)
        return event

    def resolve(self, player_actions: Optional[Dict[str, Tuple[str, Optional[str], Optional[int]]]] = None) -> BattleResult:
        """Resolve the battle until one side is defeated."""

        result = BattleResult(events=list(self.events))
        self.ensure_initiative()
        while not self.is_over():
            actor = self.current_actor()
            if actor is None:
                break
            if isinstance(actor, Player):
                action = None
                if player_actions and actor.name in player_actions:
                    action = player_actions[actor.name]
                event = self.player_action(actor, action)
                if event:
                    result.events.append(event)
            else:
                event = self.enemy_action(actor)
                if event:
                    result.events.append(event)
            self.advance_turn()
        if not any(enemy.is_alive() for enemy in self.enemies):
            for enemy in self.enemies:
                result.xp_gained += enemy.exp_worth
                result.gold_gained += enemy.gp_worth
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

    def __init__(
        self,
        rng: Optional[random.Random] = None,
        *,
        persistence: Optional[PersistenceManager] = None,
        db_path: Optional[str] = None,
    ) -> None:
        self.rng = rng or random.Random()
        self.persistence = persistence or PersistenceManager(db_path or default_db_path())
        base_maps: Dict[str, Graph] = {
            "beginner": create_beginner_map(),
            "intermediate": create_intermediate_map(),
        }
        self.maps: Dict[str, Graph] = dict(base_maps)
        self.map_blueprints: Dict[str, MapBlueprint] = {
            key: blueprint_from_graph(key, graph) for key, graph in base_maps.items()
        }
        for blueprint in self.persistence.iter_maps():
            self.maps[blueprint.key] = blueprint.to_graph()
            self.map_blueprints[blueprint.key] = blueprint
        self.current_map_key = "beginner"
        self.active_map = self.maps[self.current_map_key]
        self.current_node = "A0"
        self.hero: Optional[Player] = None
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
        if not self.battle:
            return []
        actor = self.battle.current_actor()
        if not isinstance(actor, Player):
            return []
        player = actor
        actions: List[Tuple[str, Optional[str]]] = [("attack", None)]
        if isinstance(player, Mage):
            actions.extend(("spell", spell.name) for spell in player.available_spells())
        if hasattr(player, "available_abilities"):
            abilities = player.available_abilities()  # type: ignore[attr-defined]
            actions.extend(("ability", ability) for ability in abilities)
        return actions

    def _refresh_party(self) -> None:
        if not self.hero:
            self.player_party = []
            return
        party: List[Player] = [self.hero]
        for follower in self.hero.following:
            if follower not in party:
                party.append(follower)
        self.player_party = party

    def _party_level(self) -> int:
        if not self.player_party:
            return 1
        return max(member.level for member in self.player_party)

    # ------------------------------------------------------------------
    # Game setup
    # ------------------------------------------------------------------
    def start_new_game(self, player: Player) -> None:
        self.hero = player
        self._refresh_party()
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
        ally_blueprint = node_data.get("ally")
        if ally_blueprint and self.hero:
            ally = self._spawn_ally(ally_blueprint)
            events.append(self.recruit_ally(ally))
            node_data.pop("ally", None)
        if transition := node_data.get("transition"):
            transition_event = self.transition_map(str(transition))
            if transition == "auto" and transition_event.details:
                node_data["transition"] = transition_event.details[0]
            events.append(transition_event)
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
        self._refresh_party()
        enemies = self._generate_enemies()
        for player in self.player_party:
            if isinstance(player, Ranger):
                player.reset_focus()
        self.battle = Battle(self.player_party, enemies, rng=self.rng)
        self.battle.ensure_initiative()
        summary = "Encountered " + ", ".join(enemy.name for enemy in enemies)
        details = [self._format_enemy_status(idx, enemy) for idx, enemy in enumerate(enemies, 1)]
        opener = self._process_auto_turns()
        if opener:
            opener_lines = [self._format_event(evt) for evt in opener]
            details.extend(opener_lines)
            self.event_log.extend(opener_lines)
        next_actor = self.battle.current_actor() if self.battle else None
        if isinstance(next_actor, Player):
            details.append(f"Awaiting command for {next_actor.name}")
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
        battle = self.battle
        actor = battle.current_actor()
        if not isinstance(actor, Player):
            raise RuntimeError("It is not a player's turn")
        player = actor
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

        battle.advance_turn()
        enemy_events = self._process_auto_turns()
        events.extend(enemy_events)
        if battle.is_over():
            return self._finalize_battle(events)

        details = [self._format_event(evt) for evt in events]
        if details:
            self.event_log.extend(details)
        next_actor = battle.current_actor()
        if isinstance(next_actor, Player):
            details.append(f"Awaiting command for {next_actor.name}")
        return NodeEvent("battle", payload="Battle continues", details=details)

    def _process_auto_turns(self) -> List[BattleEvent]:
        if not self.battle:
            return []
        events: List[BattleEvent] = []
        self.battle.ensure_initiative()
        while not self.battle.is_over():
            actor = self.battle.current_actor()
            if isinstance(actor, Enemy):
                event = self.battle.enemy_action(actor)
                if event:
                    events.append(event)
                self.battle.advance_turn()
            else:
                break
        return events

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
        if key == "auto":
            key = self._create_generated_map()
        if key not in self.maps:
            blueprint = self.persistence.load_map(key)
            if not blueprint:
                raise KeyError(f"Unknown map '{key}'")
            self.maps[key] = blueprint.to_graph()
            self.map_blueprints[key] = blueprint
        self.current_map_key = key
        self.active_map = self.maps[key]
        self.current_node = next(iter(self.active_map.nodes))
        blueprint = self.map_blueprints.get(key) or blueprint_from_graph(key, self.active_map)
        self.map_blueprints[key] = blueprint
        self.event_log.append(f"Traveled to {blueprint.name} map")
        return NodeEvent("transition", payload=blueprint.name, details=[key])

    def _create_generated_map(self, *, size: Optional[int] = None) -> str:
        map_size = size or self.rng.randint(9, 15)
        key = f"frontier_{uuid.uuid4().hex[:6]}"
        blueprint = generate_blueprint(
            key,
            size=map_size,
            base_level=self._party_level(),
            rng=self.rng,
        )
        self.maps[key] = blueprint.to_graph()
        self.map_blueprints[key] = blueprint
        self.persistence.save_map(blueprint)
        return key

    def generate_new_map(self, *, size: Optional[int] = None) -> NodeEvent:
        key = self._create_generated_map(size=size)
        blueprint = self.map_blueprints[key]
        message = f"Discovered {blueprint.name} ({key})"
        self.event_log.append(message)
        return NodeEvent("map", payload=message)

    def _spawn_ally(self, blueprint: Dict[str, object]) -> Player:
        class_key = str(blueprint.get("class", "player"))
        name = str(blueprint.get("name", "Ally"))
        desired_level = max(1, self._party_level() + int(blueprint.get("level_bonus", 0)))
        ally = startGame(name, class_key)
        while ally.level < desired_level:
            threshold = ally.exp_to_level[ally.level] - ally.exp + 1
            ally.gain_exp(threshold)
        ally.hp = ally.max_hp
        if isinstance(ally, Mage):
            ally.mp = ally.max_mp
        setattr(ally, "personality", blueprint.get("personality", "steady"))
        return ally

    def recruit_ally(self, ally: Player) -> NodeEvent:
        if not self.hero:
            raise RuntimeError("No hero available to recruit allies")
        self.hero.add_follower(ally)
        self._refresh_party()
        message = f"{ally.name} joins the party!"
        detail = f"Class: {ally.__class__.__name__}"
        personality = getattr(ally, "personality", None)
        details = [detail]
        if personality:
            details.append(f"Personality: {personality}")
        self.event_log.append(message)
        return NodeEvent("ally", payload=message, details=details)

    def save_game(self, slot: str) -> None:
        if not self.hero:
            raise RuntimeError("No active game to save")
        state = {
            "hero": self.hero.to_dict(),
            "map_key": self.current_map_key,
            "current_node": self.current_node,
            "event_log": self.event_log[-50:],
            "shop": self.shop.to_dict(),
        }
        self.persistence.save_game(slot, state, map_key=self.current_map_key)

    def list_saves(self) -> List[str]:
        return self.persistence.list_saves()

    def load_game(self, slot: str) -> None:
        state = self.persistence.load_game(slot)
        if not state:
            raise KeyError(f"Save slot '{slot}' not found")
        map_key = str(state.get("map_key", "beginner"))
        if map_key not in self.maps:
            blueprint = self.persistence.load_map(map_key)
            if not blueprint:
                raise KeyError(f"Map '{map_key}' missing for save '{slot}'")
            self.maps[map_key] = blueprint.to_graph()
            self.map_blueprints[map_key] = blueprint
        self.current_map_key = map_key
        self.active_map = self.maps[map_key]
        self.current_node = str(state.get("current_node", next(iter(self.active_map.nodes))))
        hero_data = state.get("hero")
        if not hero_data:
            raise ValueError("Save slot missing hero data")
        hero = Player.from_dict(hero_data)  # type: ignore[arg-type]
        self.hero = hero
        self._refresh_party()
        shop_data = state.get("shop")
        if isinstance(shop_data, dict):
            self.shop = Shop.from_dict(shop_data)
        self.event_log = list(state.get("event_log", []))
        self.battle = None


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

