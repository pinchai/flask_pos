Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Building Flask POS Windows Executable (.exe)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$pythonExe = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }

& $pythonExe -m PyInstaller --noconfirm flask_pos.spec

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================================" -ForegroundColor Green
    Write-Host "  [SUCCESS] Build Complete!" -ForegroundColor Green
    Write-Host "  Output: dist\flask_pos.exe" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] Build failed with exit code $LASTEXITCODE" -ForegroundColor Red
}

