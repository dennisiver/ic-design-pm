@echo off
chcp 65001 >nul
echo ========================================
echo  IC設計專案管理工具 - 打包腳本
echo ========================================
echo.

echo [1/3] 安裝相依套件...
pip install openpyxl pyinstaller
echo.

echo [2/3] 執行 PyInstaller 打包...
pyinstaller --onefile --windowed --name "IC設計專案管理" main.py
echo.

echo [3/3] 打包完成！
echo 執行檔位於: dist\IC設計專案管理.exe
echo.
pause
