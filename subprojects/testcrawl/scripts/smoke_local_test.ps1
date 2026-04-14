$ErrorActionPreference = "Stop"
Set-Location -Path (Split-Path -Parent $PSScriptRoot)

if (!(Test-Path ".env.localtest")) {
  Write-Host ".env.localtest not found. Copy from .env.localtest.example first."
  exit 1
}

$envMap = @{}
Get-Content ".env.localtest" | ForEach-Object {
  if ($_ -match "^\s*#") { return }
  if ($_ -notmatch "=") { return }
  $parts = $_.Split("=", 2)
  $envMap[$parts[0].Trim()] = $parts[1]
}

$base = "http://127.0.0.1:8001"
$adminKey = "local-test-key"
if ($envMap.ContainsKey("ADMIN_API_KEY") -and $envMap["ADMIN_API_KEY"]) {
  $adminKey = $envMap["ADMIN_API_KEY"]
}
$headers = @{ "X-API-Key" = $adminKey }

Write-Host "Checking /health..."
$health = Invoke-RestMethod -Uri "$base/health" -Method Get
$health | ConvertTo-Json -Depth 3

Write-Host "Checking provinces..."
$provinces = Invoke-RestMethod -Uri "$base/api/provinces" -Method Get
Write-Host ("Province count: " + $provinces.Count)

Write-Host "Checking ai search..."
$ai = Invoke-RestMethod -Uri "$base/api/search/ai?query=%E8%80%83%E8%AF%95" -Method Get
$ai | ConvertTo-Json -Depth 4

Write-Host "Checking latest report..."
$report = Invoke-RestMethod -Uri "$base/api/crawl/report-latest" -Method Get
$report | ConvertTo-Json -Depth 5

Write-Host "Triggering full refresh job..."
$body = @{ type = "full" } | ConvertTo-Json
$job = Invoke-RestMethod -Uri "$base/api/crawl/trigger" -Method Post -Headers $headers -ContentType "application/json" -Body $body
$job | ConvertTo-Json -Depth 4

Write-Host "Smoke test finished."
