$ErrorActionPreference = "Stop"

# 本文件需为 UTF-8 带 BOM，否则 Windows PowerShell 5.1 解析中文会乱码；以下为控制台 UTF-8 输出
try {
  $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
  [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
} catch {}

$root = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $root "frontend"
$testcrawlDir = Join-Path $root "subprojects\testcrawl"

Write-Host "[1/5] 启动前端服务 (3000)..."
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendDir'; npm run dev" | Out-Null

Write-Host "[2/5] 启动后端服务 (8000)..."
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; uv run python main.py" | Out-Null

Write-Host "[3/5] 启动考试院工具服务 (8001)..."
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "Set-Location '$testcrawlDir'; powershell -ExecutionPolicy Bypass -File .\scripts\run_local_tool.ps1" | Out-Null

Write-Host "[4/5] 等待服务启动（后端首次 uv 冷启动可能较慢）..."
Start-Sleep -Seconds 6

$checks = @(
  @{ Name = "frontend"; Url = "http://127.0.0.1:3000/" },
  @{ Name = "backend"; Url = "http://127.0.0.1:8000/docs" },
  @{ Name = "testcrawl"; Url = "http://127.0.0.1:8001/health" }
)

Write-Host "[5/5] 健康检查（最多轮询约 45 秒）:"
$deadline = (Get-Date).AddSeconds(45)
$seenOk = @{}
foreach ($c in $checks) { $seenOk[$c.Name] = $false }

while ((Get-Date) -lt $deadline) {
  $pending = @($checks | Where-Object { -not $seenOk[$_.Name] })
  if ($pending.Count -eq 0) { break }
  foreach ($check in $pending) {
    try {
      $resp = Invoke-WebRequest -Uri $check.Url -TimeoutSec 8 -UseBasicParsing
      Write-Host (" - {0}: OK ({1})" -f $check.Name, $resp.StatusCode)
      $seenOk[$check.Name] = $true
    } catch {
      # 本轮静默，下一轮再试
    }
  }
  if ($seenOk.Values -notcontains $false) { break }
  Start-Sleep -Seconds 3
}

foreach ($check in $checks) {
  if (-not $seenOk[$check.Name]) {
    try {
      $resp = Invoke-WebRequest -Uri $check.Url -TimeoutSec 8 -UseBasicParsing
      Write-Host (" - {0}: OK ({1})" -f $check.Name, $resp.StatusCode)
      $seenOk[$check.Name] = $true
    } catch {
      Write-Host (" - {0}: FAIL ({1})" -f $check.Name, $_.Exception.Message)
    }
  }
}

Write-Host "Done. Launch commands for all services were issued."
