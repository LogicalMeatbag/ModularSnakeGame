Set WshShell = WScript.CreateObject("WScript.Shell")
Set FileSystem = CreateObject("Scripting.FileSystemObject")

' =================================================================
'  Shortcut Creator for ANAHKEN's Modular Snake Game
' =================================================================
' This script generates a portable Windows shortcut (.lnk) that
' launches the game. It uses relative paths so it will work
' correctly no matter where the user unzips the game folder.

' Get the full path to the directory where this script is running.
scriptDir = FileSystem.GetParentFolderName(WScript.ScriptFullName)

' Define the name and path for the shortcut we are creating.
shortcutPath = FileSystem.BuildPath(scriptDir, "ANAHKENs Modular Snake Game.lnk")

' Create the shortcut object.
Set oShellLink = WshShell.CreateShortcut(shortcutPath)

' --- Set Shortcut Properties ---

' Target: The executable file inside the 'dist' folder.
oShellLink.TargetPath = "%windir%\\system32\\cmd.exe"
oShellLink.Arguments = "/c start """" ""dist\\ANAHKENs Modular Snake Game.exe"""
oShellLink.IconLocation = FileSystem.BuildPath(scriptDir, "assets\\images\\icon.ico")
oShellLink.WorkingDirectory = scriptDir
oShellLink.Description = "Launches ANAHKENs Modular Snake Game"

' Save the shortcut file to disk.
oShellLink.Save

WScript.Echo "Shortcut 'ANAHKENs Modular Snake Game.lnk' created successfully in the project folder."