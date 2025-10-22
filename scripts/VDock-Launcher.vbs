' VDock Desktop Launcher for Windows
' This VBS script runs launch.bat silently without showing a console window

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Change to VDock directory
objShell.CurrentDirectory = strScriptPath

' Run launch.bat in a minimized window
objShell.Run "cmd /c launch.bat", 0, False

' Show notification (optional)
' objShell.Popup "VDock is starting...", 2, "VDock", 64

Set objShell = Nothing
Set objFSO = Nothing
