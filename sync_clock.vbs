Set objShell = CreateObject("WScript.Shell")
Set objNetwork = CreateObject("WScript.Network")

' Get current time from system
strComputerName = objNetwork.ComputerName

' Try to sync time using w32tm
strCommand = "w32tm /resync /force"
On Error Resume Next
objShell.Run strCommand, 0, True
On Error GoTo 0

' Check if it worked
strCheckCommand = "w32tm /query /status"
Set objExec = objShell.Exec("cmd /c " & strCheckCommand)
strOutput = objExec.StdOut.ReadAll()

If InStr(strOutput, "synchronized") Then
    MsgBox "✓ Clock synchronized successfully!", 64, "SmartVision"
Else
    MsgBox "Clock sync may have failed. Please run as Administrator." & vbCrLf & vbCrLf & _
           "Open PowerShell as Admin and run:" & vbCrLf & _
           "w32tm /resync /force", 48, "SmartVision - Clock Fix"
End If
