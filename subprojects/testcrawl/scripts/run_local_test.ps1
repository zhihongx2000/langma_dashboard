Param(
  [switch]$InstallDeps = $true
)

$ErrorActionPreference = "Stop"
Set-Location -Path (Split-Path -Parent $PSScriptRoot)

if (!(Test-Path ".env.localtest")) {
  Copy-Item ".env.localtest.example" ".env.localtest"
  Write-Host "Created .env.localtest from template. Please fill API keys if needed."
}

if ($InstallDeps) {
  python -m pip install -r requirements.txt
  python -m playwright install chromium
}

Get-Content ".env.localtest" | ForEach-Object {
  if ($_ -match "^\s*#") { return }
  if ($_ -notmatch "=") { return }
  $parts = $_.Split("=", 2)
  $name = $parts[0].Trim()
  $value = $parts[1]
  [Environment]::SetEnvironmentVariable($name, $value, "Process")
}

Write-Host "Starting local test server at http://127.0.0.1:8000"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

