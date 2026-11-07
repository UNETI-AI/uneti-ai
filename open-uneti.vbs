' ============================================
'  UNETI AI - open like an app (what the Desktop and Start menu shortcuts run)
'
'  UNETI AI already running: only opens the window. Not running: starts it hidden through
'  start-uneti.vbs /open, which waits for the server and then opens the window.
'
'  Why not point the shortcut straight at start-uneti.vbs: that script ALWAYS stops the old
'  instance first, so clicking the icon a second time would restart the server and kill every
'  job running in the background. Same rule as "UNETI AI.bat", minus the black console window.
'
'  ASCII only: wscript reads this file with the ANSI codepage.
' ============================================
Option Explicit
Dim fso, sh, root, port, url
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
root = fso.GetParentFolderName(WScript.ScriptFullName)

port = ReadPort()
url = "http://127.0.0.1:" & port

If ServerUp() Then
  OpenWindow
Else
  sh.Run "wscript.exe //nologo """ & root & "\start-uneti.vbs"" /open", 0, False
End If

' The port, in the server's own order: the environment, then .env next to this script, then 7777.
Function ReadPort()
  Dim p, path, f, re, found
  p = sh.ExpandEnvironmentStrings("%UNETI_PORT%")
  If p <> "%UNETI_PORT%" And p <> "" Then
    ReadPort = p
    Exit Function
  End If
  ReadPort = "7777"
  path = fso.GetParentFolderName(WScript.ScriptFullName) & "\.env"
  If Not fso.FileExists(path) Then Exit Function
  If fso.GetFile(path).Size = 0 Then Exit Function
  On Error Resume Next
  Set f = fso.OpenTextFile(path, 1)
  Set re = CreateObject("VBScript.RegExp")
  re.Global = True
  re.Multiline = True
  re.Pattern = "^\s*(?:export\s+)?UNETI_PORT\s*=\s*[""']?(\d+)"
  Set found = re.Execute(f.ReadAll)
  f.Close
  If found.Count > 0 Then ReadPort = found(found.Count - 1).SubMatches(0)
  On Error GoTo 0
End Function

Function ServerUp()
  Dim http
  ServerUp = False
  On Error Resume Next
  Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
  http.setTimeouts 2000, 2000, 2000, 2000
  http.Open "GET", url & "/health", False
  http.Send
  If Err.Number = 0 Then
    If http.Status = 200 Then ServerUp = True
  End If
  Err.Clear
  On Error GoTo 0
End Function

Sub OpenWindow()
  ' App window (no address bar, own taskbar entry): Edge ships with every Windows 10/11,
  ' then Chrome, then whatever the default browser is.
  Dim cands, c
  cands = Array(sh.ExpandEnvironmentStrings("%ProgramFiles(x86)%") & "\Microsoft\Edge\Application\msedge.exe", _
                sh.ExpandEnvironmentStrings("%ProgramFiles%") & "\Microsoft\Edge\Application\msedge.exe", _
                sh.ExpandEnvironmentStrings("%ProgramFiles%") & "\Google\Chrome\Application\chrome.exe", _
                sh.ExpandEnvironmentStrings("%LocalAppData%") & "\Google\Chrome\Application\chrome.exe")
  For Each c In cands
    If fso.FileExists(c) Then
      sh.Run """" & c & """ --app=" & url, 1, False
      Exit Sub
    End If
  Next
  sh.Run url, 1, False
End Sub
