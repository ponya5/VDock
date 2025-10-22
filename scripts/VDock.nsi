; VDock Windows Installer
; NSIS Installer script for VDock application

!include "MUI2.nsh"
!include "LogicLib.nsh"

; Basic settings
Name "VDock"
OutFile "VDock-Installer.exe"
InstallDir "$PROGRAMFILES\VDock"
InstallDirRegKey HKCU "Software\VDock" ""
RequestExecutionLevel admin

; Appearance
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

; Installer sections
Section "Install VDock"
  SetOutPath "$INSTDIR"

  ; Copy application files
  File /r "backend"
  File /r "frontend"
  File /r "docs"
  File /r "scripts"
  File "README.md"
  File "LICENSE"
  File "launch.bat"
  File "install.bat"

  ; Create shortcuts
  SetOutPath "$INSTDIR"
  CreateDirectory "$SMPROGRAMS\VDock"
  CreateShortcut "$SMPROGRAMS\VDock\VDock.lnk" "$INSTDIR\VDock-Launcher.exe"
  CreateShortcut "$SMPROGRAMS\VDock\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortcut "$DESKTOP\VDock.lnk" "$INSTDIR\VDock-Launcher.exe"

  ; Store installation folder
  WriteRegStr HKCU "Software\VDock" "" $INSTDIR

  ; Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  ; Remove shortcuts
  RMDir /r "$SMPROGRAMS\VDock"
  Delete "$DESKTOP\VDock.lnk"

  ; Remove installation directory
  RMDir /r "$INSTDIR"

  ; Remove registry key
  DeleteRegKey HKCU "Software\VDock"
SectionEnd
