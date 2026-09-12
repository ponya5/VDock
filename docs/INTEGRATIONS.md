# AI & Developer Integrations

VDock ships four integration packs — Claude, GitHub, Cursor and GitHub Copilot —
plus a generic HTTP action that covers everything else.

**None of them are required.** Each pack detects what it can use at startup. An
action it cannot run is listed in the picker but greyed out, with the reason on
hover, instead of failing when you press it.

---

## Quick answer: what do I need to install?

| You want | You need | Notes |
|---|---|---|
| Claude Code prompts, slash commands, sessions | the `claude` CLI | Uses your existing login. No API key. |
| "Ask Claude (API)" | `ANTHROPIC_API_KEY` + `pip install anthropic` | Optional. The CLI actions do not need this. |
| PRs, issues, checks, workflow runs | the `gh` CLI, logged in | `gh auth login`. No token stored by VDock. |
| Live PR count / CI status **on the button** | `GITHUB_TOKEN` | Only the polling widgets need this. |
| Cursor and Copilot actions | the editor itself | Keystroke-driven; nothing to install. |
| Discord, Slack, n8n, Zapier, Home Assistant… | nothing | Use the **HTTP Request** action. |

---

## Claude

### Claude Code CLI (recommended)

Uses the `claude` CLI and your existing login.

| Action | What it does |
|---|---|
| **Ask Claude Code** | Runs a prompt in your project and returns the answer |
| **Claude Slash Command** | Runs `/code-review`, `/commit`, or any slash command |
| **Open Claude Code** | Opens an interactive session in a terminal, optionally resuming |

Prompts support placeholders, so one button works across projects:

| Placeholder | Becomes |
|---|---|
| `{clipboard}` | Current clipboard contents |
| `{repo}` | Absolute path of the resolved project |
| `{project}` | Project folder name |
| `{branch}` | Current git branch |

Example prompt: `Review the staged changes in {repo} and suggest a commit message`

### Claude API

**Ask Claude (API)** calls the Messages API directly and puts the answer on your
clipboard. Needs `ANTHROPIC_API_KEY` in `backend/.env` and the `anthropic`
package (`pip install anthropic`). Defaults to `claude-opus-5` at low effort, to
keep a button press responsive.

### Desktop / web

**Open Claude** launches the desktop app or opens claude.ai.

---

## GitHub

### `gh` CLI actions

These reuse your existing `gh auth login`; VDock stores no credential.

`gh_pr_list`, `gh_pr_create`, `gh_pr_checkout`, `gh_pr_view`, `gh_pr_checks`,
`gh_issue_list`, `gh_issue_create`, `gh_run_list`, `gh_run_rerun`, `gh_status`.

> **Create Pull Request** defaults to opening the PR form in your browser rather
> than submitting immediately — a single button press should not open a PR.
> Turn that off in the button's config if you want the one-tap version.

### Live widgets

These poll the REST API and need `GITHUB_TOKEN` (scopes: `repo`,
`notifications`). They render a badge on the button face:

| Widget | Shows |
|---|---|
| **Open PR Count** | Number of open PRs, or only those awaiting your review |
| **CI Status** | Current branch's latest workflow run — ✓ green, ✕ red, … running |
| **Unread Notifications** | Unread GitHub notification count |

### Which repository?

VDock resolves the target repo in this order:

1. an explicit path set on the button;
2. **the project in your focused editor** — the folder name is read from the
   window title of Cursor / VS Code / JetBrains, then matched against a real
   directory;
3. `VDOCK_DEFAULT_REPO_PATH` from `backend/.env`;
4. the process working directory.

Step 2 is deliberately conservative: it only accepts a match when the directory
actually exists under a known workspace root, so a browser tab or an untitled
window can never redirect a command somewhere unexpected.

---

## Cursor and GitHub Copilot

Neither has a CLI or local API, so these actions **focus the editor and send the
keystrokes you would press**.

**Cursor:** Composer, Composer full screen, AI chat, new chat, inline edit,
accept/reject diff, command palette, quick open, terminal, sidebar, find in files.

**Copilot:** chat, inline chat, edits, accept/dismiss/cycle suggestions, and the
slash commands `/explain`, `/fix`, `/tests`, `/doc`.

### The focus guard

Typing into the wrong window is destructive, so every keystroke action checks
the foreground process first and **refuses to send anything unless the expected
editor is focused**. If a Cursor button seems to do nothing, that is almost
always why — focus Cursor and press again.

You can disable the check per button, but don't unless you have a specific
reason.

### Keybindings drift

Editor shortcuts change between versions and users remap them. They live as data
in `backend/integrations/keymaps.py` — edit that one file if a shortcut moves.

---

## HTTP Request

The most flexible action in VDock: call any URL, from a button.

| Field | Notes |
|---|---|
| **URL** | `http` or `https` only |
| **Method** | GET, POST, PUT, PATCH, DELETE, HEAD |
| **Body** | JSON or raw text |
| **Headers** | One per line, as `Key: value` |
| **Show value from response** | Dotted path into a JSON response, e.g. `data.0.name`, rendered on the button |

Private and localhost addresses are allowed on purpose — pointing a button at a
LAN Home Assistant or a local n8n is the main use case.

**Examples**

- Discord webhook: POST your webhook URL with `{"content": "Deploy finished"}`
- Home Assistant: POST `http://homeassistant.local:8123/api/webhook/xyz`
- n8n / Zapier: POST the trigger URL
- Any REST API: GET and surface a value with a result path

---

## Security notes

Worth knowing, since these actions run real commands on your machine:

- **No shell.** Every CLI call passes arguments as a list with `shell=False`. A
  prompt containing `;`, `&&` or backticks is sent as text, never executed.
- **Secrets stay server-side.** The action list exposes only whether an
  integration is configured. Keys are stripped from command output before it
  reaches a notification or the log file.
- **Keystrokes are focus-gated.** See the focus guard above.
- **`backend/.env` is gitignored.** Keep it that way.

---

## Prebuilt scenes

Six ready-made decks ship in the app — **Settings → Templates**:

**Claude Code** · **Cursor AI** · **GitHub Review** · **Git & Terminal** ·
**Debug Session** · **Focus & Meeting**

The Claude Code and Cursor decks declare the app that activates them, so they
auto-switch when you focus that editor (enable auto scene switching in
**Settings → Widgets & Integration**).

---

## Adding your own

An integration is a plugin, not a core change — see
[`docs/development/DEVELOPER_GUIDE.md`](development/DEVELOPER_GUIDE.md) →
*Adding an Integration*. Drop a `*_pack.py` into `backend/integrations/`,
implement `get_action_specs()` and `is_available()`, and your actions appear in
the picker automatically.
