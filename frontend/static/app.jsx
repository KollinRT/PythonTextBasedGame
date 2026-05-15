const { useEffect, useMemo, useState } = React;

const api = async (path, body) => {
  const options = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : {};
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Request failed");
  return payload;
};

function HealthBar({ value, max }) {
  const percent = Math.max(0, Math.min(100, Math.round((value / Math.max(1, max)) * 100)));
  return <div className="hpbar"><span style={{ width: `${percent}%` }} /></div>;
}

function StartScreen({ onStart, error }) {
  const [name, setName] = useState("Hero");
  const [klass, setKlass] = useState("player");
  const [joinId, setJoinId] = useState(new URLSearchParams(location.search).get("session") || "");
  return (
    <section className="card login stack">
      <span className="badge">Online API prototype</span>
      <h2>Start or join an adventure</h2>
      <p className="muted">Create a hosted session, send the share link to friends, and everyone can push the same party forward from a browser.</p>
      {error && <div className="error">{error}</div>}
      <label className="stack">Hero name<input value={name} onChange={(event) => setName(event.target.value)} /></label>
      <label className="stack">Class<select value={klass} onChange={(event) => setKlass(event.target.value)}>
        <option value="player">Player</option>
        <option value="mage">Mage</option>
        <option value="ranger">Ranger</option>
        <option value="cleric">Cleric</option>
      </select></label>
      <div className="row"><button onClick={() => onStart({ name, class: klass })}>Create session</button></div>
      <label className="stack">Join session id<input placeholder="Paste a session id" value={joinId} onChange={(event) => setJoinId(event.target.value)} /></label>
      <button className="secondary" disabled={!joinId.trim()} onClick={() => onStart(null, joinId.trim())}>Join shared game</button>
    </section>
  );
}

function PartyPanel({ party }) {
  return <section className="card"><h3 className="panel-title">Party</h3><div className="stat-list">
    {party.map((member) => <article className="stat-card" key={member.name}>
      <strong>{member.name}</strong> <span className="muted">{member.class}{member.role ? ` · ${member.role}` : ""}</span>
      <div className="muted">Lv {member.level} · {member.gp} gp · {member.dmg} dmg</div>
      <div>{member.hp}/{member.max_hp} HP {member.max_mp ? `· ${member.mp}/${member.max_mp} MP` : ""}</div>
      <HealthBar value={member.hp} max={member.max_hp} />
    </article>)}
  </div></section>;
}

function BattlePanel({ state, send }) {
  const battle = state.battle;
  const [target, setTarget] = useState(0);
  const actions = battle?.actions?.length ? battle.actions : [{ kind: "attack", name: null, label: "attack" }];
  return <section className="card stack">
    <h3 className="panel-title">Battle</h3>
    <p><span className="badge">Turn</span> {battle.current_actor || "Waiting"}</p>
    <div className="stat-list">
      {battle.enemies.map((enemy, index) => <button className="stat-card enemy" key={enemy.name} onClick={() => setTarget(index)} style={{ textAlign: "left", outline: target === index ? "2px solid #79ffe1" : "none" }}>
        <strong>{enemy.index}. {enemy.name}</strong> <span className="muted">Lv {enemy.level}</span>
        <div>{enemy.hp}/{enemy.max_hp} HP</div><HealthBar value={enemy.hp} max={enemy.max_hp} />
      </button>)}
    </div>
    <div className="actions">
      {actions.map((action) => <button key={`${action.kind}-${action.name || "basic"}`} disabled={battle.current_actor_type !== "player"} onClick={() => send("/api/battle/action", { action: action.kind, name: action.name, target_index: target })}>{action.label}</button>)}
    </div>
  </section>;
}

function WorldPanel({ state, send }) {
  const [slot, setSlot] = useState("web");
  return <section className="card stack">
    <div><span className="badge">{state.current_map.name}</span><div className="map-node">{state.current_node}</div></div>
    <p className="muted">Choose a neighboring node to move. Shops, fishing spots, allies, portals, and battles are handled by the API.</p>
    <div className="actions">{state.neighbors.map((node) => <button key={node} onClick={() => send("/api/move", { node })}>Move {node}</button>)}</div>
    <div className="row"><button className="secondary" onClick={() => send("/api/generate", {})}>Discover frontier map</button></div>
    <h3 className="panel-title">Shop</h3>
    <div className="actions">{(state.shop || []).slice(0, 6).map((item) => <button className="secondary" key={item.name} onClick={() => send("/api/shop/buy", { item: item.name })}>{item.name} · {item.value}gp</button>)}</div>
    <div className="row"><input style={{ maxWidth: 180 }} value={slot} onChange={(event) => setSlot(event.target.value)} /><button className="secondary" onClick={() => send("/api/save", { slot })}>Save</button><button className="secondary" onClick={() => send("/api/load", { slot })}>Load</button></div>
  </section>;
}

function EventLog({ state }) {
  const recentEvents = useMemo(() => (state.events || []).flatMap((event) => [event.payload, ...(event.details || [])].filter(Boolean)), [state]);
  return <section className="card log"><h3 className="panel-title">Adventure log</h3>
    {[...recentEvents, ...(state.event_log || []).slice().reverse()].slice(0, 28).map((line, index) => <div className="event" key={`${line}-${index}`}>{line}</div>)}
  </section>;
}

function Game() {
  const [state, setState] = useState(null);
  const [error, setError] = useState("");
  const start = async (character, joinId) => {
    try {
      setError("");
      const next = joinId ? await api(`/api/session?id=${encodeURIComponent(joinId)}`) : await api("/api/session", character);
      history.replaceState(null, "", `?session=${next.session_id}`);
      setState(next);
    } catch (err) { setError(err.message); }
  };
  const send = async (path, body) => {
    try { setError(""); setState(await api(path, { session_id: state.session_id, ...body })); }
    catch (err) { setError(err.message); }
  };
  useEffect(() => {
    const session = new URLSearchParams(location.search).get("session");
    if (session) start(null, session);
  }, []);
  return <div className="app-shell">
    <header className="hero"><h1>Python Text Adventure</h1><p>Now playable through a tiny JSON API with a React front end. Host it, share the session id, and let friends collaborate on the same run.</p></header>
    {!state ? <StartScreen onStart={start} error={error} /> : <>
      {error && <div className="error">{error}</div>}
      <p className="muted">Share: <span className="share">{location.origin + location.pathname + `?session=${state.session_id}`}</span></p>
      <div className="grid"><div className="stack">{state.in_battle ? <BattlePanel state={state} send={send} /> : <WorldPanel state={state} send={send} />}<EventLog state={state} /></div><PartyPanel party={state.party} /></div>
    </>}
  </div>;
}

ReactDOM.createRoot(document.getElementById("root")).render(<Game />);
