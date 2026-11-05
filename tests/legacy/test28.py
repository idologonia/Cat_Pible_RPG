# Кооператив через інтернет (WebRTC): хост і гість у різних профілях браузера, знайомство — через локальну імітацію ntfy
import os,pathlib,socket,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
s=socket.socket();s.bind(('127.0.0.1',0));PORT=s.getsockname()[1];s.close()
srv=subprocess.Popen([sys.executable,str(ROOT/'tests'/'ntfy_mock.py'),str(PORT)]);time.sleep(0.6)
SETUP=f"CONFIG.coop.signalUrl='http://127.0.0.1:{PORT}/';CONFIG.coop.iceServers=[];CONFIG.coop.iceWait=1"
errs=[]
def check(cond,what):
    print(('ok  ' if cond else 'FAIL'),what)
    if not cond:errs.append(what)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(args=['--disable-features=WebRtcHideLocalIpsWithMdns'])
    cA=b.new_context(viewport={'width':1280,'height':760});cB=b.new_context(viewport={'width':1280,'height':760})
    A=cA.new_page();B=cB.new_page()
    for pg,n in [(A,'A'),(B,'B')]:pg.on('pageerror',lambda e,n=n: errs.append(n+': '+str(e)+' '+(e.stack or '')[:300]))
    A.goto(GAME);A.wait_for_timeout(400);A.evaluate(SETUP);A.click('#btnNew');A.click('#btnSkip');A.click('#btnStart');A.wait_for_timeout(800)
    A.evaluate("Game.changeLocation('outskirts',{x:40,y:40})");A.wait_for_timeout(1200);A.evaluate("setInterval(()=>{Game.hero.iframe=99},100)")
    A.keyboard.press('Escape');A.wait_for_timeout(200);A.click('#btnCoop2');A.wait_for_timeout(200);A.click('#btnCoopHost');A.wait_for_timeout(800)
    code=A.evaluate("Net.room");print('room',code)
    check(A.evaluate("Net.sigOk"),'хост на звʼязку із сервісом знайомства')
    A.screenshot(path=SHOTS+'net_host_panel.png')
    A.click('#btnCloseCoop');A.keyboard.press('Escape')
    B.goto(GAME);B.wait_for_timeout(400);B.evaluate(SETUP);B.click('#btnCoop1');B.wait_for_timeout(200)
    B.fill('#coopName','Далекий');B.fill('#coopCodeIn',code);B.click('#btnCoopJoin')
    for i in range(40):
        B.wait_for_timeout(250)
        if B.evaluate("Game.state")=='create':break
    check(B.evaluate("Game.state")=='create','гість через інтернет дійшов до створення героя')
    check(B.evaluate("Net.hostLink&&Net.hostLink.kind")=='rtc','гість зʼєднаний напряму (WebRTC)')
    B.evaluate("UI.cc.cls='archer'");B.fill('#heroName','Стріла');B.click('#btnStart');B.wait_for_timeout(2500)
    check(B.evaluate("Net.isGuest()&&Game.state==='play'"),'гість у грі')
    check(B.evaluate("Game.locationId")==A.evaluate("Game.locationId"),'та сама локація')
    check(A.evaluate("Net.remotes.length")==1 and B.evaluate("Net.remotes.length")==1,'гравці бачать одне одного')
    check(A.evaluate("Game.combatants.length")==B.evaluate("Game.combatants.length"),'однакові вороги')
    nid=A.evaluate("Game.combatants.find(c=>c.isEnemy&&!c.dead).nid");hp0=A.evaluate(f"Game.combatants.find(c=>c.nid==={nid}).hp")
    B.evaluate(f"hitTarget(Game.combatants.find(c=>c.nid==={nid}),{{mult:2,tags:[]}})");B.wait_for_timeout(500)
    check(A.evaluate(f"Game.combatants.find(c=>c.nid==={nid}).hp")<hp0,'удар гостя через інтернет дійшов до хоста')
    A.evaluate("Game.hero.x=37;Game.hero.y=42");A.wait_for_timeout(700)
    r=B.evaluate("(()=>{const r=Net.remotes[0];return [r.x,r.y]})()");check(abs(r[0]-37)<0.3 and abs(r[1]-42)<0.3,f'рух хоста видно {r}')
    B.screenshot(path=SHOTS+'net_guest.png')
    A.evaluate("Game.changeLocation('forest',null)");B.wait_for_timeout(2500)
    check(B.evaluate("Game.locationId")=='forest','гість перейшов разом із хостом')
    # закрита вкладка гостя — хост одразу це помічає
    B.close(run_before_unload=True);A.wait_for_timeout(1500)
    check(A.evaluate("Net.remotes.length")==0,'хост помітив, що гість закрив гру')
    check(A.evaluate("Game.flags.party['далекий'].hd.name")=='Стріла','герой гостя з інтернету збережений у хоста')
    print('ERRORS',errs[:6]);b.close()
finally:
    srv.terminate()
