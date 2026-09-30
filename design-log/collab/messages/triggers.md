# W5 triggers — notes for the orchestrator

## app.py wiring needed (I can't touch it)

```python
from services import triggers as triggers_service
from routes.triggers import triggers_bp

# with the other service wiring:
triggers_service.set_emitter(lambda event, payload: socketio.emit(event, payload))
triggers_service.set_spawner(socketio.start_background_task)  # threading-mode emit rule applies
triggers_service.set_executor(action_executor)

# with the other blueprints:
app.register_blueprint(triggers_bp)
limiter.exempt(triggers_bp)  # fire/<key> is localhost-only; CRUD is low-volume UI traffic

# under __main__, next to volume_monitor.start():
triggers_service.start()
```

`routes.triggers.set_emitter(fn)` also exists and delegates to the service —
either wiring point works; setting both is harmless (plain assignment).

## Frontend mounting

`frontend/src/components/settings/TriggersPanel.vue` renders a
`<section class="panel">` root — drop it inside any `.col` in
SettingsView. It needs nothing injected (talks to `/api/triggers` directly,
subscribes `trigger_fired` itself). A natural home is a new "Automation"
group; suggest mounting it near the notifications section.

## Contract usage

- Emits `trigger_fired {id,label,ok,detail,ts}` on every fire (including
  failures and `/test` fires).
- `switch_scene` actions emit `navigate_scene {scene}` — orchestrator's
  frontend listener consumes it (per socket contract, case-insensitive
  scene-name match).
- `show_notification` actions emit `panel_notification {source:'trigger',
  title,message,ts}` — W4's `agentAlerts.ts` consumes these into the
  notification store/bell.
- `POST /api/triggers/fire/<key>` is localhost-only, no auth — same model
  as `/api/agent-events`. W6's MCP `show_notification`/`switch_scene`
  tools overlap in effect but stay independent.

## Semantics worth knowing

- Polled events fire on observed **entry only**; the engine's first
  observation is a baseline (never fires), and editing a trigger
  re-baselines it. Time triggers fire once per matching minute
  (`days:[]`/absent = daily, 0=Monday).
- Webhook `fired` counts only *enabled* matching triggers; `POST
  /api/triggers/<id>/test` ignores `enabled`.
- Store file: `DATA_DIR/triggers.json`, `{'triggers': [...]}` — a bare
  list also loads (tolerated on read).
