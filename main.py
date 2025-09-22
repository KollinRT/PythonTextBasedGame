"""Entry point for the adventure game.

Running ``python -m main`` launches the traditional text interface.  The
``--mode pygame`` switch starts the graphical interface that uses pygame.
"""

from __future__ import annotations

import argparse

from classes.classes import Mage, Player
from game_logic.core import GameEngine, NodeEvent, startGame


def _select_player_class() -> str:
    while True:
        choice = input("Choose a class (Player/Mage/Ranger/Cleric): ").strip().lower()
        if choice in {"player", "mage", "ranger", "cleric"}:
            return choice
        print("Invalid class. Try again.")


def _print_status(engine: GameEngine) -> None:
    player = engine.player_party[0]
    print("-" * 40)
    print(f"Location: {engine.current_node} on {engine.current_map_key} map")
    print(f"HP: {player.hp}/{player.max_hp}")
    if isinstance(player, Mage):
        print(f"MP: {player.mp}/{player.max_mp}")
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
    command = input("Enter command (move <node>/potion <name>/quit): ").strip().lower()
    if command == "quit":
        return False
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
                    print(f"Traveled to {event.payload} map")
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
    print("Use 'attack', 'spell <name>', 'ability <name>' or select an action number. Optional <target> selects an enemy.")
    print("Use 'potion <name>' to consume a potion.")


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

    if action == "potion":
        if len(parts) < 2:
            print("Specify a potion name")
            return True
        requested = " ".join(parts[1:])
        potions = {name.lower(): name for name in player.potions}
        potion_name = potions.get(requested.lower(), requested)
        try:
            event = engine.perform_player_action("potion", name=potion_name)
        except (KeyError, ValueError) as exc:
            print(exc)
            return True
        return _handle_battle_event(engine, event)

    target_index = 0
    if len(parts) > 1 and parts[-1].isdigit():
        target_index = max(0, int(parts[-1]) - 1)
        parts = parts[:-1]

    name = None
    if action == "spell":
        if len(parts) < 2:
            print("Specify a spell name")
            return True
        name = " ".join(parts[1:])
    elif action == "ability":
        if len(parts) < 2:
            print("Specify an ability name")
            return True
        name = " ".join(parts[1:])
    elif action != "attack":
        print("Unknown battle command")
        return True

    try:
        event = engine.perform_player_action(action, target_index=target_index, name=name)
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
    name = input("What is your character's name?: ").strip() or "Hero"
    class_choice = _select_player_class()
    player = startGame(name, class_choice)
    engine = GameEngine()
    engine.start_new_game(player)
    print("Welcome to the adventure!")
    running = True
    while running and player.is_alive():
        _print_status(engine)
        running = _prompt_command(engine)
    if not player.is_alive():
        print("Your journey ends here...")


def main() -> None:
    parser = argparse.ArgumentParser(description="Python Text Adventure")
    parser.add_argument("--mode", choices=["text", "pygame"], default="text")
    args = parser.parse_args()
    if args.mode == "pygame":
        from ui.pygame_ui import run_pygame_ui

        run_pygame_ui()
    else:
        run_text_mode()


if __name__ == "__main__":
    main()

