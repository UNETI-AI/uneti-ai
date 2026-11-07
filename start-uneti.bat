@echo off
chcp 65001 >nul
title Khoi dong UNETI AI
cd /d "%~dp0"

REM Cong: dung thu tu cua server - bien moi truong, roi .env, roi 7777.
if "%UNETI_PORT%"=="" if exist ".env" for /f "usebackq tokens=1-3 delims== " %%a in (".env") do (
  if /i "%%a"=="UNETI_PORT" set "UNETI_PORT=%%~b"
  if /i "%%a"=="export" if /i "%%b"=="UNETI_PORT" set "UNETI_PORT=%%~c"
)
if "%UNETI_PORT%"=="" set UNETI_PORT=7777
echo Bat UNETI AI chay NEN - khong con cua so den (port %UNETI_PORT%)...
REM Viec tat instance cu + chay server AN giao het cho start-uneti.vbs (cua so an hoan toan).
REM Log ghi vao server\uneti.log (mo file do neu can xem loi). Tat server: stop-uneti.bat.
wscript //nologo start-uneti.vbs

echo.
echo Da bat. Cho ~10 giay roi mo http://localhost:%UNETI_PORT% va bam Ctrl+Shift+R.
echo (Tat server: chay stop-uneti.bat. Xem loi: mo file server\uneti.log)
timeout /t 4 >nul
