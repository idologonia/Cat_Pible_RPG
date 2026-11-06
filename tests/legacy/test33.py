# Етап 28: сервер гри на ПК — оголошення адреси, стан «онлайн/офлайн» у вікні кооперативу, гра через нього
import os,pathlib,signal,socket,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
def port():
    s=socket.socket();s.bind(('127.0.0.1',0));p=s.getsockname()[1];s.close();return p
NP,SP=port(),port()
mock=subprocess.Popen([sys.executable,str(ROOT/'tests'/'ntfy_mock.py'),str(NP)]);time.sleep(0.5)
SURL=f'http://127.0.0.1:{SP}'
srv=subprocess.Popen([sys.executable,str(ROOT/'server'/'coop-server.py'),'--port',str(SP),'--announce-url',SURL,'--brokers','','--ntfy',f'http://127.0.0.1:{NP}/','--name','Сервер Тест'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
time.sleep(4.5)
SETUP=f"CONFIG.coop.mqttUrls=[];CONFIG.coop.signalUrl='http://127.0.0.1:{NP}/';CONFIG.coop.iceServers=[];CONFIG.coop.mainServer.allowAny=true;CONFIG.coop.mainServer.wait=2"
errs=[]
def check(cond,what):
    print(('ok  ' if cond else 'FAIL'),what)
    if not cond:errs.append(what)
def status(pg):
    pg.wait_for_timeout(200)
    for i in range(30):
        c=pg.evaluate("(document.querySelector('#coopBody .coopSrv')||{}).className||''")
        if 'on' in c.split() or 'off' in c.split():return c
        pg.wait_for_timeout(200)
    return c
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    A=b.new_context(viewport={'width':1280,'height':760}).new_page();B=b.new_context(**p.devices['Pixel 7']).new_page()
    for pg,n in [(A,'A'),(B,'B')]:pg.on('pageerror',lambda e,n=n: errs.append(n+': '+str(e)+' '+(e.stack or '')[:300]))
    A.goto(GAME);A.wait_for_timeout(400);A.evaluate(SETUP);A.click('#btnNew');A.click('#btnSkip');A.click('#btnStart');A.wait_for_timeout(900)
    A.evaluate("setInterval(()=>{Game.hero.iframe=99},100)")
    A.keyboard.press('Escape');A.click('#btnCoop2')
    check('on' in status(A).split(),'хост бачить: сервер гри онлайн')
    check('Сервер Тест' in A.evaluate("$('coopBody').textContent"),'видно назву сервера')
    A.screenshot(path=SHOTS+'srv28_online.png')
    A.click('#btnCoopHost');A.wait_for_timeout(1500)
    check(A.evaluate("Net.srvOk")==True,'кімната хоста відкрита на сервері гри')
    code=A.evaluate("Net.room");A.click('#btnCloseCoop');A.keyboard.press('Escape')
    # друг відкриває звичайну гру (не з сервера) — сервер гри знайдеться сам
    B.goto(GAME);B.wait_for_timeout(400);B.evaluate(SETUP);B.tap('#btnCoop1')
    check('on' in status(B).split(),'гість у меню бачить: сервер гри онлайн')
    B.screenshot(path=SHOTS+'srv28_phone.png')
    B.fill('#coopName','Бельгієць');B.fill('#coopCodeIn',code);B.tap('#btnCoopJoin')
    for i in range(30):
        B.wait_for_timeout(250)
        if B.evaluate("Game.state")=='create':break
    check(B.evaluate("Net.hostLink&&Net.hostLink.kind")=='srv','гість підключився через сервер гри')
    B.tap('#btnStart');B.wait_for_timeout(2500)
    check(B.evaluate("Net.isGuest()&&Game.state==='play'"),'гість у грі через сервер')
    check(A.evaluate("Net.remotes.length")==1,'хост бачить гостя')
    # сервер вимикається (Ctrl+C) — оголошує «офлайн»
    srv.send_signal(signal.SIGINT);srv.wait(timeout=10)
    out=srv.stdout.read();print('server:',' | '.join(l for l in out.splitlines() if l.strip())[:300])
    check('офлайн' in out,'сервер повідомив, що вимикається')
    A.keyboard.press('Escape');A.click('#btnCoop2');A.evaluate("MainServer.check(true)")
    check('off' in status(A).split() and A.evaluate("MainServer.state")=='offline','після вимкнення — сервер гри офлайн')
    A.screenshot(path=SHOTS+'srv28_offline.png')
    print('ERRORS',errs[:6]);b.close()
finally:
    for pr in (srv,mock):
        try:pr.terminate()
        except Exception:pass
