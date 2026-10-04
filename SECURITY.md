# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in VDock, please report it privately rather than opening a public issue:

- Open a [GitHub Security Advisory](https://github.com/ponya5/VDock/security/advisories/new) (preferred), **or**
- Email **ponya81@gmail.com** if you can't or don't want to use GitHub, **or**
- Report it through [GitHub Issues](https://github.com/ponya5/VDock/issues) only if it is not sensitive.

Please include:

- A description of the vulnerability and its potential impact
- Steps to reproduce (a minimal example is ideal)
- The version/commit you tested against

We'll acknowledge reports as soon as possible and aim to release a fix promptly for confirmed issues. Please give us a reasonable amount of time to address the issue before any public disclosure.

## Supported Versions

VDock is under active development on the `main` branch. Only the latest version is supported with security fixes.

## Security-Relevant Configuration

VDock is designed to run **locally, on a trusted machine**, with no login screen in the UI by default. A few settings materially affect its security posture — review them before exposing the app beyond `localhost`:

| Setting (`backend/.env`) | Default | Notes |
|---|---|---|
| `REQUIRE_AUTH` | `False` | The UI never sends a token; only enable this if you're calling the API directly with your own client. |
| `AUTH_PASSWORD` | — | Change this from the example value if you enable `REQUIRE_AUTH`. |
| `ALLOW_LAN` | `False` | Keep this `False` unless you intentionally want VDock reachable from other devices on your network. |
| `USE_SSL` | `False` | Enable and provide real certificates if exposing VDock outside `localhost`. |
| `ALLOW_COMMAND_EXECUTION` | `False` | Lets configured buttons run shell commands/hotkeys. Only enable this if you trust every profile/button loaded into VDock — a malicious or corrupted profile could otherwise run arbitrary commands. |
| `REQUIRE_COMMAND_CONFIRMATION` | `True` | Adds a confirmation prompt before command-execution actions run; recommended to leave enabled. |

**Do not** expose a VDock instance directly to the public internet without authentication, SSL, and a hardened `SECRET_KEY`/`AUTH_PASSWORD`. It's built as a personal, local control panel, not a multi-tenant service.

## Secrets & Environment Files

Never commit real `.env` files, API keys, or credentials. Use `backend/.env.example` and `frontend/.env.example` as templates — they contain placeholder values only. `.gitignore` already excludes `.env*` files and local data (`backend/data/config.json`, `backend/data/user_settings.json`, uploads, etc.).

## Running on your network (phones, tablets, a 7" panel)

- **Set a deck password before you turn on Allow LAN** (Settings, Devices & network). Without one, anyone on the same Wi-Fi can press your keys, type into agent sessions and approve agent permission prompts. VDock logs a warning at startup when LAN is on and no password is set.
- A device on your network can do everything the deck can do: run actions, open apps, send keystrokes. Treat the LAN like the keyboard.
- `DEBUG=True` is never safe together with Allow LAN (it exposes the Werkzeug debugger). VDock refuses to start with that combination.
- API keys (`GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `WEATHERAPI_KEY`) live only in the backend `.env` (`backend/.env` from source, `<data dir>/.env` in the installed app). They are never sent to the browser, never logged, and redacted from CLI output.
- `SECRET_KEY` is generated on first start and saved to the same file; a published example key is replaced automatically.
- Found a problem? See "Reporting a Vulnerability" above.
- Keys can be saved or removed in Settings > Integrations > Accounts & keys (`PUT/DELETE /api/config/integrations/<id>`). The endpoint accepts only the three allowlisted names, is refused for any non-localhost request, requires the deck password when auth is on, validates the value, writes the env file atomically and never returns or logs the value.
