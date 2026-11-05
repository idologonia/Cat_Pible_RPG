# Кооператив (частина 1): хост і гість у двох вкладках одного браузера
import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
errs=[]
def check(cond,what):
    print(('ok  ' if cond else 'FAIL'),what)
    if not cond:errs.append(what)
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':1280,'height':760})
    A=ctx.new_page();B=ctx.new_page()
    for pg,n in [(A,'A'),(B,'B')]:pg.on('pageerror',lambda e,n=n: errs.append(n+': '+str(e)+' '+(e.stack or '')[:300]))
    # хост
    A.goto(GAME);A.wait_for_timeout(400);A.click('#btnNew');A.click('#btnSkip');A.click('#btnStart');A.wait_for_timeout(800)
    A.evaluate("Game.heroData.level=4;Game.changeLocation('outskirts',{x:40,y:40})");A.wait_for_timeout(1200)
    A.evaluate("setInterval(()=>{Game.hero.iframe=99},100)")
    A.keyboard.press('Escape');A.wait_for_timeout(200);A.click('#btnCoop2');A.wait_for_timeout(200);A.click('#btnCoopHost');A.wait_for_timeout(200)
    code=A.evaluate("Net.room");print('room',code)
    A.screenshot(path=SHOTS+'co_host_panel.png')
    A.click('#btnCloseCoop');A.keyboard.press('Escape');A.wait_for_timeout(200)
    # гість: невідомий — створює героя
    B.goto(GAME);B.wait_for_timeout(400);B.click('#btnCoop1');B.wait_for_timeout(200)
    B.fill('#coopName','Друг');B.fill('#coopCodeIn',code);B.click('#btnCoopJoin');B.wait_for_timeout(800)
    check(B.evaluate("Game.state")=='create','гість без героя потрапляє на створення героя')
    B.evaluate("UI.cc.cls='mage'");B.fill('#heroName','Мурчик');B.click('#btnStart');B.wait_for_timeout(2500)
    check(B.evaluate("Net.isGuest()&&Game.state==='play'"),'гість у грі')
    check(B.evaluate("Game.locationId")==A.evaluate("Game.locationId"),'гість на тій самій локації')
    check(A.evaluate("Net.remotes.length")==1 and B.evaluate("Net.remotes.length")==1,'кожен бачить іншого героя')
    check(A.evaluate("!!Game.flags.party['друг']&&Game.flags.party['друг'].hd.name==='Мурчик'"),'герой гостя збережений у хоста')
    nA=A.evaluate("Game.combatants.length");nB=B.evaluate("Game.combatants.length")
    check(nA==nB and nB>0,f'гість бачить тих самих ворогів ({nA}/{nB})')
    check(B.evaluate("Game.combatants.every(c=>c.mirror)"),'у гостя лише копії ворогів')
    print('hp scale',A.evaluate("(()=>{const e=Game.combatants.find(c=>c.isEnemy&&!c.dead);return [e._cm,e.maxHp]})()"))
    check(A.evaluate("Game.combatants.filter(c=>c.isEnemy&&!c.dead).every(c=>c._cm===1+CONFIG.coop.enemyHpPerPlayer)"),'вороги міцніші для двох гравців')
    # рух хоста видно в гостя
    A.evaluate("Game.hero.x=38;Game.hero.y=41");A.wait_for_timeout(700)
    hp=B.evaluate("(()=>{const r=Net.remotes.find(r=>r.pid==='host');return [r.x,r.y]})()")
    check(abs(hp[0]-38)<0.3 and abs(hp[1]-41)<0.3,f'позиція хоста в гостя {hp}')
    A.screenshot(path=SHOTS+'co_host.png');B.screenshot(path=SHOTS+'co_guest.png')
    # удар гостя по ворогу
    nid=A.evaluate("(()=>{const e=Game.combatants.find(c=>c.isEnemy&&!c.dead);return e.nid})()")
    hp0=A.evaluate(f"Game.combatants.find(c=>c.nid==={nid}).hp")
    B.evaluate(f"(()=>{{const e=Game.combatants.find(c=>c.nid==={nid});hitTarget(e,{{mult:1.5,tags:['fire'],status:{{burn:{{dur:3,dps:4}}}}}})}})()");B.wait_for_timeout(400)
    hp1,burn=A.evaluate(f"(()=>{{const e=Game.combatants.find(c=>c.nid==={nid});return [e.hp,e.st.burn||0]}})()")
    check(hp1<hp0 and burn>0,f'удар гостя дійшов до хоста: {hp0} → {hp1}, горіння {burn:.1f}')
    check(A.evaluate(f"Game.combatants.find(c=>c.nid==={nid}).state")=='fight','ворог після удару гостя бʼється')
    # ворог б'є гостя
    B.evaluate("setInterval(()=>{if(Game.heroData&&Game.heroData.hp<20)Game.heroData.hp=Game.derived.maxHp},200)")
    g0=B.evaluate("Game.heroData.hp")
    A.evaluate(f"(()=>{{const e=Game.combatants.find(c=>c.nid==={nid});const r=Net.remotes[0];Game.hero.x=e.x+12;Game.hero.y=e.y+12;e.x=r.tx+0.6;e.y=r.ty;e.state='fight';}})()")
    for i in range(30):
        B.evaluate(f"(()=>{{const e=Game.combatants.find(c=>c.nid==={nid});Game.hero.x=e.x-0.6;Game.hero.y=e.y;}})()");B.wait_for_timeout(150)
        if B.evaluate("Game.heroData.hp")<g0:break
    g1=B.evaluate("Game.heroData.hp")
    check(g1<g0,f'ворог хоста поранив гостя: {g0} → {g1}')
    A.evaluate("Game.hero.x=38;Game.hero.y=41")
    # гість добиває ворога — досвід і подія вбивства
    xp0=B.evaluate("Game.heroData.xp")
    B.evaluate(f"(()=>{{const e=Game.combatants.find(c=>c.nid==={nid});for(let i=0;i<40&&!e.dead;i++)dealRaw(e,9999,'#fff')}})()");B.wait_for_timeout(600)
    check(A.evaluate(f"Game.combatants.find(c=>c.nid==={nid}).dead"),'ворог загинув у хоста')
    check(B.evaluate(f"Game.combatants.find(c=>c.nid==={nid}).dead"),'і в гостя')
    xp1=B.evaluate("Game.heroData.xp");check(xp1>xp0 or B.evaluate("Game.heroData.level")>1,f'гість отримав досвід {xp0} → {xp1}')
    # монети й речі: хто перший
    g0=B.evaluate("Game.heroData.gold")
    A.evaluate("Game.coins.length=0;Game.groundItems.length=0");B.wait_for_timeout(300)
    A.evaluate("(()=>{const r=Net.remotes[0];dropCoins(r.tx,r.ty,40);dropItem(r.tx+0.3,r.ty,makeItem('hp_potion'))})()");B.wait_for_timeout(900)
    g1=B.evaluate("Game.heroData.gold");check(g1>g0,f'гість підібрав монети {g0} → {g1}')
    check(A.evaluate("Game.coins.length")==0,'монети зникли в хоста')
    B.evaluate("(()=>{const g=Game.groundItems.find(g=>g.it.base==='hp_potion');Game.hero.x=g.x;Game.hero.y=g.y;})()");B.wait_for_timeout(200)
    pot0=B.evaluate("Inv.count(Game.heroData,'hp_potion')")
    B.evaluate("Game.interact(Game.groundItems.find(g=>g.it.base==='hp_potion'))");B.wait_for_timeout(600)
    check(B.evaluate("Inv.count(Game.heroData,'hp_potion')")==pot0+1 and A.evaluate("Game.groundItems.length")==0,'гість підібрав зілля, у хоста воно зникло')
    # навичка гостя: вогняна куля летить і влучає у ворога хоста
    nid2=A.evaluate("(()=>{const r=Net.remotes[0];const e=Game.combatants.filter(c=>c.isEnemy&&!c.dead).sort((a,b)=>Math.hypot(a.x-r.tx,a.y-r.ty)-Math.hypot(b.x-r.tx,b.y-r.ty))[0];return e.nid})()")
    B.evaluate(f"(()=>{{const e=Game.combatants.find(c=>c.nid==={nid2});Game.hero.x=e.x-3;Game.hero.y=e.y;Game.heroData.res=999;}})()");B.wait_for_timeout(500)
    h0=A.evaluate(f"Game.combatants.find(c=>c.nid==={nid2}).hp")
    B.evaluate(f"(()=>{{const e=Game.combatants.find(c=>c.nid==={nid2});const [sx,sy]=Render.worldToScreenCss(e.x,e.y,20);Input.mouse.x=sx;Input.mouse.y=sy;Input.mouse.inside=true;Input.mouse.moved=Game.time;castSkill(0,false);}})()")
    B.wait_for_timeout(250);B.screenshot(path=SHOTS+'co_guest_fireball.png');A.screenshot(path=SHOTS+'co_host_sees_fireball.png')
    B.wait_for_timeout(900)
    h1=A.evaluate(f"Game.combatants.find(c=>c.nid==={nid2}).hp")
    check(h1<h0,f'вогняна куля гостя поранила ворога в хоста: {h0} → {h1}')
    # гість гине й воскресає біля хоста
    B.evaluate("Game.heroData.hp=1;Game.hero.iframe=0;heroTakeDamage(999,Game.hero.x+1,Game.hero.y)");B.wait_for_timeout(1600)
    check(B.evaluate("Game.state")=='dead','гість загинув')
    check(A.evaluate("Net.remotes[0].dead"),'хост бачить, що гість загинув')
    B.evaluate("Game.respawn()");B.wait_for_timeout(500)
    d=B.evaluate("(()=>{const r=Net.remotes.find(r=>r.pid==='host');return [Game.state,Game.locationId,Math.hypot(r.x-Game.hero.x,r.y-Game.hero.y)]})()")
    check(d[0]=='play' and d[1]=='outskirts' and d[2]<3,f'гість воскрес біля хоста {d}')
    # гість не може піти сам
    B.evaluate("Game.changeLocation('city',null)");B.wait_for_timeout(600)
    check(B.evaluate("Game.locationId")=='outskirts','гість не переходить сам')
    # без паузи: хост у меню паузи, а світ живе
    A.keyboard.press('Escape');A.wait_for_timeout(150)
    t0=A.evaluate("Game.flags.clock");A.wait_for_timeout(800);t1=A.evaluate("Game.flags.clock")
    check(A.evaluate("Game.state")=='pause' and t1>t0,'у кооперативі пауза не зупиняє світ')
    A.keyboard.press('Escape');A.wait_for_timeout(150)
    # перехід хоста: гість іде слідом, у підземеллі ті самі коридори
    A.evaluate("Game.changeLocation('crypt',null)");A.wait_for_timeout(2500)
    check(B.evaluate("Game.locationId")=='crypt','гість спустився в склеп разом із хостом')
    ta=A.evaluate("Array.from(Game.world.tiles).join('')");tb=B.evaluate("Array.from(Game.world.tiles).join('')")
    check(ta==tb,'склеп однаковий у хоста й гостя')
    check(A.evaluate("Game.combatants.length")==B.evaluate("Game.combatants.length"),'вороги склепу однакові')
    A.screenshot(path=SHOTS+'co_crypt_host.png');B.screenshot(path=SHOTS+'co_crypt_guest.png')
    A.evaluate("Game.changeLocation('outskirts',{x:40,y:40})");A.wait_for_timeout(2500)
    check(B.evaluate("Game.locationId")=='outskirts','гість повернувся разом із хостом')
    # гість виходить і повертається — той самий герой
    B.evaluate("Game.heroData.level=3;Game.heroData.gold=777");B.wait_for_timeout(5600)
    B.evaluate("Net.leave()");B.wait_for_timeout(600)
    check(A.evaluate("Net.remotes.length")==0,'хост бачить, що гість вийшов')
    check(A.evaluate("Game.flags.party['друг'].hd.gold")==777,'прогрес гостя збережено в хоста')
    B.click('#btnCoop1');B.wait_for_timeout(200);B.fill('#coopCodeIn',code);B.click('#btnCoopJoin');B.wait_for_timeout(2500)
    check(B.evaluate("Net.isGuest()&&Game.heroData&&Game.heroData.name==='Мурчик'&&Game.heroData.gold===777"),'гість повернувся тим самим героєм')
    # хост закриває кімнату
    A.evaluate("Net.closeRoom()");A.wait_for_timeout(600)
    check(B.evaluate("Game.state")=='menu' and not B.evaluate("Net.role"),'гість повертається в меню, коли хост закриває кімнату')
    print('ERRORS',errs[:6]);b.close()
