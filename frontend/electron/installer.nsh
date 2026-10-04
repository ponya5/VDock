; OS login autostart was removed — users launch VDock via shortcut or launch.bat.
; package, both under the value name "VDock" — so the generated
; uninstaller never sees it. One delete covers both writers; a
; missing value is a no-op.
!macro customUnInstall
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "VDock"
!macroend
