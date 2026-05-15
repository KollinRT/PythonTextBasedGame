# Python Text Adventure

The project evolved from an experimental text RPG into a more feature complete
adventure engine.  The current iteration introduces a structured game engine,
multi-enemy combat, a potion and loot system, fishing, shops and a lightweight
pygame user interface.

## Features

- **Flexible game engine** – the `GameEngine` class coordinates movement,
  encounters, inventory and shops in a way that can be reused by different
  front-ends.
- **Initiative-driven combat** – every unit rolls its own initiative and acts in
  order. Heroes, companions, ranger pets and enemies can interleave actions, and
  the battle log records each turn so you can plan accordingly. Healing spells
  can be directed to any ally, letting clerics pivot their support on demand.
- **Class variety & companions** – begin as a stalwart player, arcane mage,
  agile ranger (who now travels with a loyal hawk) or supportive cleric. On your
  travels you can recruit AI-generated allies who permanently join the party.
- **Inventory & potions** – players can equip weapons and armor, purchase items
  from shops, and consume potions that restore HP/MP.
- **Fishing mini-game** – stepping on fishing tiles triggers a catch with gold
  and experience rewards.
- **Expanded world** – the handcrafted Beginner trail, Winding Expanse and
  Frontier Bastion maps interlink with AI-generated frontier regions, so there
  is always a new path to explore.
- **Endless frontier maps** – portals can lead to procedurally generated maps
  that are stored in an on-disk SQLite database so discoveries persist between
  sessions. Generate new regions manually at any time with the `generate` text
  command.
- **Save anywhere** – the engine can be saved and resumed with `save <slot>` and
  `load <slot>` commands. All heroes, companions and map discoveries are stored
  in the same SQLite database.
- **Pygame interface** – run the game with a simple graphical overlay that shows
  status, neighbours, recent events and full battle breakdowns.

## Requirements

- Python 3.10+
- `pygame` (install via `pip install pygame`).

## Running the game

### Text mode

```bash
python main.py
```

Commands are entered as text (for example `move A1`, `potion Basic HP Potion`
or `quit`).  When a battle starts you decide every action: `attack`,
`spell fireball`, `ability power shot` or `potion Major HP Potion`.  Append an
enemy number (e.g. `attack 2`) to focus a specific target, or use
`spell healing prayer ally 2` / `ally Mira` to channel restorative magic to a
specific party member. Rangers can direct their hawk companions by prefixing
commands with `pet`, e.g. `pet attack 2` or `pet ability twin strike` when the
companion's initiative turn arrives.

Additional world commands include:

- `save <slot>` – write the current hero, party and map progress to SQLite.
- `load <slot>` – resume a previous save.
- `generate [size]` – create a new AI-guided frontier map (size defaults to a
  random value).
- `saves` – list the available save slots.

### Pygame mode

```bash
python main.py --mode pygame
```

Use number keys (`1`, `2`, …), the arrow keys or `WASD` to travel to neighbouring
nodes.  Press `H` to consume the first available potion and `Esc` to exit.  Tap
`F5` to open the save menu and choose a slot with `1-9`, and `F9` to open the
load menu — the pygame client reads and writes the same SQLite slots as text
mode so you can swap between interfaces seamlessly.  In battle, use the arrow
keys or `A`/`D` to choose a foe, press `Tab` to toggle ally targeting for healing
spells, use number keys to trigger attacks, spells or abilities, and `H` to drink
a potion while enemies counter. The HUD shows whose turn it is so you know when a
companion or ranger's pet is waiting for orders – the action keys always
control the highlighted party member.

### Controls at a glance

- **Text mode** – type `move <node>` to travel, issue battle commands such as
  `attack`, `spell <name>` or `ability <name>`, use `potion <name>` to heal,
  `save <slot>`/`load <slot>` to persist progress, `generate` to spawn a new map
  and `quit` to leave the adventure.
- **Pygame mode** – move with `1-9`, `WASD` or the arrow keys when exploring.
  During battles use the arrow keys/A-D to select an enemy, press `Tab` to switch
  between enemy and ally healing targets, `1-9` to perform
  actions, `H` to drink the first potion, `F5`/`F9` to save or load a slot and
  `Esc` to quit. The same slots appear in both interfaces.

## Persistence and databases

Generated frontier maps and save slots are stored in an SQLite database (by
default `game_data.db`). SQLite offers the right balance of portability and
capability for a local adventure game: it is part of Python's standard library,
requires no external server, yet is robust enough to hold the procedurally
generated content and long-term save data. The `ADVENTURE_DB` environment
variable can be set to point the engine at an alternate database path if
desired.

## Project layout

```
├── api
│   └── app.py            # FastAPI service for browser clients
├── frontend
│   └── src/main.jsx      # React client for online play
├── classes
│   ├── classes.py        # Player, Enemy, Mage and supporting data classes
│   └── items.py          # Simple helpers for consumables
├── game_logic
│   └── core.py           # GameEngine, Battle system and helpers
├── items
│   └── items.py          # Item definitions, shops, fishing table
├── maps
│   ├── beginner_map.py   # Introductory map
│   ├── intermediate_map.py  # Mid-game routes
│   └── advanced_map.py   # Frontier Bastion layout
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


## Web API and React client

The game engine can now run as a JSON API for browser clients. This makes the
existing adventure logic usable from a hosted React app while keeping the CLI and
pygame front-ends intact.

### Start the API

```bash
pip install -r requirements.txt
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

Useful endpoints include:

- `POST /sessions` with `{ "name": "Hero", "player_class": "mage" }` to start a game.
- `GET /sessions/{session_id}` to reconnect to an in-memory game session.
- `POST /sessions/{session_id}/move` with `{ "destination": "A1" }` to explore.
- `POST /sessions/{session_id}/battle/action` to submit battle choices.
- `POST /sessions/{session_id}/save` and `/load` to use the existing SQLite save slots.

Sessions are in-memory, so a simple single-server deployment is enough for a
friends-and-family hosted game. For a larger public deployment, back the session
store with Redis or persist active sessions in SQLite/Postgres before running
multiple API workers.

### Start the React client

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

Open the Vite URL, create a session, and share the session id with a friend so
they can join the same running adventure through the API.
