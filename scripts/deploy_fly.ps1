param(
    [string]$AppName = "robovai-nova",
    [string]$Region = "fra",
    [switch]$CreateIfMissing
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Get-Command fly -ErrorAction SilentlyContinue)) {
    throw "Fly CLI is not installed. Install from: https://fly.io/docs/hands-on/install-flyctl/"
}

if ($CreateIfMissing) {
    try {
        fly apps create $AppName --machines | Out-Null
        Write-Host "Created Fly app: $AppName" -ForegroundColor Green
    }
    catch {
        Write-Host "App may already exist. Continuing..." -ForegroundColor Yellow
    }
}

if (-not (Test-Path "fly.toml")) {
    throw "fly.toml not found in repository root."
}

fly deploy --config fly.toml --app $AppName --region $Region --remote-only
if ($LASTEXITCODE -ne 0) {
    throw "Fly deploy failed."
}

fly status --app $AppName
fly open --app $AppName
