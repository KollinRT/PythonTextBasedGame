"""Entry point for the adventure game.

Running ``python -m main`` launches the traditional text interface.  The
``--mode pygame`` switch starts the graphical interface that uses pygame.
"""

from __future__ import annotations

import argparse

from typing import Optional

from classes.classes import Mage, Player
from game_logic.core import GameEngine, NodeEvent, startGame


def _select_player_class() -> str:
    while True:
        choice = input("Choose a class (Player/Mage/Ranger/Cleric): ").strip().lower()
        if choice in {"player", "mage", "ranger", "cleric"}:
            return choice
        print("Invalid class. Try again.")


def _print_status(engine: GameEngine) -> None:
    if not engine.player_party:
        return
    player = engine.player_party[0]
    map_info = engine.map_blueprints.get(engine.current_map_key)
    map_label = map_info.name if map_info else engine.current_map_key
    print("-" * 40)
    print(f"Location: {engine.current_node} on {map_label} map")
    print("Party:")
    for member in engine.player_party:
        resources = f"HP {member.hp}/{member.max_hp}"
        if isinstance(member, Mage):
            resources += f"  MP {member.mp}/{member.max_mp}"
        if hasattr(member, "focus"):
            resources += f"  Focus {member.focus}/{member.max_focus}"
        tag = "(leader)" if member is player else ""
        print(f"  {member.name} {tag} - {resources}")
    print(f"Level: {player.level}  EXP: {player.exp}  Gold: {player.gp}")
    print("Inventory:")
    for item in player.sort_inventory():
        print(f"  {item.name} (lvl {item.level}) x{item.quantity}")
    print("Potions:")
    for potion in player.potions.values():
        print(f"  {potion.name} x{potion.quantity}")
    print("-" * 40)


def _prompt_command(engine: GameEngine) -> bool:
    if engine.in_battle():
        return _prompt_battle_command(engine)
    neighbors = engine.neighbors()
    print(f"You can travel to: {', '.join(neighbors)}")
    command = input(
        "Enter command (move <node>/potion <name>/save <slot>/load <slot>/generate [size]/quit): "
    ).strip()
    if command == "quit":
        return False
    if command.lower() == "saves":
        slots = engine.list_saves()
        if slots:
            print("Available saves:")
            for slot in slots:
                print(f"  {slot}")
        else:
            print("No saves yet.")
        return True
    if command.lower().startswith("save"):
        _, _, slot = command.partition(" ")
        slot = slot.strip() or "slot1"
        engine.save_game(slot)
        print(f"Game saved to '{slot}'.")
        return True
    if command.lower().startswith("load"):
        _, _, slot = command.partition(" ")
        slot = slot.strip()
        if not slot:
            print("Specify a save slot to load.")
            return True
        try:
            engine.load_game(slot)
            print(f"Loaded save '{slot}'.")
        except (KeyError, ValueError) as exc:
            print(exc)
        return True
    if command.lower().startswith("generate"):
        parts = command.split()
        size = None
        if len(parts) > 1 and parts[1].isdigit():
            size = int(parts[1])
        event = engine.generate_new_map(size=size)
        if event.payload:
            print(event.payload)
        return True
    if command.startswith("move"):
        _, _, destination = command.partition(" ")
        if destination:
            try:
                events = engine.move_to(destination.upper())
            except ValueError as exc:  # pragma: no cover - exercised interactively
                print(exc)
                return True
            for event in events:
                if event.kind == "battle":
                    if event.payload:
                        print(event.payload)
                    for line in event.details:
                        print(f"  {line}")
                    if event.game_over:
                        return False
                elif event.kind == "shop":
                    _handle_shop(engine)
                elif event.kind == "fishing":
                    print(event.payload)
                elif event.kind == "transition":
                    key = event.details[0] if event.details else engine.current_map_key
                    map_info = engine.map_blueprints.get(key)
                    label = event.payload or (map_info.name if map_info else key)
                    print(f"Traveled to {label} map")
                elif event.payload:
                    print(event.payload)
            return True
    if command.startswith("potion"):
        _, _, potion_name = command.partition(" ")
        try:
            engine.player_party[0].use_potion(potion_name.title())
            print(f"Used {potion_name}")
        except (KeyError, ValueError) as exc:  # pragma: no cover - interactive flow
            print(exc)
        return True
    print("Unknown command")
    return True


def _print_battle_state(engine: GameEngine) -> None:
    battle = engine.battle
    if not battle:
        return
    actor = battle.current_actor()
    if actor:
        print(f"Current turn: {actor.name}")
    print("Enemies:")
    for idx, enemy in enumerate(battle.enemies, 1):
        status = "DEFEATED" if not enemy.is_alive() else f"{enemy.hp}/{enemy.max_hp} HP"
        print(f"  {idx}. {enemy.name} - {status}")
    actions = engine.list_player_actions()
    if actions:
        print("Available actions:")
        for idx, (kind, name) in enumerate(actions, 1):
            label = kind if not name else f"{kind} {name}"
            print(f"  {idx}. {label}")
    print(
        "Use 'attack', 'spell <name>', 'ability <name>' or select an action number. "
        "Add a number to target enemies, or 'ally <name/#>' to heal a party member."
    )
    print("Use 'potion <name>' to consume a potion.")
    if any(getattr(member, "role", "") == "pet" for member in engine.player_party):
        print("Prefix commands with 'pet' to direct your companion when it is their turn.")


def _handle_battle_event(engine: GameEngine, event: NodeEvent) -> bool:
    if event.payload:
        print(event.payload)
    for line in event.details:
        print(f"  {line}")
    if event.game_over:
        return False
    return True


def _prompt_battle_command(engine: GameEngine) -> bool:
    battle = engine.battle
    if not battle:
        return True
    _print_battle_state(engine)
    command = input("Enter battle command: ").strip()
    if not command:
        return True
    if command.isdigit():
        index = int(command) - 1
        actions = engine.list_player_actions()
        if 0 <= index < len(actions):
            kind, name = actions[index]
            event = engine.perform_player_action(kind, name=name)
            return _handle_battle_event(engine, event)
        print("Invalid selection")
        return True

    parts = command.split()
    action = parts[0].lower()
    player = engine.player_party[0]

    actor_name_override: Optional[str] = None
    if parts:
        alias = parts[0].lower()
        if alias in {"pet", "companion"}:
            pet_member = next(
                (member for member in engine.player_party if getattr(member, "role", "") == "pet" and member.is_alive()),
                None,
            )
            if not pet_member:
                print("No pet is available to command.")
                return True
            actor_name_override = pet_member.name
            parts = parts[1:]
            if not parts:
                print("Specify an action for your pet.")
                return True
            action = parts[0].lower()

    acting_player: Optional[Player] = None
    if actor_name_override:
        acting_player = next(
            (member for member in engine.player_party if member.name == actor_name_override),
            None,
        )
    else:
        current_actor = battle.current_actor()
        if isinstance(current_actor, Player):
            acting_player = current_actor

    if action == "potion":
        if len(parts) < 2:
            print("Specify a potion name")
            return True
        requested = " ".join(parts[1:])
        owner = acting_player or player
        potions = {name.lower(): name for name in owner.potions}
        potion_name = potions.get(requested.lower(), requested)
        try:
            event = engine.perform_player_action("potion", name=potion_name, actor_name=actor_name_override)
        except (KeyError, ValueError) as exc:
            print(exc)
            return True
        return _handle_battle_event(engine, event)

    target_index = 0
    target_kind = "enemy"
    target_name: Optional[str] = None

    name = None
    if action == "spell":
        if len(parts) < 2:
            print("Specify a spell name")
            return True
        tokens = parts[1:]
        if len(tokens) >= 2 and tokens[-2].lower() in {"ally", "friend"}:
            target_kind = "ally"
            spec = tokens[-1]
            tokens = tokens[:-2]
            if spec.isdigit():
                target_index = max(0, int(spec) - 1)
            else:
                target_name = spec
        elif tokens and tokens[-1].lower() in {"self", "me", "caster"}:
            target_kind = "ally"
            target_name = acting_player.name if acting_player else None
            tokens = tokens[:-1]
        elif tokens and tokens[-1].isdigit():
            target_index = max(0, int(tokens[-1]) - 1)
            tokens = tokens[:-1]
        name = " ".join(tokens)
    else:
        if len(parts) > 1 and parts[-1].isdigit():
            target_index = max(0, int(parts[-1]) - 1)
            parts = parts[:-1]
        if action == "ability":
            if len(parts) < 2:
                print("Specify an ability name")
                return True
            name = " ".join(parts[1:])
        elif action != "attack":
            print("Unknown battle command")
            return True

    try:
        event = engine.perform_player_action(
            action,
            target_index=target_index,
            name=name,
            actor_name=actor_name_override,
            target_kind=target_kind,
            target_name=target_name,
        )
    except (ValueError, KeyError) as exc:
        print(exc)
        return True
    return _handle_battle_event(engine, event)


def _handle_shop(engine: GameEngine) -> None:
    player = engine.player_party[0]
    print("Welcome to the shop! Available items:")
    for item in engine.shop.list_items():
        print(f"  {item.name} - {item.value}gp (qty {item.quantity})")
    selection = input("Enter the item name to purchase or leave blank to exit: ").strip()
    if not selection:
        return
    try:
        item = engine.purchase_item(selection)
        print(f"Purchased {item.name}")
    except (KeyError, ValueError) as exc:  # pragma: no cover - interactive only
        print(exc)


def run_text_mode() -> None:
    engine = GameEngine()
    player: Optional[Player] = None
    existing = engine.list_saves()
    if existing:
        print("Existing saves:")
        for slot in existing:
            print(f"  {slot}")
        choice = input("Enter a slot to load or leave blank for a new game: ").strip()
        if choice:
            try:
                engine.load_game(choice)
                player = engine.hero
                print(f"Resumed adventure from '{choice}'.")
            except (KeyError, ValueError) as exc:
                print(exc)
    if not player:
        name = input("What is your character's name?: ").strip() or "Hero"
        class_choice = _select_player_class()
        player = startGame(name, class_choice)
        engine.start_new_game(player)
    print("Welcome to the adventure!")
    running = True
    while running and engine.hero and engine.hero.is_alive():
        _print_status(engine)
        running = _prompt_command(engine)
    if engine.hero and not engine.hero.is_alive():
        print("Your journey ends here...")


def main() -> None:
    parser = argparse.ArgumentParser(description="Python Text Adventure")
    parser.add_argument("--mode", choices=["text", "pygame", "web"], default="text")
    parser.add_argument("--host", default="0.0.0.0", help="Host for --mode web")
    parser.add_argument("--port", type=int, default=8000, help="Port for --mode web")
    args = parser.parse_args()
    if args.mode == "pygame":
        from ui.pygame_ui import run_pygame_ui

        run_pygame_ui()
    elif args.mode == "web":
        from api.server import run as run_web_server

        run_web_server(args.host, args.port)
    else:
        run_text_mode()


if __name__ == "__main__":
    main()

