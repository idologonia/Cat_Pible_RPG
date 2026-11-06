# Кооператив: хост і гість у двох вкладках. Кожен ходить своїми локаціями; локацію рахує той, хто прийшов першим;
# завдання спільні; з одним мешканцем говорить лише один гравець
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
def wait_loc(pg,loc,ms=4000):
    for i in range(ms//200):
        if pg.evaluate("Game.locationId")==loc and pg.evaluate("Game.state")=='play':return True
        pg.wait_for_timeout(200)
    return False
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':1280,'height':760})
    A=ctx.new_page();B=ctx.new_page()
    for pg,n in [(A,'A'),(B,'B')]:pg.on('pageerror',lambda e,n=n: errs.append(n+': '+str(e)+' '+(e.stack or '')[:300]))
    A.goto(GAME);A.wait_for_timeout(400);A.click('#btnNew');A.click('#btnSkip');A.click('#btnStart');A.wait_for_timeout(800)
    A.evaluate("Game.heroData.level=4;Game.changeLocation('outskirts',{x:40,y:40})");A.wait_for_timeout(1200)
    A.evaluate("setInterval(()=>{if(Game.hero)Game.hero.iframe=99},100)")
    A.keyboard.press('Escape');A.wait_for_timeout(200);A.click('#btnCoop2');A.wait_for_timeout(200)
    check(A.locator('#btnCoopJoinLocal').count()==0,'кнопки «З іншої вкладки» немає')
    check(A.locator('#coopSrv').count()==0,'поля «Сервер» немає')
    A.click('#btnCoopHost');A.wait_for_timeout(300)
    code=A.evaluate("Net.room");print('room',code)
    A.screenshot(path=SHOTS+'co_host_panel.png')
    A.click('#btnCloseCoop');A.keyboard.press('Escape');A.wait_for_timeout(200)
    # гість без героя — створює його
    B.goto(GAME);B.wait_for_timeout(400);B.click('#btnCoop1');B.wait_for_timeout(200)
    check(B.locator('#btnCoopJoinLocal').count()==0 and B.locator('#coop .invHint').count()==0,'у вікні гостя немає зайвих кнопок і пояснень')
    B.evaluate(f"Net.join('Друг','{code}','local')");B.wait_for_timeout(800)
    check(B.evaluate("Game.state")=='create','гість без героя потрапляє на створення героя')
    B.evaluate("UI.cc.cls='mage'");B.fill('#heroName','Мурчик');B.click('#btnStart');B.wait_for_timeout(2500)
    check(B.evaluate("Net.isGuest()&&Game.state==='play'")and B.evaluate("Game.locationId")=='outskirts','гість з’явився біля хоста')
    check(A.evaluate("Net.remotes.length")==1 and B.evaluate("Net.remotes.length")==1,'кожен бачить іншого героя')
    check(B.evaluate("Net._mirror")==True and A.evaluate("Net._mirror")==False,'локацію рахує хост (прийшов першим)')
    nA=A.evaluate("Game.combatants.length");nB=B.evaluate("Game.combatants.length")
    check(nA==nB and nB>0,f'гість бачить тих самих ворогів ({nA}/{nB})')
    check(A.evaluate("Game.combatants.filter(c=>c.isEnemy&&!c.dead).every(c=>c._cm===1+CONFIG.coop.enemyHpPerPlayer)"),'вороги міцніші для двох гравців')
    # удар гостя, удар ворога по гостю, досвід, здобич
    nid=A.evaluate("Game.combatants.find(c=>c.isEnemy&&!c.dead).nid");hp0=A.evaluate(f"Game.combatants.find(c=>c.nid==='{nid}').hp")
    B.evaluate(f"hitTarget(Game.combatants.find(c=>c.nid==='{nid}'),{{mult:1.5,tags:['fire'],status:{{burn:{{dur:3,dps:4}}}}}})");B.wait_for_timeout(400)
    check(A.evaluate(f"Game.combatants.find(c=>c.nid==='{nid}').hp")<hp0,'удар гостя дійшов до хоста')
    B.evaluate("Game.hero.iframe=0");B.evaluate("setInterval(()=>{if(Game.heroData&&Game.heroData.hp<20)Game.heroData.hp=Game.derived.maxHp},200)")
    g0=B.evaluate("Game.heroData.hp")
    A.evaluate(f"(()=>{{const e=Game.combatants.find(c=>c.nid==='{nid}');const r=Net.remotes[0];Game.hero.x=e.x+12;Game.hero.y=e.y+12;e.x=r.tx+0.6;e.y=r.ty;e.state='fight';}})()")
    for i in range(30):
        B.evaluate(f"(()=>{{const e=Game.combatants.find(c=>c.nid==='{nid}');if(e){{Game.hero.iframe=0;Game.hero.x=e.x-0.6;Game.hero.y=e.y;}}}})()");B.wait_for_timeout(150)
        if B.evaluate("Game.heroData.hp")<g0:break
    check(B.evaluate("Game.heroData.hp")<g0,'ворог поранив гостя')
    B.evaluate("Game.hero.iframe=99")
    A.evaluate("Game.hero.x=38;Game.hero.y=41")
    xp0=B.evaluate("Game.heroData.xp+Game.heroData.level*1e6")
    B.evaluate(f"(()=>{{const e=Game.combatants.find(c=>c.nid==='{nid}');for(let i=0;i<40&&!e.dead;i++)dealRaw(e,9999,'#fff')}})()");B.wait_for_timeout(600)
    check(A.evaluate(f"Game.combatants.find(c=>c.nid==='{nid}').dead"),'ворог загинув у хоста')
    check(B.evaluate("Game.heroData.xp+Game.heroData.level*1e6")>xp0,'гість отримав досвід')
    A.evaluate("Game.coins.length=0;Game.groundItems.length=0");B.wait_for_timeout(300)
    g0=B.evaluate("Game.heroData.gold")
    A.evaluate("(()=>{const r=Net.remotes[0];dropCoins(r.tx,r.ty,40);dropItem(r.tx+0.3,r.ty,makeItem('hp_potion'))})()");B.wait_for_timeout(900)
    check(B.evaluate("Game.heroData.gold")>g0 and A.evaluate("Game.coins.length")==0,'гість підібрав монети, у хоста вони зникли')
    pot0=B.evaluate("Inv.count(Game.heroData,'hp_potion')")
    B.evaluate("(()=>{const g=Game.groundItems.find(g=>g.it.base==='hp_potion');Game.hero.x=g.x;Game.hero.y=g.y;Game.interact(g)})()");B.wait_for_timeout(600)
    check(B.evaluate("Inv.count(Game.heroData,'hp_potion')")==pot0+1 and A.evaluate("Game.groundItems.length")==0,'гість підібрав зілля')
    # загубились вороги в копії (як при поганому зв'язку) — гра сама просить їх заново
    B.evaluate("Net.mirrors=new Map();Game.combatants=[];Net._snapT=0")
    for i in range(30):
        B.wait_for_timeout(200)
        if B.evaluate("Game.combatants.length")>0:break
    check(B.evaluate("Game.combatants.length")==A.evaluate("Game.combatants.length"),'копія локації сама відновилась')
    # без паузи
    A.keyboard.press('Escape');A.wait_for_timeout(150);t0=A.evaluate("Game.flags.clock");A.wait_for_timeout(800)
    check(A.evaluate("Game.state")=='pause' and A.evaluate("Game.flags.clock")>t0,'пауза не зупиняє світ');A.keyboard.press('Escape')
    # хост іде в ліс — гість лишається й сам рахує Околиці
    A.evaluate("Game.changeLocation('forest',null)");A.wait_for_timeout(2200)
    check(B.evaluate("Game.locationId")=='outskirts','хост пішов — гість лишився на своїй локації')
    B.wait_for_timeout(800)
    check(B.evaluate("Net._mirror")==False,'тепер Околиці рахує гість')
    check(B.evaluate("Net.remotes.length")==0 and A.evaluate("Net.remotes.length")==0,'гравці на різних локаціях не бачать одне одного')
    alive=B.evaluate("Game.combatants.filter(c=>c.isEnemy&&!c.dead).length")
    check(alive>0 and B.evaluate("Game.combatants.every(c=>!c.mirror)"),f'вороги в гостя тепер справжні ({alive})')
    check(B.evaluate("Game.combatants.filter(c=>c.isEnemy&&!c.dead).every(c=>(c._cm||1)===1)"),'гість сам — вороги вже не підсилені на двох')
    e2=B.evaluate("(()=>{const e=Game.combatants.find(c=>c.isEnemy&&!c.dead);const h=Game.hero;h.x=e.x-0.8;h.y=e.y;return [e.state,e.hp]})()");B.wait_for_timeout(1500)
    check(B.evaluate("Game.combatants.some(c=>c.isEnemy&&!c.dead&&c.state==='fight')"),'вороги гостя самі нападають')
    # гість сам іде в ліс — бачить хоста, ліс рахує хост
    B.evaluate("Game.changeLocation('forest',null)")
    check(wait_loc(B,'forest'),'гість сам перейшов у ліс')
    B.wait_for_timeout(1200)
    check(B.evaluate("Net._mirror")==True and B.evaluate("Net.remotes.length")==1,'у лісі гість бачить хоста й копії його ворогів')
    check(A.evaluate("Game.combatants.length")==B.evaluate("Game.combatants.length"),'вороги в лісі однакові')
    # підземелля: хост першим, гість слідом — коридори однакові; хост іде — гість рахує склеп
    A.evaluate("Game.changeLocation('crypt',null)");wait_loc(A,'crypt');A.wait_for_timeout(600)
    B.evaluate("Game.changeLocation('crypt',null)");check(wait_loc(B,'crypt'),'гість спустився в склеп')
    B.wait_for_timeout(1200)
    ta=A.evaluate("Array.from(Game.world.tiles).join('')");tb=B.evaluate("Array.from(Game.world.tiles).join('')")
    check(ta==tb,'склеп однаковий у хоста й гостя')
    check(A.evaluate("Game.combatants.length")==B.evaluate("Game.combatants.length"),'вороги склепу однакові')
    A.screenshot(path=SHOTS+'co_crypt_host.png');B.screenshot(path=SHOTS+'co_crypt_guest.png')
    A.evaluate("Game.changeLocation('city',null)");wait_loc(A,'city');B.wait_for_timeout(1200)
    check(B.evaluate("Game.locationId")=='crypt' and B.evaluate("Net._mirror")==False,'хост пішов зі склепу — тепер склеп рахує гість')
    B.evaluate("Game.changeLocation('city',null)");wait_loc(B,'city');B.wait_for_timeout(1000)
    # спільні завдання: гість бере завдання в старости — у хоста воно теж активне
    A.evaluate("Game.changeLocation('outskirts',{x:30,y:20})");wait_loc(A,'outskirts')
    B.evaluate("Game.changeLocation('outskirts',{x:31,y:20})");wait_loc(B,'outskirts');B.wait_for_timeout(1000)
    B.evaluate("(()=>{const n=Game.npcs.find(n=>n.id==='elder');Game.hero.x=n.x+0.6;Game.hero.y=n.y+0.6;Game.interact(n)})()");B.wait_for_timeout(300)
    opts=B.evaluate("[...document.querySelectorAll('#dlgBtns button')].map(b=>b.textContent)");print('  гість у старости:',opts)
    check(any('Що тут сталося' in o for o in opts),'гість бачить пункт завдання')
    # хост тим часом намагається заговорити зі старостою — зайнято
    A.wait_for_timeout(300)
    A.evaluate("(()=>{const n=Game.npcs.find(n=>n.id==='elder');Game.hero.x=n.x-0.6;Game.hero.y=n.y+0.6;Game.interact(n)})()");A.wait_for_timeout(300)
    check(A.evaluate("Game.state")!='dialog' and 'розмовляє' in A.evaluate("$('toast').textContent"),'хост не може заговорити з мешканцем, з яким говорить гість')
    B.locator('#dlgBtns button',has_text='Що тут сталося').click();B.wait_for_timeout(150)
    B.locator('#dlgBtns button',has_text='Далі').click();B.wait_for_timeout(150)
    B.locator('#dlgBtns button',has_text='Я з’ясую').click();B.wait_for_timeout(300)
    B.evaluate("UI.closeDialog()");B.wait_for_timeout(2500)
    check(A.evaluate("Quests.state('main')")=='active','завдання, взяте гостем, активне й у хоста')
    A.evaluate("(()=>{const n=Game.npcs.find(n=>n.id==='elder');Game.interact(n)})()");A.wait_for_timeout(300)
    check(A.evaluate("Game.state")=='dialog','після розмови гостя хост може говорити з мешканцем');A.evaluate("UI.closeDialog()")
    # виконане хостом завдання — нагорода й гостю
    g0=B.evaluate("Game.heroData.gold");A.evaluate("Quests.complete('main')");B.wait_for_timeout(700)
    check(B.evaluate("Game.heroData.gold")>g0,'нагорода за завдання загону дісталась гостю')
    B.wait_for_timeout(2500);check(B.evaluate("Quests.state('main')")=='done','журнал гостя бачить виконане завдання')
    # гонка: гість бере завдання, хост одразу його виконує — у всіх «виконано», нічого не повертається назад
    B.evaluate("Quests.start('training')");A.wait_for_timeout(1300);A.evaluate("Quests.st.training&&Quests.complete('training')");B.wait_for_timeout(5000)
    check(A.evaluate("Quests.state('training')")=='done' and B.evaluate("Quests.state('training')")=='done','зміни завдань не перезаписують одна одну')
    # згорнуті вкладки, вихід і повернення
    HIDE="""(()=>{window.requestAnimationFrame=()=>0;Object.defineProperty(document,'hidden',{get:()=>true,configurable:true});document.dispatchEvent(new Event('visibilitychange'));})()"""
    B.evaluate("Game.heroData.gold=777");B.wait_for_timeout(5600)
    A.evaluate(HIDE);B.wait_for_timeout(8000)
    check(B.evaluate("Net.isGuest()&&Game.state==='play'"),'гість не вилітає, коли вкладку хоста згорнуто')
    B.evaluate("Net.leave()");A.wait_for_timeout(1500)
    check(A.evaluate("Net.remotes.length")==0 and A.evaluate("Object.keys(Net.peers).length")==0,'хост бачить, що гість вийшов')
    check(A.evaluate("Game.flags.party['друг'].hd.gold")==777,'прогрес гостя збережено в хоста')
    B.evaluate(f"Net.join('Друг','{code}','local')");B.wait_for_timeout(2500)
    check(B.evaluate("Net.isGuest()&&Game.heroData&&Game.heroData.name==='Мурчик'&&Game.heroData.gold===777"),'гість повернувся тим самим героєм')
    A.evaluate("Net.closeRoom()");B.wait_for_timeout(800)
    check(B.evaluate("Game.state")=='menu' and not B.evaluate("Net.role"),'гість повертається в меню, коли хост закриває кімнату')
    print('ERRORS',errs[:6]);b.close()
