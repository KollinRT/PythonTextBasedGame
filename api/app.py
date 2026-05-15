"""HTTP API for the text adventure game.

The API keeps the existing :class:`game_logic.core.GameEngine` as the source of
truth and exposes small JSON endpoints that web clients can call.  Sessions are
held in memory so multiple browsers can play at the same time; save slots still
use the existing SQLite persistence layer.
"""

from __future__ import annotations

from dataclasses import asdict
import os
import secrets
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from classes.classes import Enemy, Mage, Player, Ranger
from game_logic.core import GameEngine, NodeEvent, startGame

PlayerClass = Literal["player", "mage", "ranger", "cleric"]


class StartGameRequest(BaseModel):
    """Payload used to create a browser-playable game session."""

    name: str = Field(default="Hero", min_length=1, max_length=40)
    player_class: PlayerClass = "player"


class MoveRequest(BaseModel):
    destination: str = Field(min_length=1, max_length=20)


class BattleActionRequest(BaseModel):
    action: str = Field(default="attack", min_length=1, max_length=20)
    name: Optional[str] = None
    target_index: int = 0
    actor_name: Optional[str] = None
    target_kind: str = "enemy"
    target_name: Optional[str] = None


class PotionRequest(BaseModel):
    name: str = Field(min_length=1)


class SaveRequest(BaseModel):
    slot: str = Field(default="slot1", min_length=1, max_length=40)


class LoadRequest(BaseModel):
    slot: str = Field(min_length=1, max_length=40)


class GenerateMapRequest(BaseModel):
    size: Optional[int] = Field(default=None, ge=5, le=40)


class PurchaseRequest(BaseModel):
    item_name: str = Field(min_length=1)


_sessions: Dict[str, GameEngine] = {}

app = FastAPI(
    title="Python Text Adventure API",
    version="1.0.0",
    description="JSON API for starting, exploring, fighting, saving, and loading text adventure sessions.",
)
cors_origins = [origin.strip() for origin in os.getenv("ADVENTURE_CORS_ORIGINS", "*").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials="*" not in cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _new_session_id() -> str:
    return secrets.token_urlsafe(12)


def _engine_or_404(session_id: str) -> GameEngine:
    engine = _sessions.get(session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Game session not found")
    return engine


def _item_to_dict(item: Any) -> Dict[str, Any]:
    if hasattr(item, "to_dict"):
        return item.to_dict()
    return dict(item)


def _character_to_dict(character: Player) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "name": character.name,
        "type": character.__class__.__name__,
        "level": character.level,
        "hp": character.hp,
        "max_hp": character.max_hp,
        "dmg": character.dmg,
        "exp": character.exp,
        "gp": character.gp,
        "is_alive": character.is_alive(),
        "role": getattr(character, "role", "hero" if not character.is_companion else "companion"),
    }
    if isinstance(character, Mage):
        data.update({"mp": character.mp, "max_mp": character.max_mp})
    if isinstance(character, Ranger):
        data.update({"focus": character.focus, "max_focus": character.max_focus})
    return data


def _enemy_to_dict(enemy: Enemy, index: int) -> Dict[str, Any]:
    return {
        "index": index,
        "name": enemy.name,
        "level": enemy.level,
        "hp": enemy.hp,
        "max_hp": enemy.max_hp,
        "dmg": enemy.dmg,
        "is_alive": enemy.is_alive(),
    }


def _node_event_to_dict(event: NodeEvent) -> Dict[str, Any]:
    return asdict(event)


def _battle_state(engine: GameEngine) -> Optional[Dict[str, Any]]:
    if not engine.battle:
        return None
    actor = engine.battle.current_actor()
    return {
        "current_actor": actor.name if actor else None,
        "current_actor_type": actor.__class__.__name__ if actor else None,
        "enemies": [_enemy_to_dict(enemy, idx) for idx, enemy in enumerate(engine.battle.enemies, 1)],
        "actions": [
            {"kind": kind, "name": name, "label": kind if name is None else f"{kind} {name}"}
            for kind, name in engine.list_player_actions()
        ],
    }


def _state(engine: GameEngine, session_id: str, events: Optional[List[NodeEvent]] = None) -> Dict[str, Any]:
    map_info = engine.map_blueprints.get(engine.current_map_key)
    hero = engine.hero
    return {
        "session_id": session_id,
        "map": {
            "key": engine.current_map_key,
            "name": map_info.name if map_info else engine.current_map_key,
            "current_node": engine.current_node,
            "neighbors": engine.neighbors(),
        },
        "party": [_character_to_dict(member) for member in engine.player_party],
        "hero": _character_to_dict(hero) if hero else None,
        "inventory": [_item_to_dict(item) for item in hero.sort_inventory()] if hero else [],
        "potions": [_item_to_dict(item) for item in hero.potions.values()] if hero else [],
        "shop": [_item_to_dict(item) for item in engine.shop.inventory.values()],
        "battle": _battle_state(engine),
        "events": [_node_event_to_dict(event) for event in events or []],
        "event_log": engine.event_log[-20:],
        "saves": engine.list_saves(),
    }


def _api_error(exc: Exception) -> HTTPException:
    if isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, (RuntimeError, ValueError)):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Unexpected server error")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/sessions")
def start_session(payload: StartGameRequest) -> Dict[str, Any]:
    session_id = _new_session_id()
    engine = GameEngine()
    engine.start_new_game(startGame(payload.name.strip(), payload.player_class))
    _sessions[session_id] = engine
    return _state(engine, session_id)


@app.get("/sessions/{session_id}")
def get_session(session_id: str) -> Dict[str, Any]:
    engine = _engine_or_404(session_id)
    return _state(engine, session_id)


@app.post("/sessions/{session_id}/move")
def move(session_id: str, payload: MoveRequest) -> Dict[str, Any]:
    engine = _engine_or_404(session_id)
    try:
        events = engine.move_to(payload.destination.upper())
    except Exception as exc:  # FastAPI converts this to the correct HTTP error below.
        raise _api_error(exc) from exc
    return _state(engine, session_id, events)


@app.post("/sessions/{session_id}/battle/action")
def battle_action(session_id: str, payload: BattleActionRequest) -> Dict[str, Any]:
    engine = _engine_or_404(session_id)
    try:
        event = engine.perform_player_action(
            payload.action,
            target_index=max(0, payload.target_index - 1),
            name=payload.name,
            actor_name=payload.actor_name,
            target_kind=payload.target_kind,
            target_name=payload.target_name,
        )
    except Exception as exc:
        raise _api_error(exc) from exc
    return _state(engine, session_id, [event])


@app.post("/sessions/{session_id}/potion")
def use_potion(session_id: str, payload: PotionRequest) -> Dict[str, Any]:
    engine = _engine_or_404(session_id)
    try:
        engine.player_party[0].use_potion(payload.name)
        event = NodeEvent("potion", payload=f"Used {payload.name}")
    except Exception as exc:
        raise _api_error(exc) from exc
    return _state(engine, session_id, [event])


@app.post("/sessions/{session_id}/shop/purchase")
def purchase(session_id: str, payload: PurchaseRequest) -> Dict[str, Any]:
    engine = _engine_or_404(session_id)
    try:
        item = engine.purchase_item(payload.item_name)
        event = NodeEvent("shop", payload=f"Purchased {item.name}")
    except Exception as exc:
        raise _api_error(exc) from exc
    return _state(engine, session_id, [event])


@app.post("/sessions/{session_id}/maps/generate")
def generate_map(session_id: str, payload: GenerateMapRequest) -> Dict[str, Any]:
    engine = _engine_or_404(session_id)
    try:
        event = engine.generate_new_map(size=payload.size)
    except Exception as exc:
        raise _api_error(exc) from exc
    return _state(engine, session_id, [event])


@app.post("/sessions/{session_id}/save")
def save(session_id: str, payload: SaveRequest) -> Dict[str, Any]:
    engine = _engine_or_404(session_id)
    try:
        engine.save_game(payload.slot)
        event = NodeEvent("save", payload=f"Game saved to '{payload.slot}'.")
    except Exception as exc:
        raise _api_error(exc) from exc
    return _state(engine, session_id, [event])


@app.post("/sessions/{session_id}/load")
def load(session_id: str, payload: LoadRequest) -> Dict[str, Any]:
    engine = _engine_or_404(session_id)
    try:
        engine.load_game(payload.slot)
        event = NodeEvent("load", payload=f"Loaded save '{payload.slot}'.")
    except Exception as exc:
        raise _api_error(exc) from exc
    return _state(engine, session_id, [event])
