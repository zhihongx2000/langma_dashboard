Param(
  [switch]$InstallDeps = $true
)

$ErrorActionPreference = "Stop"
Set-Location -Path (Split-Path -Parent $PSScriptRoot)

function Import-DotEnvFile {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [switch]$Overwrite
  )
  if (!(Test-Path $Path)) { return }
  Get-Content $Path | ForEach-Object {
    if ($_ -match "^\s*#") { return }
    if ($_ -notmatch "=") { return }
    $parts = $_.Split("=", 2)
    $name = $parts[0].Trim()
    $value = $parts[1]
    if ([string]::IsNullOrWhiteSpace($name)) { return }
    # 空值不写入进程环境，避免把根目录 .env 的有效值覆盖掉
    if ([string]::IsNullOrWhiteSpace($value)) { return }
    if (!$Overwrite -and [Environment]::GetEnvironmentVariable($name, "Process")) { return }
    [Environment]::SetEnvironmentVariable($name, $value, "Process")
  }
}

if (!(Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Created .env from template. Fill API keys if needed."
}

if ($InstallDeps) {
  python -m pip install -r requirements.txt
  python -m playwright install chromium
}

# 先读 testcrawl/.env（仅注入非空变量）
Import-DotEnvFile -Path ".env"
# 再读仓库根目录 .env（同样仅注入非空变量，并允许覆盖）
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\..\.."))
$repoRootEnv = if ($repoRoot) { Join-Path $repoRoot ".env" } else { $null }
if ($repoRootEnv) {
  Import-DotEnvFile -Path $repoRootEnv -Overwrite
}

if (-not $env:APP_PORT) {
  $env:APP_PORT = "8001"
}

Write-Host "Starting testcrawl tool server on 0.0.0.0:$($env:APP_PORT) (LAN: http://<本机IP>:$($env:APP_PORT)/)"
python -m uvicorn app.main:app --host 0.0.0.0 --port $env:APP_PORT --reload
