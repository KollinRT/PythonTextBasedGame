# Codebase Guide: Python Text Adventure

This document explains the architecture of the codebase, clarifies the "AI-guided frontier map" system, and provides guidance on how to extend or refactor the Pygame UI.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Understanding the "AI-Guided Frontier Map" System](#understanding-the-ai-guided-frontier-map-system)
3. [Pygame UI Issues and Refactoring Guide](#pygame-ui-issues-and-refactoring-guide)
4. [How to Extend the Codebase](#how-to-extend-the-codebase)

---

## Architecture Overview

The codebase follows a **Model-View separation** pattern:

```
┌─────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                         │
│  ┌─────────────────────┐         ┌─────────────────────────────┐    │
│  │      main.py        │         │     ui/pygame_ui.py         │    │
│  │   (Text Interface)  │         │   (Graphical Interface)     │    │
│  └──────────┬──────────┘         └──────────────┬──────────────┘    │
└─────────────┼───────────────────────────────────┼───────────────────┘
              │                                   │
              │  Both call the same GameEngine    │
              ▼                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           GAME LOGIC LAYER                           │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    game_logic/core.py                        │    │
│  │  ┌─────────────┐  ┌────────────┐  ┌────────────────────┐    │    │
│  │  │ GameEngine  │  │   Battle   │  │  Helper Functions  │    │    │
│  │  │ (orchestr.) │  │  (combat)  │  │  (startGame, etc.) │    │    │
│  │  └─────────────┘  └────────────┘  └────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌────────────────────────┐  ┌──────────────────────────────────┐   │
│  │ game_logic/            │  │ game_logic/persistence.py        │   │
│  │ map_generation.py      │  │ (SQLite save/load)               │   │
│  │ (procedural maps)      │  │                                  │   │
│  └────────────────────────┘  └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                 │
│  ┌───────────────────┐  ┌────────────────┐  ┌───────────────────┐   │
│  │ classes/classes.py│  │ items/items.py │  │ maps/*.py         │   │
│  │ Player, Enemy,    │  │ Shop, Loot,    │  │ Handcrafted maps  │   │
│  │ Mage, Ranger...   │  │ Fishing...     │  │ (beginner, etc.)  │   │
│  └───────────────────┘  └────────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Components

| File | Purpose |
|------|---------|
| `game_logic/core.py` | Central `GameEngine` class that handles movement, battles, shopping, map transitions |
| `game_logic/map_generation.py` | Procedural map generation (the "AI-guided" system) |
| `game_logic/persistence.py` | SQLite database for saving maps and game state |
| `game_logic/simple_graph.py` | Minimal graph data structure for map topology |
| `classes/classes.py` | All character classes: `Player`, `Enemy`, `Mage`, `Ranger`, `Cleric`, `Companion` |
| `items/items.py` | Item definitions, shop system, fishing mechanics |
| `maps/*.py` | Three handcrafted maps: beginner, intermediate, advanced |
| `ui/pygame_ui.py` | Pygame graphical interface |
| `main.py` | Text-based interface and entry point |

---

## Understanding the "AI-Guided Frontier Map" System

**IMPORTANT: The name "AI-guided" is misleading!** There is no actual AI/ML involved. The system is a **procedural random map generator** using weighted probabilities. The term "AI-guided" was likely used by Codex to sound fancy, but it's just random generation with constraints.

### How It Actually Works

The system is in `game_logic/map_generation.py`. Here's what happens:

#### 1. Map Structure (`MapBlueprint`)

```python
@dataclass
class MapBlueprint:
    key: str                              # Unique ID like "frontier_abc123"
    name: str                             # Display name like "Frontier ABC123"
    nodes: Dict[str, Dict[str, object]]   # Node data with features
    edges: List[Tuple[str, str]]          # Connections between nodes
```

A map is just a graph with:
- **Nodes**: Locations you can visit (each can have features like `shop`, `encounter`, `fishing`)
- **Edges**: Paths connecting nodes (bidirectional)

#### 2. Node Features

Each node can have these boolean/dict features:

```python
NODE_FEATURE_WEIGHTS: Dict[str, float] = {
    "encounter": 0.75,   # 75% chance: random enemy battle may occur
    "shop": 0.15,        # 15% chance: can buy items
    "fishing": 0.1,      # 10% chance: fishing mini-game
    "city": 0.12,        # 12% chance: safe rest zone
    "transition": 0.08,  # 8% chance: portal to another map
    "ally": 0.12,        # 12% chance: recruit a companion
}
```

#### 3. Generation Algorithm (`generate_blueprint`)

```python
def generate_blueprint(key, size=12, base_level=1, rng=None):
    # 1. Create first node (always a city with encounters)
    nodes["1"] = {"city": True, "encounter": True}
    
    # 2. Generate remaining nodes in a loop
    while len(nodes) < size:
        # Create node with random features based on weights
        features = _generate_node_features(...)
        
        # Connect to a random existing node (ensures connectivity)
        target = random.choice(existing_nodes)
        edges.append((new_node, target))
        
        # 35% chance to add a second connection (more interesting topology)
        if random.random() < 0.35:
            edges.append((new_node, another_random_node))
    
    # 3. Ensure at least one transition and one ally exist
    if no_transition_yet:
        random_node["transition"] = "auto"
    if no_ally_yet:
        random_node["ally"] = generate_ally_blueprint()
```

#### 4. What "auto" Transition Means

When a node has `"transition": "auto"`:
- When you step on it, `GameEngine._create_generated_map()` is called
- This generates a brand new random map and stores it in SQLite
- The "auto" value is replaced with the new map's key (e.g., `"frontier_abc123"`)
- This creates an "endless" world effect

#### 5. Ally Generation

```python
ALLY_PROFILES = [
    {"class": "player", "names": ["Borin", "Kaia", "Mira", "Thalen"]},
    {"class": "ranger", "names": ["Lyra", "Finn", "Selene", "Rowan"]},
    {"class": "cleric", "names": ["Aria", "Lucan", "Seren", "Moira"]},
    {"class": "mage", "names": ["Eldrin", "Cira", "Varis", "Ilyana"]},
]

def _generate_ally_blueprint(rng, base_level):
    profile = random.choice(ALLY_PROFILES)
    return {
        "name": random.choice(profile["names"]),
        "class": profile["class"],
        "level_bonus": random.randint(-1, 1),
        "personality": random.choice(["cautious", "bold", "curious", "stoic"]),
    }
```

### Flow Diagram

```
Player reaches node with transition="auto"
          │
          ▼
    GameEngine.transition_map("auto")
          │
          ▼
    _create_generated_map()
          │
          ├── generate_blueprint() creates MapBlueprint
          │         │
          │         ├── Creates nodes with random features
          │         ├── Connects them with edges
          │         └── Ensures at least 1 ally + 1 transition
          │
          ├── Stores blueprint in self.maps and self.map_blueprints
          │
          └── persistence.save_map() writes to SQLite
          │
          ▼
    Player teleports to new map's first node
```

### Why It's Called "AI-Guided"

This is a misnomer. The only "intelligence" is:
1. **Weighted randomness** for feature placement
2. **Constraints** ensuring connectivity and required features
3. **Level scaling** where enemy/ally levels match party level

A more accurate name would be: **"Procedural Map Generation with Heuristics"**

---

## Pygame UI Issues and Refactoring Guide

The current `pygame_ui.py` has several architectural problems:

### Problem 1: Single Monolithic Function

The entire UI is in one 340-line `run_pygame_ui()` function. This makes it:
- Hard to understand
- Difficult to modify one part without breaking others
- Impossible to unit test

### Problem 2: Mixed Responsibilities

The function handles:
- Input processing (keyboard events)
- Game state management (battles, movement)
- Rendering (drawing to screen)
- Menu systems (save/load)
- Target selection (enemies/allies)

### Problem 3: Fragile Overlay System

The "overlay" is just text lines drawn at fixed Y positions:
```python
_render_lines(screen, font, status_lines, 20)    # Status at Y=20
_render_lines(screen, font, log_header, 300)     # Log at Y=300
```

If status_lines has too many lines, it overlaps with the log.

### Problem 4: Hardcoded Layout

```python
WINDOW_SIZE = (900, 600)  # Fixed size
start_y = 20              # Fixed positions
```

No dynamic layout based on content size.

### Refactoring Recommendations

#### Step 1: Split Into Classes

```python
# ui/pygame_ui.py - Refactored structure

class GameRenderer:
    """Handles all drawing operations."""
    
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
    
    def draw_status_panel(self, engine, player):
        """Draw player stats in top-left."""
        pass
    
    def draw_battle_panel(self, battle, selected_enemy, target_mode):
        """Draw battle UI when in combat."""
        pass
    
    def draw_exploration_panel(self, neighbors):
        """Draw movement options when exploring."""
        pass
    
    def draw_event_log(self, log):
        """Draw scrollable event log."""
        pass


class InputHandler:
    """Processes keyboard/mouse input."""
    
    def __init__(self, engine):
        self.engine = engine
    
    def handle_exploration_input(self, event, neighbors):
        """Handle movement keys."""
        pass
    
    def handle_battle_input(self, event, battle):
        """Handle combat keys."""
        pass
    
    def handle_menu_input(self, event, menu_mode):
        """Handle save/load menu."""
        pass


class GameUI:
    """Coordinates renderer and input handler."""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.font = pygame.font.Font(None, 28)
        self.engine = GameEngine()
        self.renderer = GameRenderer(self.screen, self.font)
        self.input_handler = InputHandler(self.engine)
        self.log = []
    
    def run(self):
        """Main game loop."""
        while self.running:
            self.process_events()
            self.render()
            self.clock.tick(30)
```

#### Step 2: Create a Layout Manager

```python
class LayoutManager:
    """Calculate positions based on content."""
    
    def __init__(self, screen_size, font):
        self.width, self.height = screen_size
        self.font = font
        self.line_height = font.get_linesize()
        
        # Define regions as percentages
        self.status_region = (0, 0, self.width * 0.5, self.height * 0.5)
        self.battle_region = (self.width * 0.5, 0, self.width * 0.5, self.height * 0.5)
        self.log_region = (0, self.height * 0.5, self.width, self.height * 0.5)
    
    def fit_text_in_region(self, lines, region):
        """Return lines that fit, with scrolling if needed."""
        x, y, w, h = region
        max_lines = int(h / self.line_height)
        return lines[-max_lines:]  # Show most recent
```

#### Step 3: Use Panels for Organization

```python
class Panel:
    """A rectangular region that can render content."""
    
    def __init__(self, rect, bg_color=None, border_color=None):
        self.rect = pygame.Rect(rect)
        self.bg_color = bg_color
        self.border_color = border_color
    
    def draw(self, screen):
        if self.bg_color:
            pygame.draw.rect(screen, self.bg_color, self.rect)
        if self.border_color:
            pygame.draw.rect(screen, self.border_color, self.rect, 2)
    
    def render_text(self, screen, font, lines, color):
        y = self.rect.top + 5
        for line in lines:
            if y + font.get_linesize() > self.rect.bottom:
                break  # Don't overflow
            text = font.render(line, True, color)
            screen.blit(text, (self.rect.left + 5, y))
            y += font.get_linesize()
```

---

## How to Extend the Codebase

### Adding a New Character Class

1. **Define the class in `classes/classes.py`:**

```python
class Paladin(Player):
    """Holy warrior with defensive abilities."""
    
    def __init__(self, name, level, hp, dmg, *, shield_block=0.2, ...):
        super().__init__(name, level, hp, dmg, ...)
        self.shield_block = shield_block  # Chance to block attacks
        self.divine_charges = 3
    
    def available_abilities(self) -> List[str]:
        abilities = []
        if self.divine_charges >= 1:
            abilities.append("holy strike")
        if self.divine_charges >= 2:
            abilities.append("divine shield")
        return abilities
    
    def use_ability(self, name, target):
        if name == "holy strike":
            self.divine_charges -= 1
            damage = int(self.dmg * 1.3)
            target.take_damage(damage)
            return damage, f"smites with Holy Strike for {damage} damage"
        # ...
    
    def to_dict(self):
        data = super().to_dict()
        data["shield_block"] = self.shield_block
        data["divine_charges"] = self.divine_charges
        return data
```

2. **Update `Player.from_dict()` to handle deserialization**

3. **Update `startGame()` in `core.py`:**

```python
def startGame(player_name: str, player_class: str) -> Player:
    player_class = player_class.lower()
    if player_class == "paladin":
        return Paladin(player_name, 1, 130, 13)
    # ... existing classes
```

### Adding a New Map Feature

1. **Add the feature to `NODE_FEATURE_WEIGHTS` in `map_generation.py`:**

```python
NODE_FEATURE_WEIGHTS = {
    # ... existing features
    "dungeon": 0.05,  # 5% chance for a dungeon entrance
}
```

2. **Handle the feature in `_generate_node_features()`:**

```python
if feature == "dungeon":
    features[feature] = {"difficulty": rng.randint(1, 3)}
```

3. **Handle the feature in `GameEngine._handle_node()`:**

```python
if node_data.get("dungeon"):
    events.append(self._enter_dungeon(node_data["dungeon"]))
```

### Adding New Items

Edit `items/items.py` and add to the appropriate list/dict:

```python
# In the Shop class or item definitions
WEAPONS = [
    # ... existing
    Item(name="Flamebrand", level=8, slot="weapon", dmg=18, value=450),
]
```

### Adding a New Node Event Type

1. **Create handler in `GameEngine`:**

```python
def _handle_shrine(self, shrine_data):
    """Restore resources at a shrine."""
    for player in self.player_party:
        player.heal(player.max_hp * 0.5)
        if isinstance(player, Mage):
            player.mp = min(player.max_mp, player.mp + player.max_mp // 2)
    return NodeEvent("shrine", payload="Blessed by the shrine")
```

2. **Call it from `_handle_node()`:**

```python
if node_data.get("shrine"):
    events.append(self._handle_shrine(node_data["shrine"]))
```

3. **Handle in Pygame UI (`_apply_node_events`):**

```python
elif node_event.kind == "shrine":
    log.append(node_event.payload or "Found a shrine")
```

---

## Quick Reference: Key Methods

### GameEngine

| Method | Purpose |
|--------|---------|
| `start_new_game(player)` | Initialize a new game with the given player |
| `move_to(node)` | Move to an adjacent node, returns list of NodeEvents |
| `neighbors()` | Get list of adjacent nodes |
| `in_battle()` | Check if currently in combat |
| `perform_player_action(...)` | Execute a combat action |
| `generate_new_map(size)` | Create a new frontier map |
| `save_game(slot)` / `load_game(slot)` | Persistence |

### Battle

| Method | Purpose |
|--------|---------|
| `current_actor()` | Get whose turn it is (Player or Enemy) |
| `is_over()` | Check if battle ended |
| `player_action(player, action)` | Execute player's action |
| `enemy_action(enemy)` | Execute enemy's action |
| `advance_turn()` | Move to next combatant |

### Player

| Method | Purpose |
|--------|---------|
| `attack_damage()` | Calculate damage with crit chance |
| `take_damage(amount)` | Reduce HP |
| `heal(amount)` | Restore HP |
| `use_potion(name)` | Consume a potion |
| `equip_item(name)` | Equip from inventory |
| `add_follower(player)` | Add a companion |

---

## Summary

1. **The "AI-guided frontier map" is just procedural generation** with random weighted features and guaranteed constraints (at least one ally, one transition per map). No machine learning involved.

2. **The Pygame UI needs refactoring** into separate classes for rendering, input handling, and layout management to fix the overlay issues and make it maintainable.

3. **Extending the codebase** follows clear patterns: add classes in `classes/`, handle features in `GameEngine._handle_node()`, and update UIs to display new events.

4. **The GameEngine is the central coordinator** - both text and Pygame UIs call the same methods, making it easy to add new front-ends.
