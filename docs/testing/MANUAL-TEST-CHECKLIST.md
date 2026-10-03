# Manual checks for VDock 2.3.0

Automated suites cannot cover these. Do them once on real hardware.
Set a deck password first: **Settings → Devices & network → Connect**.

| Check | Why | Steps | Pass | Fail |
|---|---|---|---|---|
| Approve / Deny a live Claude Code prompt | Highest-value phone use: unblock an agent from another room | Install the hook in a project. Ask Claude Code to run a command. When the permission popup appears, tap **Approve** on the deck or phone | The terminal accepts the command; the key shows working | Nothing happens, or the wrong window receives the keystroke |
| Install, then remove, the Claude hook | Removal must take only VDock's entries | In Settings, Agent hooks, install the Claude Code hook, then tap **Remove hook** and confirm **Yes**. Open `~/.claude/settings.json`, then start Claude Code | The chip shows not hooked; the file keeps all your other hooks and settings; Claude Code starts normally | Another hook or setting is gone, or Claude Code reports a settings error |
| Agent Prompt to a real session | Presets must land in the targeted window only | Open one Claude Code window. Press an Agent Prompt key (e.g. Continue) | The prompt text appears in that window | Text goes to another app, or nothing is typed |
| Hold-to-talk on a phone | Finger drift used to cut dictation off | Hold the dictate key for ~5 s, drift slightly, speak, release | Dictation stays on until release; text appears; nothing is submitted | Dictation stops mid-hold, or Enter is pressed for you |
| Mic mute on a call | System-wide mute must match the key | Join Teams/Zoom/Meet. Tap Mic Mute | The call shows you muted; the key turns red | The key flips but the call still hears you, or the reverse |
| Win+H dictation | Windows voice typing is the backend | Click a text box. Hold the dictate key. Speak. Release | Words appear. Nothing is submitted | Windows never opens voice typing, or it auto-sends |
| Docker running state | The key is grey without a daemon | Start Docker Desktop with one container | Key shows the running count; menu can stop/start | Always "not running" while Docker is up |
| Samsung home-screen icon | PWA icon was missing | Chrome → deck address → Add to Home screen | VDock icon, not a letter | Generic globe / first letter |
| QR pairing under 60 s | First-time setup is where people give up | Set a password. Scan the Connect QR on a fresh phone. Time it | Deck loads, no typing, under 60 s. A reused or 10-minute-old code is rejected | Password prompt, wrong host, or timeout |
| Wake lock + HTTPS | Screen-on needs an installed app or TLS | Follow the mkcert steps in the developer guide. Set `USE_SSL=true`. Install the app. Turn keep-awake on | Screen stays on while the deck is open; dims after leaving | Screen still sleeps after ~30 s |
| Reconnect after sleep | Phones sleep constantly | Lock the phone for a minute. Unlock | Same scene and page, no manual refresh | "Can't reach VDock" that never clears, or a reset to page 1 |
| Deck password | LAN on + no password lets anyone on Wi-Fi control the PC | Settings → Connect → set one. Open the deck on a second device | Second device must log in | Second device is in with no prompt |
| Electron update | Lockfile was patched for a security bump | Close the desktop app. `cd frontend\electron; npm ci`. Start it | App opens normally | Installer / start fails |
| CI on GitHub | New jobs have never run remotely | After you push, open Actions | All jobs green | A job red — open the log |
| Save a key in-app | Keys used to need hand-editing `.env` | Settings → Integrations → Accounts & keys → GitHub token → Set key → paste a real token → Save. Open a GitHub widget button. Then Remove | Chip flips to Set, "Saved / Active now" toast, GitHub widgets go live with no restart; after Remove they go back to "needs a token". On a phone no Set key button appears | Widgets stay dead until relaunch, key visible anywhere, or the phone can change keys |
| Installer build | Not run this cycle | Build the packaged installer for your OS | Installer runs; first launch works | SmartScreen / Gatekeeper only (expected once); anything else is a fail |

Also glance at `docs/assets/screens/phone-portrait.jpg` and `tablet-portrait.jpg`. If they look stacked twice, that is a capture artefact (live DOM has one grid). The button labelled "Volume Slider (Copy)" is from the live profile, not a bug.
