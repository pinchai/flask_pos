@echo off
echo ========================================================
echo   Building Flask POS Windows Executable (.exe)
echo ========================================================
if exist ".\.venv\Scripts\python.exe" (
    .\.venv\Scripts\python.exe -m PyInstaller --noconfirm flask_pos.spec
) else (
    python -m PyInstaller --noconfirm flask_pos.spec
)

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo   [SUCCESS] Build Complete!
    echo   Output: dist\flask_pos.exe
    echo ========================================================
) else (
    echo.
    echo [ERROR] Build failed with exit code %ERRORLEVEL%
)
pause

