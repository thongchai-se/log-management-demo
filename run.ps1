# One-command appliance bring-up (Windows PowerShell)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$certDir = "deploy\nginx\certs"
$cert = Join-Path $certDir "server.crt"
$key = Join-Path $certDir "server.key"
New-Item -ItemType Directory -Force -Path $certDir | Out-Null

if (-not (Test-Path $cert)) {
  if (Get-Command openssl -ErrorAction SilentlyContinue) {
    openssl req -x509 -nodes -newkey rsa:2048 `
      -keyout $key -out $cert -days 365 `
      -subj "/CN=localhost/O=LogManagementDemo/C=TH"
  } else {
    docker run --rm -v "${PWD}/deploy/nginx/certs:/certs" alpine/openssl `
      req -x509 -nodes -newkey rsa:2048 `
      -keyout /certs/server.key -out /certs/server.crt -days 365 `
      -subj "/CN=localhost/O=LogManagementDemo/C=TH"
  }
  Write-Host "Generated self-signed TLS certs"
}

docker compose up -d --build
Write-Host ""
Write-Host "UI (HTTPS): https://localhost"
Write-Host "API docs:   https://localhost/docs"
Write-Host "Syslog UDP: localhost:5514"
Write-Host "Users: admin/admin123 | viewer/viewer123"
