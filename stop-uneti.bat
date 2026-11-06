@echo off
chcp 65001 >nul
title Dung UNETI AI
echo Dang tim va tat UNETI AI...
REM Logic giet nam trong stop-uneti.ps1 (giet theo dung python cua venv + chu port 7777).
REM KHONG dung timeout o day: chay an qua VBS se loi "Input redirection is not supported".
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-uneti.ps1"
REM Don cua so CMD den "UNETI AI" kieu cu con sot (flow moi chay an, khong tao cua so nay).
taskkill /F /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq UNETI AI*" >nul 2>&1
echo Xong.
exit /b 0
