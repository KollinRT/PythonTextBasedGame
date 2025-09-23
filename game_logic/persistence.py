"""SQLite backed persistence helpers for generated maps and save slots."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Dict, Iterator, List, Optional

from game_logic.map_generation import MapBlueprint


class PersistenceManager:
    """Manage storage of maps and game saves using SQLite."""

    def __init__(self, path: str = "game_data.db") -> None:
        self.path = path
        self._ensure_schema()

    # ------------------------------------------------------------------
    # Schema helpers
    # ------------------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS maps (
                    key TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    data TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS game_saves (
                    slot TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    map_key TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    # ------------------------------------------------------------------
    # Map storage
    # ------------------------------------------------------------------
    def save_map(self, blueprint: MapBlueprint) -> None:
        payload = blueprint.to_json()
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO maps (key, name, data) VALUES (?, ?, ?)",
                (blueprint.key, blueprint.name, payload),
            )

    def load_map(self, key: str) -> Optional[MapBlueprint]:
        with self._connect() as conn:
            row = conn.execute("SELECT data FROM maps WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        return MapBlueprint.from_json(row[0])

    def iter_maps(self) -> Iterator[MapBlueprint]:
        with self._connect() as conn:
            for row in conn.execute("SELECT data FROM maps"):
                yield MapBlueprint.from_json(row[0])

    def delete_map(self, key: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM maps WHERE key = ?", (key,))

    # ------------------------------------------------------------------
    # Game saves
    # ------------------------------------------------------------------
    def save_game(self, slot: str, state: Dict[str, object], *, map_key: str) -> None:
        payload = json.dumps(state)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO game_saves (slot, data, map_key) VALUES (?, ?, ?)",
                (slot, payload, map_key),
            )

    def load_game(self, slot: str) -> Optional[Dict[str, object]]:
        with self._connect() as conn:
            row = conn.execute("SELECT data FROM game_saves WHERE slot = ?", (slot,)).fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def list_saves(self) -> List[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT slot FROM game_saves ORDER BY updated_at DESC").fetchall()
        return [row[0] for row in rows]

    def delete_save(self, slot: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM game_saves WHERE slot = ?", (slot,))


def default_db_path() -> str:
    """Return a path suitable for local SQLite storage."""

    return os.environ.get("ADVENTURE_DB", "game_data.db")
