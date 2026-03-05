@echo off
echo ========================================
echo  IC Design PM Tool - Build Script
echo ========================================
echo.

echo [1/3] Installing dependencies...
pip install openpyxl pyinstaller
echo.

echo [2/3] Running PyInstaller...
pyinstaller --onefile --windowed --name "IC_Design_PM" main.py
echo.

echo [3/3] Build complete!
echo Output: dist\IC_Design_PM.exe
echo.
pause
