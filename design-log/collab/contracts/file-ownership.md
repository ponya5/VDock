# Contract — File ownership

Only the listed owner may write a file. Everything not listed belongs to the
orchestrator. If you need a change in a file you don't own, write it in
`messages/<your-slug>.md` and note it in your final report — do not edit.

## Orchestrator-owned (never touch)

- `backend/app.py`, `backend/requirements*.txt`
- `frontend/src/utils/screensaverLayout.ts`
- `frontend/src/components/ScreenSaver.vue`
- `frontend/src/views/SettingsView.vue`, `frontend/src/views/DashboardView.vue`
- `frontend/src/stores/settings.ts`, `frontend/src/stores/dashboard.ts`
  *(dashboard.ts shared exception: W7 may append its timer dispatch branch —
  see W7 row)*
- `frontend/src/composables/useUiCommands.ts`, `frontend/src/api/socket.ts`,
  `frontend/src/App.vue`, `frontend/src/main.ts`, `frontend/src/router/*`
- `design-log/README.md`, `AGENTS.md`, everything under `design-log/collab/`
  except your own `messages/<slug>.md` and your STATUS.md row
- Any existing test file not listed below (if a test breaks because the
  contract changed, fix the test only if you own the feature that changed
  the contract; otherwise flag it)

## W1 — now-playing (DL-116)

- `backend/services/now_playing.py` (new)
- `backend/routes/now_playing.py` (new)
- `backend/tests/test_now_playing.py` (new)
- `frontend/src/services/nowPlaying.ts` (new)
- `frontend/src/components/screensaver/NowPlayingWidget.vue` (new)
- `frontend/src/tests/now-playing.test.ts` (new, optional)
- `design-log/DL-116-now-playing-smtc.md` (new)

## W2 — spectrum (DL-117)

- `backend/services/audio_spectrum.py` (new)
- `backend/tests/test_audio_spectrum.py` (new)
- `frontend/src/services/audioSpectrum.ts` (new)
- `frontend/src/components/screensaver/SpectrumWidget.vue` (new)
- `design-log/DL-117-spectrum-screensaver.md` (new)

## W3 — system-stats (DL-118)

- `frontend/src/composables/useSystemStats.ts` (new)
- `frontend/src/components/screensaver/SystemStatsWidget.vue` (new)
- `frontend/src/tests/system-stats-widget.test.ts` (new, optional)
- `design-log/DL-118-system-stats-widget.md` (new)

## W4 — notification (DL-119)

- `backend/routes/agent_events.py` (edit)
- `frontend/src/services/agentAlerts.ts` (edit)
- `frontend/src/components/AgentAlertOverlay.vue` (edit)
- `frontend/src/components/AgentWaitingDock.vue` (new)
- `frontend/src/components/NotificationCenter.vue` (edit, only if needed)
- `backend/tests/test_agent_state_events.py` (edit — keep it green)
- `frontend/src/tests/notification-panel.test.ts` (new)
- `design-log/DL-119-notification-to-panel.md` (new)

## W5 — triggers (DL-120)

- `backend/services/triggers.py` (new)
- `backend/routes/triggers.py` (new)
- `backend/tests/test_triggers.py` (new)
- `frontend/src/services/triggersApi.ts` (new)
- `frontend/src/components/settings/TriggersPanel.vue` (new)
- `design-log/DL-120-triggers-schedules.md` (new)

## W6 — mcp (DL-121)

- `backend/routes/mcp.py` (new)
- `backend/tests/test_mcp.py` (new)
- `docs/mcp.md` (new)
- `design-log/DL-121-mcp-server.md` (new)

## W7 — timer-rules (DL-122)

- `backend/actions/catalog.py` (edit — add entries only)
- `backend/models/button.py` (edit — add `rules` field only)
- `backend/tests/test_catalog.py` (edit only if your catalog changes require)
- `frontend/src/types/index.ts` (edit — add action-type union entries +
  Button.rules typing)
- `frontend/src/stores/dashboard.ts` (edit — append the timer dispatch branch
  only; do not refactor)
- `frontend/src/services/timerButtons.ts`, `frontend/src/services/buttonRules.ts`,
  `frontend/src/services/conditionalState.ts` (new)
- `frontend/src/components/TimerButtonFace.vue` (new)
- `frontend/src/components/DeckButton.vue` (edit — mount timer face +
  rule-patch application)
- `frontend/src/components/ButtonEditor.vue` (edit — timer config +
  conditional-style sub-section)
- `frontend/src/tests/timer-buttons.test.ts`,
  `frontend/src/tests/button-rules.test.ts` (new)
- `design-log/DL-122-timer-buttons-conditional-ui.md` (new)
