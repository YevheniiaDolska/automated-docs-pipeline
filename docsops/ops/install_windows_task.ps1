$ErrorActionPreference = "Stop"
$TaskNamePrefix = "VeriOpsWeekly-veriops"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RepoLeaf = Split-Path -Path $RepoRoot -Leaf
$RepoSlug = ($RepoLeaf.ToLower() -replace '[^a-z0-9]+', '-').Trim('-')
if (-not $RepoSlug) { $RepoSlug = "repo" }
$TaskName = "$TaskNamePrefix-$RepoSlug"
$ScriptPath = (Resolve-Path (Join-Path $PSScriptRoot "run_weekly_docsops.ps1")).Path
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "10:00"
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Force | Out-Null
Write-Host "Installed Task Scheduler job: $TaskName (monday 10:00)"
