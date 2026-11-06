@echo off
chcp 65001 >nul
cd /d "%~dp0"
title CAT ^& PIBBLE RPG - сервер кооперативу
echo ============================================
echo   Сервер кооперативу CAT ^& PIBBLE RPG
echo   Не закривай це вікно, поки граєте.
echo ============================================
echo.
python -c "import sys" >nul 2>nul && (python coop-server.py --public & goto end)
py -3 -c "import sys" >nul 2>nul && (py -3 coop-server.py --public & goto end)
if exist python\python.exe goto run
echo Python не знайдено - завантажую портативний Python (один раз, ~10 МБ)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip -OutFile py.zip; Expand-Archive py.zip python -Force; Remove-Item py.zip"
if not exist python\python.exe (echo Не вдалося завантажити Python. Перевір інтернет. & goto end)
:run
python\python.exe coop-server.py --public
:end
echo.
pause
