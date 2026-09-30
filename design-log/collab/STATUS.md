# Worker status board

Each worker updates ONLY its own row. States:
`queued → working → done | blocked`. Add a short note on transitions.

| Worker | Feature | DL | State | Note |
|---|---|---|---|---|
| W1 now-playing | SMTC monitor + widget | DL-116 | done | All deliverables built; 12 backend + 10 frontend tests green; app.py wiring notes in messages/now-playing.md |
| W2 spectrum | Loopback FFT + Winamp widget | DL-117 | done | 21 backend tests green; live-verified on real loopback; patched soundcard 0.4.6 PROPVARIANT heap bug (see messages/spectrum.md) |
| W3 system-stats | System stats widget | DL-118 | done | Composable + widget + 15 tests green; type-check clean |
| W4 notification | Multi-agent notification-to-panel | DL-119 | done | per-source alerts + waiting dock; 72 backend / 48 frontend tests green; vue-tsc clean; navigate-scene listener needs orchestrator wiring |
| W5 triggers | Triggers/schedules engine | DL-120 | done | 39 backend tests pass; panel + api wrapper built; app.py wiring noted in messages/triggers.md |
| W6 mcp | MCP server endpoint | DL-121 | done | 40 tests green; needs app.py wiring (mcp_bp + set_emitter/set_executor) |
| W7 timer-rules | Timer buttons + conditional UI | DL-122 | done | Engine + face + rules + editor built; 27 new frontend tests green; backend suite 1057 green; no backend wiring needed; notes in messages/timer-rules.md (property8 failure is pre-existing, SettingsView.vue) |

## Orchestrator integration — complete

- app.py: blueprints registered (now_playing, triggers, mcp), emitters/executor/spawners wired, services started via socketio.start_background_task; `import app` clean.
- requirements.txt: winrt-* wheels + soundcard + numpy pinned Windows-only (installed into backend/venv; winsdk has no cp313 wheel — lazy shim tries winsdk then winrt).
- Screensaver: nowplaying/spectrum/systemstats IDs registered in screensaverLayout.ts + mounted in ScreenSaver.vue (desktop-only, layout edit + clamp covered).
- Settings: widget toggles + descriptions, TriggersPanel + MCP endpoint info on Integrations tab, search index entries, property8 font fix.
- Frontend wiring: initTriggerEvents() in App.vue (navigate_scene → setScene, trigger_fired → notifications, vdock:navigate-scene from AgentWaitingDock).
- actionCatalog fallback narrowed (time_timer/time_stopwatch are interactive); DashboardView compact mode covers time_stopwatch.
- Verified: backend 1057 pass (+112 new-feature files re-run under backend/venv), frontend 433 pass, `npm run build` clean — dist bundle updated for the panel.
- SMTC binding resolved live under backend/venv (winrt 3.2.1, `supported: True`).
