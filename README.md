# Python Text Adventure

The project evolved from an experimental text RPG into a more feature complete
adventure engine.  The current iteration introduces a structured game engine,
multi-enemy combat, a potion and loot system, fishing, shops and a lightweight
pygame user interface.

## Features

- **Flexible game engine** – the `GameEngine` class coordinates movement,
  encounters, inventory and shops in a way that can be reused by different
  front-ends.
- **Multiple enemies & tactical combat** – encounters spawn one to three enemies
  and turn-based battles let you choose between attacks, spells, abilities and
  potions each round.
- **Class variety** – begin as a stalwart player, arcane mage, agile ranger or
  supportive cleric, each with distinct stats and abilities.
- **Inventory & potions** – players can equip weapons and armor, purchase items
  from shops, and consume potions that restore HP/MP.
- **Fishing mini-game** – stepping on fishing tiles triggers a catch with gold
  and experience rewards.
- **Map transitions** – the beginner map leads into an intermediate area and the
  journey can return back.
- **Pygame interface** – run the game with a simple graphical overlay that shows
  status, neighbours, recent events and full battle breakdowns.

## Requirements

- Python 3.10+
- `pygame` and `networkx` (install via `pip install -r requirements.txt` or
  manually `pip install pygame networkx`).

## Running the game

### Text mode

```bash
python main.py
```

Commands are entered as text (for example `move A1`, `potion Basic HP Potion`
or `quit`).  When a battle starts you decide every action: `attack`,
`spell fireball`, `ability power shot` or `potion Major HP Potion`.  Append an
enemy number (e.g. `attack 2`) to focus a specific target.

### Pygame mode

```bash
python main.py --mode pygame
```

Use number keys (`1`, `2`, …), the arrow keys or `WASD` to travel to neighbouring
nodes.  Press `H` to consume the first available potion and `Esc` to exit.  In
battle, use the arrow keys or `A`/`D` to choose a target, number keys to trigger
attacks, spells or abilities, and `H` to drink a potion while enemies counter.

### Controls at a glance

- **Text mode** – type `move <node>` to travel, issue battle commands such as
  `attack`, `spell <name>` or `ability <name>`, use `potion <name>` to heal and
  `quit` to leave the adventure.
- **Pygame mode** – move with `1-9`, `WASD` or the arrow keys when exploring.
  During battles use the arrow keys/A-D to select an enemy, `1-9` to perform
  actions, `H` to drink the first potion and `Esc` to quit.

## Project layout

```
├── classes
│   ├── classes.py        # Player, Enemy, Mage and supporting data classes
│   └── items.py          # Simple helpers for consumables
├── game_logic
│   └── core.py           # GameEngine, Battle system and helpers
├── items
│   └── items.py          # Item definitions, shops, fishing table
├── maps
│   ├── beginner_map.py   # Introductory map
│   └── intermediate_map.py
├── ui
│   └── pygame_ui.py      # Graphical front-end
└── tests                 # Pytest suite
```

## Testing

Run the automated test-suite with:

```bash
pytest
```

## Contribution guidelines

- Keep the core logic under `game_logic/core.py` clean and without print
  side-effects to allow reuse by multiple interfaces.
- Write or update tests for any new feature.
- Prefer dataclasses for new data structures and keep interactions deterministic
  where possible to simplify testing.

