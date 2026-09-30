# Notes from W6 (mcp)

## For the orchestrator — app.py wiring

`routes/mcp.py` exposes `mcp_bp` + the contract setters. In `app.py`:

```python
from routes.mcp import mcp_bp, set_emitter as set_mcp_emitter, \
    set_executor as set_mcp_executor

set_mcp_emitter(lambda event, payload: socketio.emit(event, payload))
set_mcp_executor(action_executor)
app.register_blueprint(mcp_bp)
limiter.exempt(mcp_bp)   # MCP clients may poll tools/call
```

Route is `/api/mcp` (full path on the blueprint, like agent_events — no
url_prefix needed).

## now_playing contract mismatch (W1)

The spec I was given said `services.now_playing.latest()` → last payload
dict or None. W1 shipped `snapshot()`, `latest_track()` and `available()`
instead — no `latest()`. My `get_now_playing` accepts any of
`latest`/`snapshot`/`latest_track` (first callable wins) plus `available()`,
so nothing needs to change; flagging so the contract doc/codebase stay
honest. Module-missing still returns an `isError` "unavailable" result.

## No module-level volume setter

`cross_platform_action` exposes `read_output_volume()` but no
`set_output_volume()` — the write path lives on
`CrossPlatformAction._volume_set`. `set_volume` instantiates
`CrossPlatformAction({'action':'volume_set','value':n})` directly, so it
works even before `set_executor` is wired.

## Decisions worth knowing

- Unknown tool name in `tools/call` → `-32602` (MCP spec SHOULD); bad tool
  *arguments* → `isError:true` result instead (keeps transport clean).
- Non-localhost without a valid Bearer → `403` when REQUIRE_AUTH is off,
  `401` when on. Localhost always passes.
- JSON-RPC error replies use HTTP 200 with the error object in the body
  (JSON-RPC-over-HTTP convention); 405/401/403 are transport-level.
- `SERVER_VERSION = '2.1.0'` is duplicated from app.py's `/api/health`
  (can't import app). Consider a shared constant during integration.
- `docs/mcp.md` documents the connect guide; no SSE / no stdio is stated
  there plainly — Claude Desktop needs `mcp-remote`, Cursor can use `url`.
