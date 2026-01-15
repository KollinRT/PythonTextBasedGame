from __future__ import annotations

import pygame

from typing import Iterable, List, Optional, Tuple

from classes.classes import Mage
from game_logic.core import GameEngine, startGame


WINDOW_SIZE = (900, 600)
BACKGROUND = (30, 30, 40)
TEXT_COLOR = (230, 230, 230)


def _render_lines(
    screen: pygame.Surface,
    font: pygame.font.Font,
    lines: list[str],
    start_y: int,
    max_y: int = 600,
    max_width: int = 860
) -> int:
    """Render lines of text with boundary checking to prevent overlap.
    
    Args:
        screen: Pygame surface to render on
        font: Font to use for rendering
        lines: List of text lines to render
        start_y: Y coordinate to start rendering
        max_y: Y coordinate to stop rendering (prevents overflow)
        max_width: Maximum width before truncating with "..."
    
    Returns:
        The Y coordinate where rendering stopped
    """
    y = start_y
    for line in lines:
        # Stop if we would render past the boundary
        if y + font.get_linesize() > max_y:
            break
        
        text = font.render(line, True, TEXT_COLOR)
        
        # Truncate long lines with ellipsis
        if text.get_width() > max_width:
            truncated = line
            while len(truncated) > 3 and font.size(truncated + "...")[0] > max_width:
                truncated = truncated[:-1]
            text = font.render(truncated + "...", True, TEXT_COLOR)
        
        screen.blit(text, (20, y))
        y += font.get_linesize()
    
    return y

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
    selected_ally = 0
    target_mode = "enemy"
    menu_mode: Optional[str] = None
    menu_slots: List[str] = []

    def living_enemy_indices() -> List[int]:
        if not engine.battle:
            return []
        return [idx for idx, enemy in enumerate(engine.battle.enemies) if enemy.is_alive()]

    def living_ally_indices() -> List[int]:
        if not engine.battle:
            return []
        return [idx for idx, member in enumerate(engine.battle.players) if member.is_alive()]

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
                        if target_mode == "ally":
                            allies = living_ally_indices()
                            if allies:
                                if selected_ally not in allies:
                                    selected_ally = allies[0]
                                else:
                                    pos = allies.index(selected_ally)
                                    selected_ally = allies[(pos - 1) % len(allies)]
                        elif living:
                            if selected_enemy not in living:
                                selected_enemy = living[0]
                            else:
                                pos = living.index(selected_enemy)
                                selected_enemy = living[(pos - 1) % len(living)]
                    elif event.key in {pygame.K_d, pygame.K_RIGHT}:
                        if target_mode == "ally":
                            allies = living_ally_indices()
                            if allies:
                                if selected_ally not in allies:
                                    selected_ally = allies[0]
                                else:
                                    pos = allies.index(selected_ally)
                                    selected_ally = allies[(pos + 1) % len(allies)]
                        elif living:
                            if selected_enemy not in living:
                                selected_enemy = living[0]
                            else:
                                pos = living.index(selected_enemy)
                                selected_enemy = living[(pos + 1) % len(living)]
                    elif event.key == pygame.K_TAB:
                        if target_mode == "enemy":
                            allies = living_ally_indices()
                            if allies:
                                target_mode = "ally"
                                selected_ally = allies[0]
                                log.append("Targeting allies for healing spells.")
                            else:
                                log.append("No living allies to target.")
                        else:
                            target_mode = "enemy"
                            log.append("Targeting enemies.")
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        index = event.key - pygame.K_1
                        if index < len(actions):
                            kind, name = actions[index]
                            try:
                                kwargs = {}
                                actor = engine.battle.current_actor() if engine.battle else None
                                if kind == "spell" and isinstance(actor, Mage) and name:
                                    spell = actor.spells.get(name)
                                    if spell and spell.healing > 0:
                                        if target_mode == "ally":
                                            allies = living_ally_indices()
                                            if allies:
                                                if selected_ally not in allies:
                                                    selected_ally = allies[0]
                                                target_choice = selected_ally
                                            else:
                                                target_choice = 0
                                            kwargs = {"target_kind": "ally", "target_index": target_choice}
                                        else:
                                            kwargs = {"target_kind": "ally", "target_index": engine.battle.players.index(actor)}
                                target_arg = selected_enemy
                                if "target_index" in kwargs:
                                    target_arg = kwargs.pop("target_index")
                                battle_event = engine.perform_player_action(
                                    kind,
                                    target_index=target_arg,
                                    name=name,
                                    **kwargs,
                                )
                            except (ValueError, KeyError) as exc:
                                log.append(str(exc))
                                continue
                            game_over = _apply_node_events([battle_event], log)
                            if not engine.in_battle():
                                selected_enemy = 0
                                target_mode = "enemy"
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
                                target_mode = "enemy"
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
                heal_flag = ""
                if target_mode == "ally" and engine.battle:
                    try:
                        member_index = engine.battle.players.index(member)
                    except ValueError:
                        member_index = -1
                    if member_index == selected_ally:
                        heal_flag = " [heal target]"
                status_lines.append(f"{marker} {member.name}{heal_flag} - {resources}")
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
                    "  Tab to switch enemy/ally healing targets",
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

        # Render status panel (top region: Y=20 to Y=280)
        # This prevents status lines from overlapping with the event log
        _render_lines(screen, font, status_lines, 20, max_y=280)

        # Render event log (bottom region: Y=300 to Y=580)
        # Limit to most recent entries that fit in the region
        max_log_lines = (580 - 300) // font.get_linesize() - 1  # -1 for header
        log_header = ["Event Log:"] + log[-max_log_lines:]
        _render_lines(screen, font, log_header, 300, max_y=580)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

