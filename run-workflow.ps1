# Déclenche manuellement le workflow "Daily Digest" sur GitHub Actions.
# Prérequis : fichier .env à la racine avec GITHUB_TOKEN=ghp_...
# Usage : .\run-workflow.ps1

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$envPath = Join-Path $root '.env'
if (-not (Test-Path $envPath)) {
  Write-Host "Fichier .env introuvable. Copie .env.example vers .env et ajoute GITHUB_TOKEN=..." -ForegroundColor Red
  exit 1
}

Get-Content $envPath -Encoding UTF8 | ForEach-Object {
  $line = $_.Trim()
  if ($line -eq '' -or $line.StartsWith('#')) { return }
  $eq = $line.IndexOf('=')
  if ($eq -lt 1) { return }
  $k = $line.Substring(0, $eq).Trim()
  $v = $line.Substring($eq + 1).Trim().Trim([char]0x22).Trim([char]0x27)
  if ($k) { [Environment]::SetEnvironmentVariable($k, $v, 'Process') }
}

if (-not $env:GITHUB_TOKEN) {
  Write-Host "GITHUB_TOKEN vide dans .env" -ForegroundColor Red
  exit 1
}

$headers = @{
  Authorization = "Bearer $($env:GITHUB_TOKEN)"
  Accept        = 'application/vnd.github+json'
}
$uri = 'https://api.github.com/repos/arsenefayard/ai-daily-digest/actions/workflows/daily-digest.yml/dispatches'
$body = '{"ref":"refs/heads/main"}'

Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $body -ContentType 'application/json'
Write-Host "Workflow declenche : https://github.com/arsenefayard/ai-daily-digest/actions" -ForegroundColor Green
