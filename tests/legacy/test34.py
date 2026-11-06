# Запасний шлях кооперативу: гравець не достукується до сервера гри (антивірус / мережа) — гра йде через MQTT
import os,pathlib,socket,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
def port():
    s=socket.socket();s.bind(('127.0.0.1',0));p=s.getsockname()[1];s.close();return p
WP=port()
br=subprocess.Popen([sys.executable,str(ROOT/'tests'/'mqtt_broker.py'),str(WP)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(2.5)
SETUP=f"CONFIG.coop.signalUrl='';CONFIG.coop.mqttUrls=['ws://127.0.0.1:{WP}/'];CONFIG.coop.iceServers=[];MainServer.check=()=>Promise.resolve(MainServer.state);"
errs=[]
def check(cond,what):
    print(('ok  ' if cond else 'FAIL'),what)
    if not cond:errs.append(what)
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    A=b.new_context(viewport={'width':1280,'height':760}).new_page();B=b.new_context(**p.devices['Pixel 7']).new_page()
    for pg,n in [(A,'A'),(B,'B')]:pg.on('pageerror',lambda e,n=n: errs.append(n+': '+str(e)+' '+(e.stack or '')[:300]))
    A.goto(GAME);A.wait_for_timeout(400);A.evaluate(SETUP+"MainServer.state='offline'");A.click('#btnNew');A.click('#btnSkip');A.click('#btnStart');A.wait_for_timeout(900)
    A.evaluate("Game.changeLocation('outskirts',{x:40,y:40});setInterval(()=>{if(Game.hero)Game.hero.iframe=99},100)");A.wait_for_timeout(1300)
    A.evaluate("Net.hostRoom()");A.wait_for_timeout(1500);code=A.evaluate("Net.room")
    check(A.evaluate("MqttRelay.ok()"),'хост слухає кімнату через запасний шлях')
    # гість: сервер «онлайн, але недоступний з цього пристрою»
    B.goto(GAME);B.wait_for_timeout(400);B.evaluate(SETUP+"MainServer.state='blocked';MainServer.blockedUrl='https://x.trycloudflare.com'");B.tap('#btnCoop1');B.wait_for_timeout(200)
    B.fill('#coopName','Бельгієць');B.fill('#coopCodeIn',code);B.tap('#btnCoopJoin')
    for i in range(40):
        B.wait_for_timeout(250)
        if B.evaluate("Game.state")=='create':break
    check(B.evaluate("Net.hostLink&&Net.hostLink.kind")=='mqtt' and B.evaluate("Game.state")=='create','гість підключився через запасний шлях')
    B.tap('#btnStart');B.wait_for_timeout(3000)
    check(B.evaluate("Net.isGuest()&&Game.state==='play'"),'гість у грі')
    check(A.evaluate("Net.remotes.length")==1 and B.evaluate("Net.remotes.length")==1,'гравці бачать одне одного')
    check(A.evaluate("Game.combatants.length")==B.evaluate("Game.combatants.length"),'однакові вороги')
    nid=A.evaluate("Game.combatants.find(c=>c.isEnemy&&!c.dead).nid");hp0=A.evaluate(f"Game.combatants.find(c=>c.nid==='{nid}').hp")
    B.evaluate(f"hitTarget(Game.combatants.find(c=>c.nid==='{nid}'),{{mult:2,tags:[]}})");B.wait_for_timeout(700)
    check(A.evaluate(f"Game.combatants.find(c=>c.nid==='{nid}').hp")<hp0,'удар гостя дійшов до хоста')
    A.evaluate("Game.hero.x=37;Game.hero.y=42");B.wait_for_timeout(900)
    r=B.evaluate("(()=>{const r=Net.remotes[0];return [r.x,r.y]})()");check(abs(r[0]-37)<0.4 and abs(r[1]-42)<0.4,f'рух хоста видно {r}')
    B.screenshot(path=SHOTS+'mqtt_guest.png')
    B.evaluate("Net.leave()");A.wait_for_timeout(1500)
    check(A.evaluate("Object.keys(Net.peers).length")==0,'хост бачить, що гість вийшов')
    # пряме з'єднання не вдалося — гість сам переходить на запасний шлях
    C=b.new_context().new_page();C.on('pageerror',lambda e: errs.append('C: '+str(e)))
    C.goto(GAME);C.wait_for_timeout(400);C.evaluate(SETUP+"MainServer.state='offline';CONFIG.coop.joinWaitNet=3;Signal.pub=()=>{}");C.click('#btnCoop1')
    C.fill('#coopName','Сусід');C.fill('#coopCodeIn',code);C.click('#btnCoopJoin')
    for i in range(60):
        C.wait_for_timeout(250)
        if C.evaluate("Game.state")=='create':break
    check(C.evaluate("Net.hostLink&&Net.hostLink.kind")=='mqtt' and C.evaluate("Game.state")=='create','пряме з’єднання не вдалося — гість сам перейшов на запасний шлях')
    print('ERRORS',errs[:6]);b.close()
finally:
    br.terminate()
