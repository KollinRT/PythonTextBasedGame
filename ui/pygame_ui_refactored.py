"""Refactored Pygame UI with proper separation of concerns.

This module provides the same functionality as pygame_ui.py but with:
- Clear separation between rendering, input handling, and game state
- Panel-based layout that prevents overlap
- Easier extensibility for new features

You can use this as a drop-in replacement or as a reference for refactoring.
"""

from __future__ import annotations

import pygame
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from classes.classes import Mage, Player
from game_logic.core import GameEngine, NodeEvent, startGame


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class UIConfig:
    """Centralized configuration for the UI."""
    
    window_size: Tuple[int, int] = (1000, 700)
    
    # Colors
    background: Tuple[int, int, int] = (30, 30, 40)
    text_color: Tuple[int, int, int] = (230, 230, 230)
    panel_bg: Tuple[int, int, int] = (40, 40, 55)
    panel_border: Tuple[int, int, int] = (80, 80, 100)
    highlight_color: Tuple[int, int, int] = (100, 200, 100)
    warning_color: Tuple[int, int, int] = (200, 100, 100)
    
    # Font
    font_size: int = 24
    
    # Layout (percentages of window)
    status_panel_width: float = 0.35
    status_panel_height: float = 0.45
    
    battle_panel_width: float = 0.65
    battle_panel_height: float = 0.45
    
    log_panel_height: float = 0.55
    
    panel_padding: int = 10
    panel_margin: int = 5


# =============================================================================
# PANEL SYSTEM
# =============================================================================

@dataclass
class Panel:
    """A rectangular region that can render content with optional scrolling."""
    
    rect: pygame.Rect
    bg_color: Optional[Tuple[int, int, int]] = None
    border_color: Optional[Tuple[int, int, int]] = None
    title: Optional[str] = None
    padding: int = 10
    
    def draw_background(self, screen: pygame.Surface) -> None:
        """Draw panel background and border."""
        if self.bg_color:
            pygame.draw.rect(screen, self.bg_color, self.rect)
        if self.border_color:
            pygame.draw.rect(screen, self.border_color, self.rect, 2)
    
    def get_content_rect(self, font: pygame.font.Font) -> pygame.Rect:
        """Get the drawable area inside the panel (accounting for title and padding)."""
        y_offset = self.padding
        if self.title:
            y_offset += font.get_linesize() + 5
        return pygame.Rect(
            self.rect.left + self.padding,
            self.rect.top + y_offset,
            self.rect.width - 2 * self.padding,
            self.rect.height - y_offset - self.padding
        )
    
    def max_lines(self, font: pygame.font.Font) -> int:
        """Calculate how many lines of text fit in the panel."""
        content_rect = self.get_content_rect(font)
        return max(1, content_rect.height // font.get_linesize())
    
    def render_title(self, screen: pygame.Surface, font: pygame.font.Font, 
                     color: Tuple[int, int, int]) -> None:
        """Draw the panel title if set."""
        if self.title:
            title_surf = font.render(self.title, True, color)
            screen.blit(title_surf, (self.rect.left + self.padding, self.rect.top + 5))
    
    def render_lines(self, screen: pygame.Surface, font: pygame.font.Font,
                     lines: List[str], color: Tuple[int, int, int],
                     highlights: Optional[Dict[int, Tuple[int, int, int]]] = None) -> None:
        """
        Render lines of text within the panel, respecting boundaries.
        
        Args:
            highlights: Optional dict mapping line index to highlight color
        """
        content_rect = self.get_content_rect(font)
        max_lines = self.max_lines(font)
        
        # Only show lines that fit
        visible_lines = lines[-max_lines:] if len(lines) > max_lines else lines
        
        y = content_rect.top
        for idx, line in enumerate(visible_lines):
            if y + font.get_linesize() > content_rect.bottom:
                break
            
            # Determine color (check for highlights)
            line_color = color
            if highlights:
                original_idx = len(lines) - len(visible_lines) + idx
                if original_idx in highlights:
                    line_color = highlights[original_idx]
            
            text_surf = font.render(line, True, line_color)
            
            # Clip text to panel width
            if text_surf.get_width() > content_rect.width:
                # Truncate with ellipsis
                truncated = line
                while font.size(truncated + "...")[0] > content_rect.width and len(truncated) > 0:
                    truncated = truncated[:-1]
                text_surf = font.render(truncated + "...", True, line_color)
            
            screen.blit(text_surf, (content_rect.left, y))
            y += font.get_linesize()


class LayoutManager:
    """Manages panel positions based on window size and configuration."""
    
    def __init__(self, config: UIConfig):
        self.config = config
        self._panels: Dict[str, Panel] = {}
        self._calculate_layout()
    
    def _calculate_layout(self) -> None:
        """Calculate panel positions based on configuration."""
        w, h = self.config.window_size
        m = self.config.panel_margin
        
        # Status panel (top-left)
        status_w = int(w * self.config.status_panel_width) - m
        status_h = int(h * self.config.status_panel_height) - m
        self._panels["status"] = Panel(
            rect=pygame.Rect(m, m, status_w, status_h),
            bg_color=self.config.panel_bg,
            border_color=self.config.panel_border,
            title="Status",
            padding=self.config.panel_padding
        )
        
        # Battle/Context panel (top-right)
        battle_x = status_w + 2 * m
        battle_w = w - battle_x - m
        battle_h = int(h * self.config.battle_panel_height) - m
        self._panels["context"] = Panel(
            rect=pygame.Rect(battle_x, m, battle_w, battle_h),
            bg_color=self.config.panel_bg,
            border_color=self.config.panel_border,
            title="",  # Dynamic title
            padding=self.config.panel_padding
        )
        
        # Event log panel (bottom, full width)
        log_y = int(h * self.config.status_panel_height) + m
        log_h = h - log_y - m
        self._panels["log"] = Panel(
            rect=pygame.Rect(m, log_y, w - 2 * m, log_h),
            bg_color=self.config.panel_bg,
            border_color=self.config.panel_border,
            title="Event Log",
            padding=self.config.panel_padding
        )
    
    def get_panel(self, name: str) -> Panel:
        return self._panels[name]
    
    def all_panels(self) -> Iterable[Panel]:
        return self._panels.values()


# =============================================================================
# RENDERER
# =============================================================================

class GameRenderer:
    """Handles all drawing operations for the game UI."""
    
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, 
                 layout: LayoutManager, config: UIConfig):
        self.screen = screen
        self.font = font
        self.layout = layout
        self.config = config
    
    def clear(self) -> None:
        """Clear screen with background color."""
        self.screen.fill(self.config.background)
    
    def draw_panels(self) -> None:
        """Draw all panel backgrounds."""
        for panel in self.layout.all_panels():
            panel.draw_background(self.screen)
    
    def render_status(self, engine: GameEngine, player: Player) -> None:
        """Render player status panel."""
        panel = self.layout.get_panel("status")
        panel.render_title(self.screen, self.font, self.config.text_color)
        
        map_info = engine.map_blueprints.get(engine.current_map_key)
        map_label = map_info.name if map_info else engine.current_map_key
        
        lines = [
            f"Location: {engine.current_node}",
            f"Map: {map_label}",
            "",
            f"HP: {player.hp}/{player.max_hp}",
        ]
        
        if isinstance(player, Mage):
            lines.append(f"MP: {player.mp}/{player.max_mp}")
        
        lines.extend([
            f"Level: {player.level}",
            f"EXP: {player.exp}",
            f"Gold: {player.gp}",
        ])
        
        # Show party members if any
        if len(engine.player_party) > 1:
            lines.append("")
            lines.append("Party:")
            for member in engine.player_party[1:]:  # Skip main hero
                hp_str = f"{member.hp}/{member.max_hp}"
                lines.append(f"  {member.name}: {hp_str} HP")
        
        panel.render_lines(self.screen, self.font, lines, self.config.text_color)
    
    def render_battle_context(self, engine: GameEngine, 
                               selected_enemy: int, selected_ally: int,
                               target_mode: str) -> None:
        """Render battle information panel."""
        panel = self.layout.get_panel("context")
        panel.title = "Battle"
        panel.render_title(self.screen, self.font, self.config.text_color)
        
        if not engine.battle:
            return
        
        battle = engine.battle
        actor = battle.current_actor()
        
        lines: List[str] = []
        highlights: Dict[int, Tuple[int, int, int]] = {}
        
        # Current turn indicator
        if actor:
            lines.append(f"Current turn: {actor.name}")
            highlights[0] = self.config.highlight_color
        
        lines.append("")
        
        # Party status
        lines.append("Your Party:")
        for idx, member in enumerate(battle.players):
            marker = "→" if actor is member else " "
            status = f"{member.hp}/{member.max_hp} HP"
            if isinstance(member, Mage):
                status += f" | {member.mp}/{member.max_mp} MP"
            
            heal_marker = ""
            if target_mode == "ally" and idx == selected_ally:
                heal_marker = " [HEAL TARGET]"
                highlights[len(lines)] = self.config.highlight_color
            
            alive = "✓" if member.is_alive() else "✗"
            lines.append(f"{marker} {alive} {member.name}: {status}{heal_marker}")
        
        lines.append("")
        
        # Enemy status
        lines.append("Enemies:")
        for idx, enemy in enumerate(battle.enemies):
            marker = "→" if idx == selected_enemy and target_mode == "enemy" else " "
            if enemy.is_alive():
                status = f"{enemy.hp}/{enemy.max_hp} HP"
                if idx == selected_enemy and target_mode == "enemy":
                    highlights[len(lines)] = self.config.warning_color
            else:
                status = "DEFEATED"
            lines.append(f"{marker} {idx+1}. {enemy.name}: {status}")
        
        lines.append("")
        
        # Available actions
        actions = engine.list_player_actions()
        if actions and isinstance(actor, Player):
            lines.append("Actions (press 1-9):")
            for idx, (kind, name) in enumerate(actions, 1):
                if idx > 9:
                    break
                label = kind if not name else f"{kind}: {name}"
                lines.append(f"  {idx}. {label}")
        
        panel.render_lines(self.screen, self.font, lines, self.config.text_color, highlights)
    
    def render_exploration_context(self, neighbors: List[str]) -> None:
        """Render exploration/movement panel."""
        panel = self.layout.get_panel("context")
        panel.title = "Exploration"
        panel.render_title(self.screen, self.font, self.config.text_color)
        
        lines = [
            "Available paths (press 1-9 or WASD):",
            "",
        ]
        
        for idx, node in enumerate(neighbors, 1):
            if idx > 9:
                break
            lines.append(f"  {idx}. {node}")
        
        if not neighbors:
            lines.append("  No adjacent paths!")
        
        lines.extend([
            "",
            "Controls:",
            "  1-9, WASD, Arrows: Move",
            "  H: Use first potion",
            "  G: Generate new frontier map",
            "  F5: Save game",
            "  F9: Load game",
            "  Esc: Quit",
        ])
        
        panel.render_lines(self.screen, self.font, lines, self.config.text_color)
    
    def render_menu(self, menu_mode: str, slots: List[str]) -> None:
        """Render save/load menu in the context panel."""
        panel = self.layout.get_panel("context")
        panel.title = "Save" if menu_mode == "save" else "Load"
        panel.render_title(self.screen, self.font, self.config.text_color)
        
        lines = [
            f"Select a slot (1-9) or Esc to cancel:",
            "",
        ]
        
        for idx, slot in enumerate(slots, 1):
            if idx > 9:
                break
            lines.append(f"  {idx}. {slot}")
        
        if not slots and menu_mode == "load":
            lines.append("  No saved games found!")
        
        panel.render_lines(self.screen, self.font, lines, self.config.text_color)
    
    def render_event_log(self, log: List[str]) -> None:
        """Render the scrolling event log."""
        panel = self.layout.get_panel("log")
        panel.render_title(self.screen, self.font, self.config.text_color)
        panel.render_lines(self.screen, self.font, log, self.config.text_color)
    
    def flip(self) -> None:
        """Update the display."""
        pygame.display.flip()


# =============================================================================
# INPUT HANDLER
# =============================================================================

@dataclass
class InputResult:
    """Result of processing an input event."""
    
    quit: bool = False
    node_events: List[NodeEvent] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    menu_change: Optional[str] = None  # "save", "load", or None to close


class InputHandler:
    """Processes keyboard input and translates to game actions."""
    
    def __init__(self, engine: GameEngine):
        self.engine = engine
    
    def get_living_enemy_indices(self) -> List[int]:
        """Get indices of living enemies in current battle."""
        if not self.engine.battle:
            return []
        return [idx for idx, e in enumerate(self.engine.battle.enemies) if e.is_alive()]
    
    def get_living_ally_indices(self) -> List[int]:
        """Get indices of living allies in current battle."""
        if not self.engine.battle:
            return []
        return [idx for idx, p in enumerate(self.engine.battle.players) if p.is_alive()]
    
    def handle_menu_input(self, event: pygame.event.Event, 
                          menu_mode: str, slots: List[str]) -> InputResult:
        """Handle input while in save/load menu."""
        result = InputResult()
        
        if event.key == pygame.K_ESCAPE:
            result.messages.append("Cancelled.")
            result.menu_change = None  # Close menu
            return result
        
        if pygame.K_1 <= event.key <= pygame.K_9:
            index = event.key - pygame.K_1
            if index < len(slots):
                slot = slots[index]
                if menu_mode == "save":
                    try:
                        self.engine.save_game(slot)
                        result.messages.append(f"Saved to '{slot}'.")
                    except RuntimeError as e:
                        result.messages.append(str(e))
                else:
                    try:
                        self.engine.load_game(slot)
                        result.messages.append(f"Loaded '{slot}'.")
                    except (KeyError, ValueError) as e:
                        result.messages.append(str(e))
                result.menu_change = None  # Close menu
            else:
                result.messages.append("Invalid slot number.")
        
        return result
    
    def handle_battle_input(self, event: pygame.event.Event,
                            selected_enemy: int, selected_ally: int,
                            target_mode: str) -> Tuple[InputResult, int, int, str]:
        """
        Handle input during battle.
        Returns (result, new_selected_enemy, new_selected_ally, new_target_mode)
        """
        result = InputResult()
        living = self.get_living_enemy_indices()
        allies = self.get_living_ally_indices()
        
        # Target selection
        if event.key in {pygame.K_a, pygame.K_LEFT}:
            if target_mode == "ally" and allies:
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
            if target_mode == "ally" and allies:
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
                if allies:
                    target_mode = "ally"
                    selected_ally = allies[0] if selected_ally not in allies else selected_ally
                    result.messages.append("Now targeting allies (for healing).")
                else:
                    result.messages.append("No allies to target.")
            else:
                target_mode = "enemy"
                result.messages.append("Now targeting enemies.")
        
        # Action keys
        elif pygame.K_1 <= event.key <= pygame.K_9:
            actions = self.engine.list_player_actions()
            index = event.key - pygame.K_1
            if index < len(actions):
                kind, name = actions[index]
                try:
                    kwargs: Dict[str, object] = {}
                    actor = self.engine.battle.current_actor() if self.engine.battle else None
                    
                    # Handle healing spell targeting
                    if kind == "spell" and isinstance(actor, Mage) and name:
                        spell = actor.spells.get(name)
                        if spell and spell.healing > 0:
                            if target_mode == "ally" and allies:
                                target_idx = selected_ally if selected_ally in allies else allies[0]
                                kwargs = {"target_kind": "ally", "target_index": target_idx}
                            else:
                                kwargs = {"target_kind": "ally", 
                                         "target_index": self.engine.battle.players.index(actor) 
                                                        if self.engine.battle else 0}
                    
                    target_arg = kwargs.pop("target_index", selected_enemy)
                    battle_event = self.engine.perform_player_action(
                        kind,
                        target_index=target_arg,
                        name=name,
                        **kwargs
                    )
                    result.node_events.append(battle_event)
                    
                    # Reset selection if battle ended
                    if not self.engine.in_battle():
                        selected_enemy = 0
                        target_mode = "enemy"
                        
                except (ValueError, KeyError) as e:
                    result.messages.append(str(e))
            else:
                result.messages.append("No action for that key.")
        
        # Potion use
        elif event.key == pygame.K_h:
            potions = list(self.engine.player_party[0].potions.keys())
            if potions:
                try:
                    battle_event = self.engine.perform_player_action("potion", name=potions[0])
                    result.node_events.append(battle_event)
                    if not self.engine.in_battle():
                        selected_enemy = 0
                        target_mode = "enemy"
                except (ValueError, KeyError) as e:
                    result.messages.append(str(e))
            else:
                result.messages.append("No potions available.")
        
        return result, selected_enemy, selected_ally, target_mode
    
    def handle_exploration_input(self, event: pygame.event.Event,
                                  neighbors: List[str]) -> InputResult:
        """Handle input during exploration."""
        result = InputResult()
        
        move_target: Optional[str] = None
        
        if pygame.K_1 <= event.key <= pygame.K_9:
            index = event.key - pygame.K_1
            if index < len(neighbors):
                move_target = neighbors[index]
            else:
                result.messages.append("No path for that number.")
        
        elif event.key in {pygame.K_w, pygame.K_UP}:
            if neighbors:
                move_target = neighbors[0]
        
        elif event.key in {pygame.K_d, pygame.K_RIGHT}:
            if len(neighbors) >= 2:
                move_target = neighbors[1]
        
        elif event.key in {pygame.K_s, pygame.K_DOWN}:
            if len(neighbors) >= 3:
                move_target = neighbors[2]
        
        elif event.key in {pygame.K_a, pygame.K_LEFT}:
            if len(neighbors) >= 4:
                move_target = neighbors[3]
        
        elif event.key == pygame.K_h:
            potions = list(self.engine.player_party[0].potions.keys())
            if potions:
                try:
                    self.engine.player_party[0].use_potion(potions[0])
                    result.messages.append(f"Used {potions[0]}.")
                except (ValueError, KeyError) as e:
                    result.messages.append(str(e))
            else:
                result.messages.append("No potions available.")
        
        elif event.key == pygame.K_g:
            new_map = self.engine.generate_new_map()
            result.messages.append(new_map.payload or "Generated new frontier map.")
        
        elif event.key == pygame.K_F5:
            result.menu_change = "save"
        
        elif event.key == pygame.K_F9:
            result.menu_change = "load"
        
        elif event.key == pygame.K_ESCAPE:
            result.quit = True
        
        # Execute movement
        if move_target:
            try:
                events = self.engine.move_to(move_target)
                result.node_events.extend(events)
            except (ValueError, RuntimeError) as e:
                result.messages.append(str(e))
        
        return result


# =============================================================================
# EVENT PROCESSOR
# =============================================================================

def process_node_events(events: Iterable[NodeEvent], log: List[str]) -> bool:
    """
    Process node events and add messages to log.
    Returns True if game over occurred.
    """
    game_over = False
    
    for event in events:
        if event.kind == "battle":
            if event.payload:
                log.append(event.payload)
            log.extend(event.details)
            if event.game_over:
                game_over = True
                log.append("☠ Your party has fallen. Press Esc to exit.")
        
        elif event.kind == "shop":
            log.append("🏪 Found a shop! (Use text mode to trade)")
        
        elif event.kind == "fishing":
            log.append(f"🎣 {event.payload or 'Caught something!'}")
        
        elif event.kind == "transition":
            log.append(f"🌀 Traveled to {event.payload}")
        
        elif event.kind == "ally":
            log.append(f"⚔ {event.payload or 'New ally joined!'}")
            log.extend(event.details)
        
        elif event.kind == "map":
            log.append(f"🗺 {event.payload or 'Discovered new territory'}")
        
        elif event.kind == "city":
            log.append("🏠 Reached a safe area.")
        
        elif event.payload:
            log.append(event.payload)
    
    return game_over


# =============================================================================
# SLOT BUILDER
# =============================================================================

def build_slot_options(engine: GameEngine, include_new: bool) -> List[str]:
    """Build list of save slots, optionally including empty ones."""
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


# =============================================================================
# MAIN GAME UI CLASS
# =============================================================================

class GameUI:
    """Main game UI coordinating all components."""
    
    def __init__(self, config: Optional[UIConfig] = None):
        self.config = config or UIConfig()
        
        pygame.init()
        self.screen = pygame.display.set_mode(self.config.window_size)
        pygame.display.set_caption("Python Text Adventure")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, self.config.font_size)
        
        # Game state
        self.engine = GameEngine()
        player = startGame("Hero", "player")
        self.engine.start_new_game(player)
        
        # UI state
        self.log: List[str] = list(self.engine.event_log)
        self.selected_enemy = 0
        self.selected_ally = 0
        self.target_mode = "enemy"
        self.menu_mode: Optional[str] = None
        self.menu_slots: List[str] = []
        self.game_over = False
        self.running = True
        
        # Components
        self.layout = LayoutManager(self.config)
        self.renderer = GameRenderer(self.screen, self.font, self.layout, self.config)
        self.input_handler = InputHandler(self.engine)
    
    @property
    def player(self) -> Player:
        """Get the main player character."""
        if self.engine.player_party:
            return self.engine.player_party[0]
        return startGame("Hero", "player")  # Fallback
    
    def process_events(self) -> None:
        """Process all pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            if event.type != pygame.KEYDOWN:
                continue
            
            # Handle menu mode
            if self.menu_mode:
                result = self.input_handler.handle_menu_input(
                    event, self.menu_mode, self.menu_slots
                )
                self.log.extend(result.messages)
                if result.menu_change is None:  # Close menu
                    self.menu_mode = None
                continue
            
            # Global keys
            if event.key == pygame.K_ESCAPE:
                self.running = False
                return
            
            if event.key == pygame.K_F5 and not self.game_over:
                self.menu_slots = build_slot_options(self.engine, include_new=True)
                self.menu_mode = "save"
                self.log.append("Select save slot (1-9):")
                continue
            
            if event.key == pygame.K_F9:
                self.menu_slots = build_slot_options(self.engine, include_new=False)
                if self.menu_slots:
                    self.menu_mode = "load"
                    self.log.append("Select load slot (1-9):")
                else:
                    self.log.append("No saved games found.")
                continue
            
            # Skip input if game over
            if self.game_over:
                continue
            
            # Battle or exploration input
            if self.engine.in_battle():
                result, self.selected_enemy, self.selected_ally, self.target_mode = \
                    self.input_handler.handle_battle_input(
                        event, self.selected_enemy, self.selected_ally, self.target_mode
                    )
            else:
                neighbors = self.engine.neighbors()
                result = self.input_handler.handle_exploration_input(event, neighbors)
            
            # Process results
            self.log.extend(result.messages)
            
            if result.node_events:
                self.game_over = process_node_events(result.node_events, self.log)
            
            if result.menu_change:
                self.menu_mode = result.menu_change
                if self.menu_mode == "save":
                    self.menu_slots = build_slot_options(self.engine, include_new=True)
                else:
                    self.menu_slots = build_slot_options(self.engine, include_new=False)
            
            if result.quit:
                self.running = False
    
    def render(self) -> None:
        """Render the current game state."""
        self.renderer.clear()
        self.renderer.draw_panels()
        
        # Status panel (always shown)
        self.renderer.render_status(self.engine, self.player)
        
        # Context panel (battle, exploration, or menu)
        if self.menu_mode:
            self.renderer.render_menu(self.menu_mode, self.menu_slots)
        elif self.engine.in_battle():
            self.renderer.render_battle_context(
                self.engine, self.selected_enemy, self.selected_ally, self.target_mode
            )
        else:
            self.renderer.render_exploration_context(self.engine.neighbors())
        
        # Event log
        self.renderer.render_event_log(self.log)
        
        self.renderer.flip()
    
    def run(self) -> None:
        """Main game loop."""
        while self.running:
            self.process_events()
            self.render()
            self.clock.tick(30)
        
        pygame.quit()


# =============================================================================
# ENTRY POINT
# =============================================================================

def run_pygame_ui() -> None:
    """Entry point matching the original module's interface."""
    ui = GameUI()
    ui.run()


if __name__ == "__main__":
    run_pygame_ui()
