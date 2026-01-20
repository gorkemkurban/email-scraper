@echo off
echo Building Email Scraper Executable...
echo.

echo [1/3] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/3] Running PyInstaller (this may take 1-2 minutes)...
python -m PyInstaller --clean --noconfirm EmailScraper.spec

echo [3/3] Checking build...
if exist "dist\EmailScraper.exe" (
    echo.
    echo Build successful!
    echo Executable: dist\EmailScraper.exe
    dir "dist\EmailScraper.exe" | find "EmailScraper.exe"
) else (
    echo.
    echo Build failed! Check error messages above.
)

pause
