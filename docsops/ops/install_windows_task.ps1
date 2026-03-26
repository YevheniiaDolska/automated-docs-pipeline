$ErrorActionPreference = "Stop"
$TaskName = "VeriOpsWeekly-auto-doc-pipeline"
$ScriptPath = (Resolve-Path (Join-Path $PSScriptRoot "run_weekly_docsops.ps1")).Path
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "10:00"
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel LeastPrivilege
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Force | Out-Null
Write-Host "Installed Task Scheduler job: VeriOpsWeekly-auto-doc-pipeline (monday 10:00)"
