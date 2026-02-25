@echo off
REM ============================================================
REM  PDF Anonymizer – Build script for Windows EXE
REM ============================================================
REM
REM  Prerequisites:
REM    1. Python 3.10+ installed and on PATH
REM    2. Run:  pip install -r requirements.txt
REM
REM  This script produces a single-folder distribution in dist\PDFAnonymizer\
REM  containing PDFAnonymizer.exe
REM ============================================================

echo.
echo ========================================
echo   PDF Anonymizer – Build
echo ========================================
echo.

REM Install dependencies
echo [1/2] Installing dependencies ...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)

echo.
echo [2/2] Building EXE with PyInstaller ...
pyinstaller ^
    --noconfirm ^
    --clean ^
    --name PDFAnonymizer ^
    --windowed ^
    --onedir ^
    --add-data "src;src" ^
    src\main.py

if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build complete!
echo   Output: dist\PDFAnonymizer\PDFAnonymizer.exe
echo ========================================
echo.
pause
