@echo off
chcp 65001 >nul
echo ========================================
echo  インシデント・アクシデント報告システム
echo  おもろまちメディカルセンター
echo ========================================
echo.
echo  起動中... しばらくお待ちください
echo.
echo  終了するにはこのウィンドウを閉じてください
echo ========================================
echo.

cd /d C:\incident-analysis
call venv\Scripts\activate
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true

pause
