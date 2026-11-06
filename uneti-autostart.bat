@echo off
chcp 65001 >nul
title Tu khoi dong UNETI AI
REM Tu khoi dong UNETI AI cung Windows. Dung: uneti-autostart.bat install | uninstall | status
REM Logic nam trong uneti-autostart.ps1 (ghi/xoa muc UNETI-AI trong HKCU Run, khong can quyen
REM admin). Bat roi thi dang nhap may la server tu chay nen va tu mo dashboard (0.306.0).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0uneti-autostart.ps1" %1
