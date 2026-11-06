# Кооператив через сервер на ПК (server/coop-server.py): хост вписує адресу, гість відкриває гру із сервера
import os,pathlib,socket,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
s=socket.socket();s.bind(('127.0.0.1',0));PORT=s.getsockname()[1];s.close()
srv=subprocess.Popen([sys.executable,str(ROOT/'server'/'coop-server.py'),str(PORT)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);time.sleep(0.8)
URL=f'http://127.0.0.1:{PORT}'
errs=[]
def check(cond,what):
    print(('ok  ' if cond else 'FAIL'),what)
    if not cond:errs.append(what)
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    A=b.new_context(viewport={'width':1280,'height':760}).new_page();cB=b.new_context(**p.devices['Pixel 7']);B=cB.new_page()
    for pg,n in [(A,'A'),(B,'B')]:pg.on('pageerror',lambda e,n=n: errs.append(n+': '+str(e)+' '+(e.stack or '')[:300]))
    A.goto(GAME);A.wait_for_timeout(400);A.click('#btnNew');A.click('#btnSkip');A.click('#btnStart');A.wait_for_timeout(800)
    A.evaluate("Game.changeLocation('outskirts',{x:40,y:40})");A.wait_for_timeout(1200);A.evaluate("setInterval(()=>{Game.hero.iframe=99},100)")
    A.keyboard.press('Escape');A.click('#btnCoop2');A.wait_for_timeout(200)
    A.evaluate(f"window.CPR_SERVER='{URL}'");A.click('#btnCoopHost');A.wait_for_timeout(800)
    code=A.evaluate("Net.room");print('room',code)
    check(A.evaluate("Net.srvOk"),'хост підключився до сервера')
    A.screenshot(path=SHOTS+'srv_host_panel.png');A.click('#btnCloseCoop');A.keyboard.press('Escape')
    # друг відкриває гру прямо із сервера (на телефоні) — адреса сервера підставляється сама
    B.goto(URL+'/');B.wait_for_timeout(600)
    check(B.evaluate("coopServerBase()")==URL,'гра із сервера сама знає адресу сервера')
    B.tap('#btnCoop1');B.wait_for_timeout(200)
    B.fill('#coopName','Сусід');B.fill('#coopCodeIn',code);B.screenshot(path=SHOTS+'srv_join_phone.png');B.tap('#btnCoopJoin')
    for i in range(20):
        B.wait_for_timeout(250)
        if B.evaluate("Game.state")=='create':break
    check(B.evaluate("Game.state")=='create' and B.evaluate("Net.hostLink&&Net.hostLink.kind")=='srv','гість через сервер дійшов до створення героя')
    B.evaluate("UI.cc.cls='knight'");B.fill('#heroName','Пиріг');B.tap('#btnStart');B.wait_for_timeout(2500)
    check(B.evaluate("Net.isGuest()&&Game.state==='play'"),'гість у грі')
    check(A.evaluate("Net.remotes.length")==1 and B.evaluate("Net.remotes.length")==1,'гравці бачать одне одного')
    check(A.evaluate("Game.combatants.length")==B.evaluate("Game.combatants.length"),'однакові вороги')
    nid=A.evaluate("Game.combatants.find(c=>c.isEnemy&&!c.dead).nid");hp0=A.evaluate(f"Game.combatants.find(c=>c.nid==='{nid}').hp")
    B.evaluate(f"hitTarget(Game.combatants.find(c=>c.nid==='{nid}'),{{mult:2,tags:[]}})");B.wait_for_timeout(500)
    check(A.evaluate(f"Game.combatants.find(c=>c.nid==='{nid}').hp")<hp0,'удар гостя через сервер дійшов до хоста')
    B.screenshot(path=SHOTS+'srv_guest_phone.png')
    A.evaluate("Game.changeLocation('forest',null)");B.wait_for_timeout(2500)
    check(B.evaluate("Game.locationId")!='forest','хост пішов у ліс — гість лишився на своїй локації')
    B.evaluate("Game.changeLocation('forest',null)");B.wait_for_timeout(2500)
    check(B.evaluate("Game.locationId")=='forest' and B.evaluate("Net.remotes.length")==1,'гість сам прийшов у ліс і бачить хоста')
    # гість зник (закрив вкладку без прощання) — сервер повідомляє хоста
    B.evaluate("window.onbeforeunload=null");cB.close();A.wait_for_timeout(1200)
    check(A.evaluate("Net.remotes.length")==0,'хост дізнався від сервера, що гість пішов')
    check(A.evaluate("Game.flags.party['сусід'].hd.name")=='Пиріг','герой гостя збережений у хоста')
    print('ERRORS',errs[:6]);b.close()
finally:
    srv.terminate()
    out=srv.communicate(timeout=5)[0];print('server log:',' | '.join(out.strip().splitlines()[:6]))
