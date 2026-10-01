# PowerShell Startup Script for GHS Hostel Mess Management System
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptPath

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  Starting GHS Hostel Mess Management System..." -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan

$venvPython = Join-Path $scriptPath "venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "[INFO] Using virtual environment Python..." -ForegroundColor Yellow
    & $venvPython run.py
} else {
    Write-Host "[INFO] Using system Python..." -ForegroundColor Yellow
    python run.py
}
