@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Запускаю сервер кооперативу CAT ^& PIBBLE RPG...
python coop-server.py 8787
if errorlevel 1 py coop-server.py 8787
pause
