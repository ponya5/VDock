; DL-099: the HKCU Run-key autostart entry is written at runtime —
; by the backend's autostart toggle and by the Electron auto-launch
; package, both under the value name "VDock" — so the generated
; uninstaller never sees it. One delete covers both writers; a
; missing value is a no-op.
!macro customUnInstall
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "VDock"
!macroend
