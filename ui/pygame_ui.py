from __future__ import annotations

import pygame

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

    running = True
    while running:
        neighbors = engine.neighbors()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    index = event.key - pygame.K_1
                    if index < len(neighbors):
                        events = engine.move_to(neighbors[index])
                        for node_event in events:
                            if node_event.kind == "battle":
                                log.append(node_event.payload or "Battle resolved")
                            elif node_event.kind == "shop":
                                log.append("Visited a shop (use text mode to trade)")
                            elif node_event.kind == "fishing":
                                log.append(node_event.payload or "Fishing result")
                            elif node_event.kind == "transition":
                                log.append(f"Traveled to {node_event.payload}")
                elif event.key == pygame.K_h:
                    # use first available potion
                    potions = list(engine.player_party[0].potions.keys())
                    if potions:
                        try:
                            engine.player_party[0].use_potion(potions[0])
                            log.append(f"Used {potions[0]}")
                        except ValueError:
                            log.append("Cannot use potion yet")
                elif event.key == pygame.K_m and isinstance(player, Mage):
                    available = player.available_spells()
                    if available:
                        log.append(
                            f"Spells ready: {', '.join(spell.name for spell in available)} (cast during battles in text mode)"
                        )

        log = log[-12:]
        screen.fill(BACKGROUND)

        status_lines = [
            f"Location: {engine.current_node} ({engine.current_map_key})",
            f"HP: {player.hp}/{player.max_hp}",
            f"Level: {player.level}  EXP: {player.exp}  Gold: {player.gp}",
            "Neighbors:",
        ]
        status_lines.extend([f"  {idx+1}. {node}" for idx, node in enumerate(neighbors)])
        if isinstance(player, Mage):
            status_lines.insert(2, f"MP: {player.mp}/{player.max_mp}")

        _render_lines(screen, font, status_lines, 20)

        log_header = ["Event Log:"] + log
        _render_lines(screen, font, log_header, 300)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

