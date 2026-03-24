@echo off
echo ============================================
echo   VN Stock Chart - Build EXE
echo ============================================
echo.

:: Kiem tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [LOI] Khong tim thay Python. Vui long cai Python 3.10+ truoc.
    pause
    exit /b 1
)

:: Cai thu vien
echo [1/3] Dang cai thu vien...
pip install vnstock plotly dash pandas pyinstaller -q
if errorlevel 1 (
    echo [LOI] Cai thu vien that bai.
    pause
    exit /b 1
)

:: Build EXE
echo [2/3] Dang build EXE (co the mat 2-5 phut)...
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "VNStockChart" ^
  --hidden-import "dash" ^
  --hidden-import "dash_core_components" ^
  --hidden-import "dash_html_components" ^
  --hidden-import "dash.dependencies" ^
  --hidden-import "plotly" ^
  --hidden-import "plotly.graph_objects" ^
  --hidden-import "plotly.subplots" ^
  --hidden-import "vnstock" ^
  --hidden-import "pandas" ^
  launcher.py

if errorlevel 1 (
    echo [LOI] Build that bai. Xem log o tren.
    pause
    exit /b 1
)

echo [3/3] Hoan thanh!
echo.
echo File EXE nam tai: dist\VNStockChart.exe
echo Mo thu ngay bay gio? (Y/N)
set /p choice=
if /i "%choice%"=="Y" start dist\VNStockChart.exe

pause
