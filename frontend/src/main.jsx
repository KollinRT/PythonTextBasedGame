import React, { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `Request failed with ${response.status}`);
  }
  return data;
}

function StatBar({ label, value, max, tone = 'hp' }) {
  const pct = max ? Math.max(0, Math.min(100, Math.round((value / max) * 100))) : 0;
  return (
    <div className="statbar">
      <span>{label}: {value}/{max}</span>
      <div className="track"><div className={`fill ${tone}`} style={{ width: `${pct}%` }} /></div>
    </div>
  );
}

function EventFeed({ events = [], log = [] }) {
  const eventLines = events.flatMap((event) => [event.payload, ...(event.details || [])].filter(Boolean));
  const lines = eventLines.length ? eventLines : log;
  return (
    <section className="panel feed">
      <h2>Adventure Log</h2>
      <ol>
        {lines.slice(-12).map((line, index) => <li key={`${line}-${index}`}>{line}</li>)}
      </ol>
    </section>
  );
}

function App() {
  const [state, setState] = useState(null);
  const [name, setName] = useState('Hero');
  const [playerClass, setPlayerClass] = useState('player');
  const [sessionInput, setSessionInput] = useState('');
  const [slot, setSlot] = useState('slot1');
  const [customAction, setCustomAction] = useState('attack');
  const [targetIndex, setTargetIndex] = useState(1);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const hero = state?.hero;
  const inBattle = Boolean(state?.battle);
  const currentActorIsPlayer = state?.battle?.current_actor_type && state.battle.current_actor_type !== 'Enemy';
  const visibleEvents = useMemo(() => state?.events || [], [state]);

  async function run(work) {
    setBusy(true);
    setError('');
    try {
      setState(await work());
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function startGame() {
    run(() => api('/sessions', {
      method: 'POST',
      body: JSON.stringify({ name, player_class: playerClass }),
    }));
  }

  function loadSession() {
    if (!sessionInput.trim()) return;
    run(() => api(`/sessions/${sessionInput.trim()}`));
  }

  function move(destination) {
    run(() => api(`/sessions/${state.session_id}/move`, {
      method: 'POST',
      body: JSON.stringify({ destination }),
    }));
  }

  function battleAction(action, actionName = null) {
    run(() => api(`/sessions/${state.session_id}/battle/action`, {
      method: 'POST',
      body: JSON.stringify({ action, name: actionName, target_index: Number(targetIndex) || 1 }),
    }));
  }

  function usePotion(potionName) {
    run(() => api(`/sessions/${state.session_id}/potion`, {
      method: 'POST',
      body: JSON.stringify({ name: potionName }),
    }));
  }

  function saveGame() {
    run(() => api(`/sessions/${state.session_id}/save`, {
      method: 'POST',
      body: JSON.stringify({ slot }),
    }));
  }

  function loadGame() {
    run(() => api(`/sessions/${state.session_id}/load`, {
      method: 'POST',
      body: JSON.stringify({ slot }),
    }));
  }

  function generateMap() {
    run(() => api(`/sessions/${state.session_id}/maps/generate`, {
      method: 'POST',
      body: JSON.stringify({}),
    }));
  }

  if (!state) {
    return (
      <main className="shell centered">
        <section className="hero-card">
          <p className="eyebrow">Online-ready adventure client</p>
          <h1>Python Text Adventure</h1>
          <p>Create a session, share the session id with a friend, and drive the same API-backed adventure from the browser.</p>
          <div className="form-grid">
            <label>Hero name<input value={name} onChange={(e) => setName(e.target.value)} /></label>
            <label>Class
              <select value={playerClass} onChange={(e) => setPlayerClass(e.target.value)}>
                <option value="player">Player</option>
                <option value="mage">Mage</option>
                <option value="ranger">Ranger</option>
                <option value="cleric">Cleric</option>
              </select>
            </label>
          </div>
          <button disabled={busy} onClick={startGame}>Start new adventure</button>
          <div className="join-row">
            <input placeholder="Existing session id" value={sessionInput} onChange={(e) => setSessionInput(e.target.value)} />
            <button disabled={busy} onClick={loadSession}>Join</button>
          </div>
          {error && <p className="error">{error}</p>}
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Session {state.session_id}</p>
          <h1>{state.map.name}</h1>
          <p>Node {state.map.current_node} · Share this session id so friends can connect to the same running game.</p>
        </div>
        <button onClick={() => navigator.clipboard?.writeText(state.session_id)}>Copy session id</button>
      </header>

      {error && <div className="error banner">{error}</div>}

      <div className="grid-layout">
        <section className="panel">
          <h2>Party</h2>
          <div className="party-list">
            {state.party.map((member) => (
              <article className="member" key={member.name}>
                <strong>{member.name}</strong><span>{member.type} · Lv {member.level}</span>
                <StatBar label="HP" value={member.hp} max={member.max_hp} />
                {'mp' in member && <StatBar label="MP" value={member.mp} max={member.max_mp} tone="mp" />}
                {'focus' in member && <StatBar label="Focus" value={member.focus} max={member.max_focus} tone="focus" />}
              </article>
            ))}
          </div>
        </section>

        <section className="panel action-panel">
          <h2>{inBattle ? 'Battle' : 'Explore'}</h2>
          {!inBattle && (
            <>
              <p>Choose a neighboring node to travel.</p>
              <div className="button-row">
                {state.map.neighbors.map((node) => <button disabled={busy} key={node} onClick={() => move(node)}>Move {node}</button>)}
              </div>
              <button className="secondary" disabled={busy} onClick={generateMap}>Discover frontier map</button>
            </>
          )}
          {inBattle && (
            <>
              <p>Current turn: <strong>{state.battle.current_actor}</strong></p>
              <div className="enemy-list">
                {state.battle.enemies.map((enemy) => (
                  <button className={targetIndex === enemy.index ? 'target selected' : 'target'} key={enemy.index} onClick={() => setTargetIndex(enemy.index)}>
                    {enemy.index}. {enemy.name} · {enemy.hp}/{enemy.max_hp} HP
                  </button>
                ))}
              </div>
              <div className="button-row">
                {state.battle.actions.map((action, idx) => (
                  <button disabled={busy || !currentActorIsPlayer} key={`${action.label}-${idx}`} onClick={() => battleAction(action.kind, action.name)}>{action.label}</button>
                ))}
              </div>
              <div className="join-row">
                <input value={customAction} onChange={(e) => setCustomAction(e.target.value)} placeholder="attack, spell, ability" />
                <button disabled={busy || !currentActorIsPlayer} onClick={() => battleAction(customAction)}>Send</button>
              </div>
            </>
          )}
        </section>

        <section className="panel">
          <h2>Inventory</h2>
          <p>Gold: <strong>{hero.gp}</strong> · EXP: <strong>{hero.exp}</strong></p>
          <h3>Potions</h3>
          <div className="button-row stacked">
            {state.potions.length ? state.potions.map((potion) => (
              <button disabled={busy || inBattle} key={potion.name} onClick={() => usePotion(potion.name)}>{potion.name} ×{potion.quantity}</button>
            )) : <span>No potions</span>}
          </div>
          <h3>Save slots</h3>
          <div className="join-row"><input value={slot} onChange={(e) => setSlot(e.target.value)} /><button onClick={saveGame}>Save</button><button onClick={loadGame}>Load</button></div>
          <small>Known slots: {state.saves.length ? state.saves.join(', ') : 'none'}</small>
        </section>

        <EventFeed events={visibleEvents} log={state.event_log} />
      </div>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
