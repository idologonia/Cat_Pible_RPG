@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Відкриваю тунель Cloudflare до сервера (http://localhost:8787)...
echo Шукай нижче рядок з адресою https://....trycloudflare.com - її і давай друзям.
cloudflared tunnel --url http://localhost:8787
pause
