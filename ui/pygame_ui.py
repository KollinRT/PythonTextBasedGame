from __future__ import annotations

import pygame

from typing import Iterable, List, Optional, Tuple

from classes.classes import Mage
from game_logic.core import GameEngine, startGame


WINDOW_SIZE = (900, 600)
BACKGROUND = (30, 30, 40)
TEXT_COLOR = (230, 230, 230)


def _render_lines(screen: pygame.Surface, font: pygame.font.Font, lines: list[str], start_y: int) -> None:
    y = start_y
    for line in lines:
        text = font.render(line, True, TEXT_COLOR)
        screen.blit(text, (20, y))
        y += font.get_linesize()

def _apply_node_events(events: Iterable, log: list[str]) -> bool:
    """Add node events to the on-screen log and return True if the party died."""

    game_over = False
    for node_event in events:
        if node_event.kind == "battle":
            if node_event.payload:
                log.append(node_event.payload)
            log.extend(node_event.details)
            if node_event.game_over:
                game_over = True
                log.append("Your party has fallen. Press Esc to exit.")
        elif node_event.kind == "shop":
            log.append("Visited a shop (trade in text mode)")
        elif node_event.kind == "fishing":
            log.append(node_event.payload or "Fishing result")
        elif node_event.kind == "transition":
            log.append(f"Traveled to {node_event.payload}")
        elif node_event.kind == "ally":
            log.append(node_event.payload or "An ally joined the party")
            log.extend(node_event.details)
        elif node_event.kind == "map":
            log.append(node_event.payload or "Discovered a new map")
        elif node_event.payload:
            log.append(node_event.payload)
    return game_over


def _build_slot_options(engine: GameEngine, *, include_new: bool) -> List[str]:
    slots = engine.list_saves()
    if include_new:
        seen = set(slots)
        next_index = 1
        while len(slots) < 9:
            candidate = f"slot{next_index}"
            if candidate not in seen:
                slots.append(candidate)
                seen.add(candidate)
            next_index += 1
    return slots[:9]


def run_pygame_ui() -> None:
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Python Text Adventure")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28)

    player = startGame("Hero", "player")
    engine = GameEngine()
    engine.start_new_game(player)
    log: list[str] = list(engine.event_log)
    player = engine.player_party[0] if engine.player_party else player

    running = True
    game_over = False
    selected_enemy = 0
    menu_mode: Optional[str] = None
    menu_slots: List[str] = []

    def living_enemy_indices() -> List[int]:
        if not engine.battle:
            return []
        return [idx for idx, enemy in enumerate(engine.battle.enemies) if enemy.is_alive()]

    def refresh_player() -> None:
        nonlocal player
        if engine.player_party:
            player = engine.player_party[0]

    while running:
        refresh_player()
        neighbors = engine.neighbors() if not engine.in_battle() else []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if menu_mode:
                    if event.key == pygame.K_ESCAPE:
                        log.append("Cancelled save/load selection.")
                        menu_mode = None
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        index = event.key - pygame.K_1
                        if index < len(menu_slots):
                            slot = menu_slots[index]
                            if menu_mode == "save":
                                try:
                                    engine.save_game(slot)
                                    log.append(f"Saved game to '{slot}'.")
                                except RuntimeError as exc:
                                    log.append(str(exc))
                            else:
                                try:
                                    engine.load_game(slot)
                                    new_log = list(engine.event_log[-12:])
                                    if new_log:
                                        log = new_log
                                    game_over = False
                                    selected_enemy = 0
                                    log.append(f"Loaded save '{slot}'.")
                                except (KeyError, ValueError) as exc:
                                    log.append(str(exc))
                            menu_mode = None
                        else:
                            log.append("No slot bound to that key.")
                    continue
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F5:
                    if game_over:
                        log.append("Cannot save after a defeat.")
                    else:
                        menu_slots = _build_slot_options(engine, include_new=True)
                        if not menu_slots:
                            log.append("No slots available to save.")
                        else:
                            menu_mode = "save"
                            log.append("Choose a slot (1-9) to save your progress.")
                            for idx, slot in enumerate(menu_slots, 1):
                                log.append(f"  {idx}. {slot}")
                elif event.key == pygame.K_F9:
                    menu_slots = _build_slot_options(engine, include_new=False)
                    if not menu_slots:
                        log.append("No saved games found.")
                    else:
                        menu_mode = "load"
                        log.append("Choose a slot (1-9) to load.")
                        for idx, slot in enumerate(menu_slots, 1):
                            log.append(f"  {idx}. {slot}")
                elif game_over:
                    continue
                elif event.key == pygame.K_g:
                    new_map = engine.generate_new_map()
                    log.append(new_map.payload or "Generated new map")
                elif engine.in_battle():
                    actions: List[Tuple[str, Optional[str]]] = engine.list_player_actions()
                    living = living_enemy_indices()
                    if event.key in {pygame.K_a, pygame.K_LEFT}:
                        if living:
                            if selected_enemy not in living:
                                selected_enemy = living[0]
                            else:
                                pos = living.index(selected_enemy)
                                selected_enemy = living[(pos - 1) % len(living)]
                    elif event.key in {pygame.K_d, pygame.K_RIGHT}:
                        if living:
                            if selected_enemy not in living:
                                selected_enemy = living[0]
                            else:
                                pos = living.index(selected_enemy)
                                selected_enemy = living[(pos + 1) % len(living)]
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        index = event.key - pygame.K_1
                        if index < len(actions):
                            kind, name = actions[index]
                            try:
                                battle_event = engine.perform_player_action(kind, target_index=selected_enemy, name=name)
                            except (ValueError, KeyError) as exc:
                                log.append(str(exc))
                                continue
                            game_over = _apply_node_events([battle_event], log)
                            if not engine.in_battle():
                                selected_enemy = 0
                        else:
                            log.append("No action bound to that key")
                    elif event.key == pygame.K_h:
                        potions = list(engine.player_party[0].potions.keys())
                        if potions:
                            try:
                                battle_event = engine.perform_player_action("potion", name=potions[0])
                            except (ValueError, KeyError) as exc:
                                log.append(str(exc))
                                continue
                            game_over = _apply_node_events([battle_event], log)
                            if not engine.in_battle():
                                selected_enemy = 0
                        else:
                            log.append("No potions available")
                else:
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        index = event.key - pygame.K_1
                        if index < len(neighbors):
                            events = engine.move_to(neighbors[index])
                            game_over = _apply_node_events(events, log)
                            if engine.in_battle():
                                selected_enemy = 0
                        else:
                            log.append("No path bound to that key")
                    elif event.key in {pygame.K_w, pygame.K_UP}:
                        if neighbors:
                            events = engine.move_to(neighbors[0])
                            game_over = _apply_node_events(events, log)
                            if engine.in_battle():
                                selected_enemy = 0
                    elif event.key in {pygame.K_d, pygame.K_RIGHT}:
                        if len(neighbors) >= 2:
                            events = engine.move_to(neighbors[1])
                            game_over = _apply_node_events(events, log)
                            if engine.in_battle():
                                selected_enemy = 0
                    elif event.key in {pygame.K_s, pygame.K_DOWN}:
                        if len(neighbors) >= 3:
                            events = engine.move_to(neighbors[2])
                            game_over = _apply_node_events(events, log)
                            if engine.in_battle():
                                selected_enemy = 0
                    elif event.key in {pygame.K_a, pygame.K_LEFT}:
                        if len(neighbors) >= 4:
                            events = engine.move_to(neighbors[3])
                            game_over = _apply_node_events(events, log)
                            if engine.in_battle():
                                selected_enemy = 0
                    elif event.key == pygame.K_h:
                        potions = list(engine.player_party[0].potions.keys())
                        if potions:
                            try:
                                engine.player_party[0].use_potion(potions[0])
                                log.append(f"Used {potions[0]}")
                            except ValueError:
                                log.append("Cannot use potion yet")
                        else:
                            log.append("No potions available")
                    elif event.key == pygame.K_m and isinstance(player, Mage):
                        available = player.available_spells()
                        if available:
                            log.append(
                                "Spells ready: "
                                + ", ".join(spell.name for spell in available)
                                + " (use number keys during battle)"
                            )

        log = log[-12:]
        screen.fill(BACKGROUND)

        map_info = engine.map_blueprints.get(engine.current_map_key)
        map_label = map_info.name if map_info else engine.current_map_key
        status_lines = [
            f"Location: {engine.current_node}",
            f"Map: {map_label} ({engine.current_map_key})",
            f"HP: {player.hp}/{player.max_hp}",
            f"Level: {player.level}  EXP: {player.exp}  Gold: {player.gp}",
        ]
        if isinstance(player, Mage):
            status_lines.insert(2, f"MP: {player.mp}/{player.max_mp}")

        if engine.in_battle() and engine.battle:
            actor = engine.battle.current_actor()
            status_lines.append("")
            if actor:
                status_lines.append(f"Current turn: {actor.name}")
            status_lines.append("Party:")
            for member in engine.player_party:
                resources = f"HP {member.hp}/{member.max_hp}"
                if isinstance(member, Mage):
                    resources += f"  MP {member.mp}/{member.max_mp}"
                if hasattr(member, "focus"):
                    resources += f"  Focus {member.focus}/{member.max_focus}"
                marker = "->" if actor is member else "  "
                status_lines.append(f"{marker} {member.name} - {resources}")
            status_lines.append("")
            status_lines.append("Battle:")
            for idx, enemy in enumerate(engine.battle.enemies):
                status = "defeated" if not enemy.is_alive() else f"{enemy.hp}/{enemy.max_hp} HP"
                pointer = "->" if enemy.is_alive() and idx == selected_enemy else "  "
                status_lines.append(f"{pointer} {idx+1}. {enemy.name} - {status}")
            actions = engine.list_player_actions()
            if actions:
                status_lines.append("")
                status_lines.append("Actions:")
                for idx, (kind, name) in enumerate(actions, 1):
                    label = kind if not name else f"{kind} {name}"
                    status_lines.append(f"  {idx}. {label}")
            status_lines.extend(
                [
                    "",
                    "Battle controls:",
                    "  Arrow keys/A-D to select enemy",
                    "  1-9 to trigger actions",
                    "  H to drink the first potion",
                    "  F5 to open save slots",
                    "  F9 to load a save",
                    "  Esc to leave the adventure",
                ]
            )
        else:
            status_lines.append("Neighbors:")
            status_lines.extend([f"  {idx+1}. {node}" for idx, node in enumerate(neighbors)])
            status_lines.extend(
                [
                    "",
                    "Controls:",
                    "  1-9 or WASD/Arrow keys to travel",
                    "  H to drink the first potion",
                    "  F5 to open save slots",
                    "  F9 to load a save",
                    "  G to generate a new frontier",
                    "  Esc to leave the adventure",
                ]
            )

        _render_lines(screen, font, status_lines, 20)

        log_header = ["Event Log:"] + log
        _render_lines(screen, font, log_header, 300)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

