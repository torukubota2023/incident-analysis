@echo off
chcp 65001 >nul

set BACKUP_DIR=C:\incident-backup
set DATETIME=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%
set DATETIME=%DATETIME: =0%

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

if exist "C:\incident-analysis\data\incidents.csv" (
    copy "C:\incident-analysis\data\incidents.csv" "%BACKUP_DIR%\incidents_%DATETIME%.csv"
    echo [成功] バックアップ完了: %BACKUP_DIR%\incidents_%DATETIME%.csv
) else (
    echo [情報] データファイルが見つかりません（まだ報告がありません）
)

REM 30日以上前のバックアップを自動削除
forfiles /p "%BACKUP_DIR%" /m "incidents_*.csv" /d -30 /c "cmd /c del @file" 2>nul

echo.
echo 処理が完了しました。
timeout /t 5
