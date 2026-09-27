# DL-077: Document fixing touch-to-wrong-monitor for touchscreen second displays

## Background

Users running VDock on a dedicated touchscreen monitor (the "second screen
that earns its desk space" and "kiosk/workshop panel" use cases already in
the README) can hit a Windows-level problem that has nothing to do with
VDock: Windows routes every touch tap to the *primary* display instead of
the touchscreen the finger actually touched, because the digitizer was
never associated with that specific monitor.

The built-in fix, once Tablet PC Settings' own "Setup" wizard doesn't stick,
is Windows' own `MultiDigiMon.exe` (`C:\Windows\System32`) — a legitimate
Microsoft digitizer-to-monitor mapping tool, not a third-party or invented
tool. Verified via web search before documenting it (a wrong command here
would send users hunting for a nonexistent `.exe`):
`https://superuser.com/questions/1158302` confirms `cmd /C multidigimon -touch`
as the working fix, and Microsoft's own file metadata (surfaced via
STRONTIC's xcyclopedia mirror) confirms `MultiDigiMon.exe` is signed by
Microsoft Corporation and shipped with Windows 10/11, described as
"Digitizer to Monitor Mapping Tool."

## Design

This is a Windows OS-level tip, not a VDock feature — so it's documented
as troubleshooting/setup guidance in the two places a user would already
be looking when this bites them:

- **README.md**: new subsection "Using a touchscreen as a second monitor
  (Windows)" directly under the existing kiosk-panel use case, plus a row
  in the Troubleshooting table pointing there.
- **In-app Help & Guide** (`UserGuideModal.vue`, Troubleshooting tab): a
  matching `.trouble-item` entry, since that's the tab users already open
  for "something's acting weird" issues, and it needs no new screenshot
  (this is OS dialog territory, not a VDock screen) — plain text fits the
  existing `.trouble-item` pattern used by every other entry in that tab.

Both call out explicitly that this is Windows' own tool, not something
VDock controls, so a user doesn't file it as a VDock bug.

## Implementation Results

Added the README subsection + troubleshooting row and the matching
in-app Help & Guide troubleshooting entry. No screenshot needed — this
is text-only guidance describing an OS dialog and a CMD command.

### Verification

- Frontend: 59 files / 254 tests green; `vue-tsc --noEmit` clean.
- Command verified against community reports and Microsoft's own file
  metadata before writing it into user-facing docs; not tested against a
  real dual-touchscreen rig from this session (none available here).
