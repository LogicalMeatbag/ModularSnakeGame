Set WshShell = WScript.CreateObject("WScript.Shell")
Set FileSystem = CreateObject("Scripting.FileSystemObject")

' Get the full path to the project root (one level up from this script).
projectRoot = FileSystem.GetParentFolderName(FileSystem.GetParentFolderName(WScript.ScriptFullName))

' Define the name and path for the shortcut we are creating.
shortcutPath = FileSystem.BuildPath(projectRoot, "ANAHKENs Modular Snake Game.lnk")

' Create the shortcut object.
Set oShellLink = WshShell.CreateShortcut(shortcutPath)

' --- Set Shortcut Properties ---

' Target: The executable file inside the 'dist' folder.
oShellLink.TargetPath = "%windir%\\system32\\cmd.exe"
oShellLink.Arguments = "/c start """" ""dist\\ANAHKENs Modular Snake Game.exe"""
oShellLink.IconLocation = FileSystem.BuildPath(projectRoot, "assets\\images\\icon.ico")
oShellLink.Description = "Launches ANAHKENs Modular Snake Game"

' Save the shortcut file to disk.
oShellLink.Save