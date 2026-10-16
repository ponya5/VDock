; electron-builder NSIS hooks (frontend/electron/package.json "nsis.include").
;
; Firewall (DL-010): phones reach VDock over Wi-Fi, so the packaged backend
; needs an inbound rule. Program-scoped (vdock-backend.exe), TCP, Private
; networks only - public Wi-Fi stays closed. VDock picks its port at run time
; and Settings > Ports can change it, so the rule is not tied to a port.
; Adding a rule needs admin rights: done directly when the installer is
; elevated (per-machine install), through one UAC prompt otherwise. Silent
; installs (auto-update) never prompt; an existing rule is left alone.

!define VDOCK_FW_RULE "VDock backend"
!define VDOCK_BACKEND_EXE "$INSTDIR\resources\backend\vdock-backend.exe"

!macro customInstall
  nsExec::Exec 'netsh advfirewall firewall show rule name="${VDOCK_FW_RULE}"'
  Pop $0
  ${If} $0 != 0
    UserInfo::GetAccountType
    Pop $1
    ${If} $1 == "Admin"
      nsExec::Exec 'netsh advfirewall firewall add rule name="${VDOCK_FW_RULE}" dir=in action=allow protocol=TCP profile=private program="${VDOCK_BACKEND_EXE}" enable=yes'
      Pop $0
    ${ElseIfNot} ${Silent}
      ExecShell "runas" "netsh" 'advfirewall firewall add rule name="${VDOCK_FW_RULE}" dir=in action=allow protocol=TCP profile=private program="${VDOCK_BACKEND_EXE}" enable=yes' SW_HIDE
    ${EndIf}
  ${EndIf}
!macroend

; OS login autostart was removed — users launch VDock via shortcut or launch.bat.
; Older builds wrote the Run value from both the app and the source
; package, both under the value name "VDock" — so the generated
; uninstaller never sees it. One delete covers both writers; a
; missing value is a no-op.
!macro customUnInstall
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "VDock"

  ; An update runs the old uninstaller first: keep the rule for the new build.
  ${IfNot} ${isUpdated}
    nsExec::Exec 'netsh advfirewall firewall show rule name="${VDOCK_FW_RULE}"'
    Pop $0
    ${If} $0 == 0
      UserInfo::GetAccountType
      Pop $1
      ${If} $1 == "Admin"
        nsExec::Exec 'netsh advfirewall firewall delete rule name="${VDOCK_FW_RULE}"'
        Pop $0
      ${ElseIfNot} ${Silent}
        ExecShell "runas" "netsh" 'advfirewall firewall delete rule name="${VDOCK_FW_RULE}"' SW_HIDE
      ${EndIf}
    ${EndIf}
  ${EndIf}

  ; Agent hooks (Claude Code, Cursor, Codex, Antigravity) point at
  ; vdock-backend.exe — remove them so a deleted exe isn't invoked on every
  ; tool call. Runs the bundled remove_agent_hooks.py via the app's own
  ; dispatch; always exits 0. Plain nsExec (not runas): hooks live in the
  ; *user's* profile, so elevating would clean the admin's profile instead.
  ; On update the new build reuses the same hooks — skip then.
  ${IfNot} ${isUpdated}
    ${If} ${FileExists} "${VDOCK_BACKEND_EXE}"
      nsExec::Exec '"${VDOCK_BACKEND_EXE}" --vdock_remove_agent_hooks'
      Pop $0
    ${EndIf}
  ${EndIf}
!macroend
