"""Small HTTP API and static React host for the adventure game.

This module intentionally uses only Python's standard library so the game can be
served on a small VM, Replit, Codespace, or a friend's laptop without adding a
framework requirement.  It exposes JSON endpoints consumed by the React app in
``frontend/static`` and keeps active games in memory, keyed by a shareable
session id.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from classes.classes import Enemy, Mage, Player
from game_logic.core import GameEngine, NodeEvent, startGame

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "frontend" / "static"


def _item_summary(item: Any) -> Dict[str, Any]:
    return {
        "name": item.name,
        "level": item.level,
        "slot": item.slot,
        "dmg": item.dmg,
        "hp": item.hp,
        "mp": item.mp,
        "value": item.value,
        "quantity": item.quantity,
    }


def _player_summary(player: Player) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "name": player.name,
        "class": player.__class__.__name__,
        "level": player.level,
        "hp": player.hp,
        "max_hp": player.max_hp,
        "dmg": player.dmg,
        "exp": player.exp,
        "gp": player.gp,
        "alive": player.is_alive(),
        "potions": [_item_summary(item) for item in player.potions.values()],
        "inventory": [_item_summary(item) for item in player.inventory.values()],
        "equipment": {slot: _item_summary(item) for slot, item in player.equipment.items()},
    }
    if isinstance(player, Mage):
        data["mp"] = player.mp
        data["max_mp"] = player.max_mp
        data["spells"] = [spell.to_dict() for spell in player.available_spells()]
    if hasattr(player, "available_abilities"):
        data["abilities"] = list(player.available_abilities())  # type: ignore[attr-defined]
    if hasattr(player, "focus"):
        data["focus"] = getattr(player, "focus")
        data["max_focus"] = getattr(player, "max_focus")
    role = getattr(player, "role", None)
    if role:
        data["role"] = role
    return data


def _enemy_summary(enemy: Enemy, index: int) -> Dict[str, Any]:
    return {
        "index": index,
        "name": enemy.name,
        "level": enemy.level,
        "hp": enemy.hp,
        "max_hp": enemy.max_hp,
        "dmg": enemy.dmg,
        "alive": enemy.is_alive(),
    }


def _node_event_summary(event: NodeEvent) -> Dict[str, Any]:
    return {
        "kind": event.kind,
        "payload": event.payload,
        "details": list(event.details),
        "game_over": event.game_over,
    }


class SessionStore:
    """Thread-safe in-memory game session registry."""

    def __init__(self) -> None:
        self._sessions: Dict[str, GameEngine] = {}
        self._lock = RLock()

    def create(self, name: str, player_class: str) -> str:
        engine = GameEngine()
        engine.start_new_game(startGame(name or "Hero", player_class or "player"))
        session_id = uuid4().hex[:10]
        with self._lock:
            self._sessions[session_id] = engine
        return session_id

    def get(self, session_id: str) -> GameEngine:
        with self._lock:
            engine = self._sessions.get(session_id)
        if not engine:
            raise KeyError(f"Session '{session_id}' was not found")
        return engine

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


STORE = SessionStore()


def describe_engine(engine: GameEngine, session_id: str, events: Optional[List[NodeEvent]] = None) -> Dict[str, Any]:
    """Return a JSON-serializable snapshot for clients."""

    battle = engine.battle
    map_info = engine.map_blueprints.get(engine.current_map_key)
    actor = battle.current_actor() if battle else None
    state: Dict[str, Any] = {
        "session_id": session_id,
        "current_map": {
            "key": engine.current_map_key,
            "name": map_info.name if map_info else engine.current_map_key,
        },
        "current_node": engine.current_node,
        "neighbors": engine.neighbors() if not battle else [],
        "in_battle": engine.in_battle(),
        "party": [_player_summary(member) for member in engine.player_party],
        "event_log": engine.event_log[-20:],
        "events": [_node_event_summary(event) for event in events or []],
        "saves": engine.list_saves(),
    }
    if battle:
        state["battle"] = {
            "current_actor": actor.name if actor else None,
            "current_actor_type": "player" if isinstance(actor, Player) else "enemy" if actor else None,
            "enemies": [_enemy_summary(enemy, idx) for idx, enemy in enumerate(battle.enemies, 1)],
            "actions": [
                {"kind": kind, "name": name, "label": kind if not name else f"{kind} {name}"}
                for kind, name in engine.list_player_actions()
            ],
        }
    else:
        state["shop"] = [_item_summary(item) for item in engine.shop.list_items()]
    return state


class AdventureHandler(BaseHTTPRequestHandler):
    server_version = "AdventureAPI/1.0"

    def _json(self, payload: Dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def _send_static(self, path: str) -> None:
        relative = path.lstrip("/") or "index.html"
        if relative.startswith("api/"):
            self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        file_path = (STATIC_DIR / relative).resolve()
        if not str(file_path).startswith(str(STATIC_DIR.resolve())) or not file_path.is_file():
            file_path = STATIC_DIR / "index.html"
        content = file_path.read_bytes()
        mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK.value)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib hook
        self._json({})

    def do_GET(self) -> None:  # noqa: N802 - stdlib hook
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._json({"ok": True})
            return
        if parsed.path == "/api/session":
            query = parse_qs(parsed.query)
            session_id = query.get("id", [""])[0]
            try:
                engine = STORE.get(session_id)
                self._json(describe_engine(engine, session_id))
            except KeyError as exc:
                self._json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
            return
        self._send_static(parsed.path)

    def do_POST(self) -> None:  # noqa: N802 - stdlib hook
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/session":
                data = self._read_json()
                session_id = STORE.create(str(data.get("name", "Hero")), str(data.get("class", "player")))
                self._json(describe_engine(STORE.get(session_id), session_id), HTTPStatus.CREATED)
                return

            data = self._read_json()
            session_id = str(data.get("session_id", ""))
            engine = STORE.get(session_id)
            if parsed.path == "/api/move":
                destination = str(data.get("node", "")).upper()
                events = engine.move_to(destination)
                self._json(describe_engine(engine, session_id, events))
                return
            if parsed.path == "/api/battle/action":
                event = engine.perform_player_action(
                    str(data.get("action", "attack")),
                    target_index=max(0, int(data.get("target_index", 0))),
                    name=data.get("name"),
                    actor_name=data.get("actor_name"),
                    target_kind=str(data.get("target_kind", "enemy")),
                    target_name=data.get("target_name"),
                )
                self._json(describe_engine(engine, session_id, [event]))
                return
            if parsed.path == "/api/shop/buy":
                item = engine.purchase_item(str(data.get("item", "")))
                event = NodeEvent("shop", payload=f"Purchased {item.name}")
                self._json(describe_engine(engine, session_id, [event]))
                return
            if parsed.path == "/api/save":
                slot = str(data.get("slot", "web")) or "web"
                engine.save_game(slot)
                event = NodeEvent("save", payload=f"Saved to {slot}")
                self._json(describe_engine(engine, session_id, [event]))
                return
            if parsed.path == "/api/load":
                slot = str(data.get("slot", ""))
                engine.load_game(slot)
                event = NodeEvent("load", payload=f"Loaded {slot}")
                self._json(describe_engine(engine, session_id, [event]))
                return
            if parsed.path == "/api/generate":
                size = data.get("size")
                event = engine.generate_new_map(size=int(size) if size else None)
                self._json(describe_engine(engine, session_id, [event]))
                return
            self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except (KeyError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args: Any) -> None:
        if os.environ.get("ADVENTURE_API_LOGS"):
            super().log_message(format, *args)


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), AdventureHandler)
    print(f"Serving adventure API and React client on http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the adventure game API and React front end")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
