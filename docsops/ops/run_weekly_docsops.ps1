$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\.." )).Path
Set-Location $RepoRoot
New-Item -ItemType Directory -Path "reports" -Force | Out-Null
if (Test-Path ".env.docsops.local") {
  Get-Content ".env.docsops.local" | ForEach-Object {
    if ($_ -match '^\s*$' -or $_ -match '^\s*#') { return }
    $kv = $_.Split('=', 2)
    if ($kv.Length -eq 2) {
      [Environment]::SetEnvironmentVariable($kv[0].Trim(), $kv[1].Trim(), "Process")
    }
  }
}
while ($true) {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 "docsops/scripts/run_weekly_gap_batch.py" --docsops-root "docsops" --reports-dir "reports" --since 7
  } else {
    python "docsops/scripts/run_weekly_gap_batch.py" --docsops-root "docsops" --reports-dir "reports" --since 7
  }
  if ($LASTEXITCODE -eq 0) {
    break
  }
  Write-Host "[docsops] weekly run failed, retrying in 60s..."
  Start-Sleep -Seconds 60
}
