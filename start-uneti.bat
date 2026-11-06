@echo off
chcp 65001 >nul
title Khoi dong UNETI AI
cd /d "%~dp0"

echo Bat UNETI AI chay NEN - khong con cua so den (port 7777)...
REM Viec tat instance cu + chay server AN giao het cho start-uneti.vbs (cua so an hoan toan).
REM Log ghi vao server\uneti.log (mo file do neu can xem loi). Tat server: stop-uneti.bat.
wscript //nologo start-uneti.vbs

echo.
echo Da bat. Cho ~10 giay roi mo http://localhost:7777 va bam Ctrl+Shift+R.
echo (Tat server: chay stop-uneti.bat. Xem loi: mo file server\uneti.log)
timeout /t 4 >nul
