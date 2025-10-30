@echo off
setlocal enabledelayedexpansion

REM === 路徑與環境 ===
set "ROOT=%~dp0"
set "SELF=%~f0"
set "LOG=%ROOT%weekly.log"

REM 選擇 Python：優先使用本資料夾的 venv，其次 py -3，再者 python
set "PY="
if exist "%ROOT%.venv\Scripts\python.exe" set "PY=%ROOT%.venv\Scripts\python.exe"
if not defined PY (
  where py >nul 2>&1
  if %ERRORLEVEL%==0 (
    set "PY=py -3"
  ) else (
    set "PY=python"
  )
)

REM === 參數處理 ===
if /I "%~1"=="--register" (
  schtasks /Create ^
    /TN "TWSE Weekly Update" ^
    /SC WEEKLY ^
    /D MON ^
    /ST 08:00 ^
    /RL LIMITED ^
    /F ^
    /TR "\"%SELF%\""
  echo 已註冊排程：TWSE Weekly Update（每週一 08:00）
  exit /b !ERRORLEVEL!
)

if /I "%~1"=="--unregister" (
  schtasks /Delete /TN "TWSE Weekly Update" /F
  echo 已移除排程：TWSE Weekly Update
  exit /b !ERRORLEVEL!
)

REM === 計算回補區間：start = 今天 - 7天；end = 昨天 ===
for /f %%A in ('powershell -NoProfile -Command "(Get-Date).AddDays(-7).ToString(\"yyyy-MM-dd\")"') do set "START=%%A"
for /f %%A in ('powershell -NoProfile -Command "(Get-Date).AddDays(-1).ToString(\"yyyy-MM-dd\")"') do set "END=%%A"

REM === 執行爬蟲並寫入日誌 ===
echo [%DATE% %TIME%] 開始每週回補 %START% -> %END% >> "%LOG%"
%PY% -m twse_crawler both --start %START% --end %END% >> "%LOG%" 2>&1
set "CODE=%ERRORLEVEL%"
echo [%DATE% %TIME%] 結束（代碼 %CODE%） >> "%LOG%"
exit /b %CODE%

