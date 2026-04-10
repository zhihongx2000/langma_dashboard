param(
  [int]$Port = 8000,
  [string]$BindHost = "127.0.0.1",
  [int]$FallbackPort = 8001,
  [int]$HealthTimeoutSec = 25
)

$ErrorActionPreference = "Stop"

function Get-ListeningPids {
  param([int]$TargetPort)
  $pids = @()
  try {
    $pids = Get-NetTCPConnection -State Listen -LocalPort $TargetPort -ErrorAction Stop |
      Select-Object -ExpandProperty OwningProcess -Unique
  } catch {
    $lines = netstat -ano -p tcp | Select-String (":" + $TargetPort + "\s+.*LISTENING")
    foreach ($ln in $lines) {
      $parts = ($ln.ToString() -split "\s+") | Where-Object { $_ -ne "" }
      if ($parts.Length -gt 0) {
        $pidText = $parts[-1]
        if ($pidText -match "^\d+$") {
          $pids += [int]$pidText
        }
      }
    }
    $pids = $pids | Select-Object -Unique
  }
  return $pids
}

function Stop-PortListeners {
  param([int]$TargetPort)
  $pids = Get-ListeningPids -TargetPort $TargetPort
  foreach ($pidVal in $pids) {
    if ($pidVal -eq 0 -or $pidVal -eq $PID) {
      continue
    }
    try {
      Stop-Process -Id $pidVal -Force -ErrorAction Stop
      Write-Host "Stopped PID $pidVal (port $TargetPort)."
    } catch {
      Write-Warning "Cannot stop PID $pidVal on port $TargetPort. Try running PowerShell as Administrator."
    }
  }
}

function Wait-HttpOk {
  param(
    [string]$Url,
    [int]$TimeoutSec
  )
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while ((Get-Date) -lt $deadline) {
    try {
      $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
      if ($resp.StatusCode -eq 200) {
        return $true
      }
    } catch {
      Start-Sleep -Milliseconds 500
    }
  }
  return $false
}

function Wait-Endpoint200 {
  param(
    [string]$Url,
    [int]$TimeoutSec
  )
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while ((Get-Date) -lt $deadline) {
    try {
      $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
      if ($resp.StatusCode -eq 200) {
        return $true
      }
    } catch {
      Start-Sleep -Milliseconds 500
    }
  }
  return $false
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "Switching service to new process on $BindHost`:$Port ..."
Stop-PortListeners -TargetPort $Port

$args = @("-m", "uvicorn", "app.main:app", "--host", $BindHost, "--port", "$Port")
$proc = Start-Process -FilePath "python" -ArgumentList $args -WorkingDirectory $repoRoot -PassThru
Write-Host "Started uvicorn PID $($proc.Id). Waiting for health check..."

$baseUrl = "http://$BindHost`:$Port"
$ok = Wait-HttpOk -Url "$baseUrl/api/provinces" -TimeoutSec $HealthTimeoutSec
$cqOk = Wait-Endpoint200 -Url "$baseUrl/api/test/chongqing/levels" -TimeoutSec 6

if ($ok -and $cqOk) {
  Write-Host "Service is healthy: $baseUrl/api/provinces"
  Write-Host "Quick check: $baseUrl/api/test/chongqing/levels"
  exit 0
}

Write-Warning "Port $Port is reachable but not serving latest routes (or failed to bind). Trying fallback port $FallbackPort ..."
Stop-PortListeners -TargetPort $FallbackPort

$fallbackArgs = @("-m", "uvicorn", "app.main:app", "--host", $BindHost, "--port", "$FallbackPort")
$fallbackProc = Start-Process -FilePath "python" -ArgumentList $fallbackArgs -WorkingDirectory $repoRoot -PassThru
Write-Host "Started fallback uvicorn PID $($fallbackProc.Id)."

$fallbackBase = "http://$BindHost`:$FallbackPort"
$ok2 = Wait-HttpOk -Url "$fallbackBase/api/provinces" -TimeoutSec $HealthTimeoutSec
$cqOk2 = Wait-Endpoint200 -Url "$fallbackBase/api/test/chongqing/levels" -TimeoutSec 12
if (-not $ok2 -or -not $cqOk2) {
  Write-Error "Fallback port $FallbackPort is not healthy enough. Please run script as Administrator and retry."
  exit 1
}

Write-Host "Switched to new process on fallback: $fallbackBase"
Write-Host "Use this URL now: $fallbackBase/test-ui"
