# Python Text Adventure

The project evolved from an experimental text RPG into a more feature complete
adventure engine.  The current iteration introduces a structured game engine,
multi-enemy combat, a potion and loot system, fishing, shops and a lightweight
pygame user interface.

## Features

- **Flexible game engine** – the `GameEngine` class coordinates movement,
  encounters, inventory and shops in a way that can be reused by different
  front-ends.
- **Multiple enemies** – encounters spawn one to three enemies with automatic
  resolution handled by the `Battle` class.
- **Inventory & potions** – players can equip weapons and armor, purchase items
  from shops, and consume potions that restore HP/MP.
- **Fishing mini-game** – stepping on fishing tiles triggers a catch with gold
  and experience rewards.
- **Map transitions** – the beginner map leads into an intermediate area and the
  journey can return back.
- **Pygame interface** – run the game with a simple graphical overlay that shows
  status, neighbours and recent events.

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
or `quit`).

### Pygame mode

```bash
python main.py --mode pygame
```

Use number keys (`1`, `2`, …) to travel to neighbouring nodes and `H` to consume
the first available potion.  Press `Esc` to exit.

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

