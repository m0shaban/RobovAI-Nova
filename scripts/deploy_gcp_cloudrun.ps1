param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "us-central1",
    [string]$ServiceName = "robovai-nova",
    [string]$EnvFile = ".env.cloudrun.yaml",
    [int]$MinInstances = 0,
    [int]$MaxInstances = 1,
    [string]$Memory = "1Gi",
    [int]$Cpu = 1,
    [int]$TimeoutSeconds = 300,
    [int]$Concurrency = 80
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    throw "gcloud CLI is not installed. Install from: https://cloud.google.com/sdk/docs/install"
}

if (-not (Test-Path $EnvFile)) {
    throw "Environment file '$EnvFile' not found. Create it from .env.cloudrun.example.yaml"
}

gcloud config set project $ProjectId | Out-Null

gcloud run deploy $ServiceName `
  --source . `
  --region $Region `
  --platform managed `
  --allow-unauthenticated `
  --port 8000 `
    --min-instances $MinInstances `
    --max-instances $MaxInstances `
    --memory $Memory `
    --cpu $Cpu `
    --timeout $TimeoutSeconds `
        --concurrency $Concurrency `
        --cpu-throttling `
  --env-vars-file $EnvFile

if ($LASTEXITCODE -ne 0) {
    throw "Cloud Run deploy failed."
}

gcloud run services describe $ServiceName --region $Region --format "value(status.url)"
