# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in VDock, please report it privately rather than opening a public issue:

- Open a [GitHub Security Advisory](https://github.com/ponya5/VDock2/security/advisories/new) (preferred), **or**
- Contact the maintainer directly via [LinkedIn](https://www.linkedin.com/in/daniel-shalom-13987a1a/) or through [github.com/ponya5](https://github.com/ponya5).

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

Never commit real `.env` files, API keys, or credentials. Use `.env.example` and `backend/.env.example` as templates — they contain placeholder values only. `.gitignore` already excludes `.env*` files and local data (`backend/data/config.json`, `backend/data/user_settings.json`, uploads, etc.).
