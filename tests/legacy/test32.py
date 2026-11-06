# Етап 27: анімація зброї (свій герой і в кооперативі), самостріл не за деревом, повільніше лікування ворогів
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
    A.goto(GAME);A.wait_for_timeout(400);A.click('#btnNew');A.click('#btnSkip');A.click('#btnStart');A.wait_for_timeout(900)
    A.evaluate("Game.changeLocation('outskirts',{x:30,y:20});setInterval(()=>{Game.hero.iframe=99},100)");A.wait_for_timeout(1300)
    # меч: базова атака запускає замах, а після нього анімація зникає
    A.evaluate("Game.hero.attackCd=0;heroBasicAttack(false)")
    check(A.evaluate("Game.hero.atkAnim&&Game.hero.atkAnim.kind")=='swing','удар мечем запускає замах')
    A.wait_for_timeout(500);A.evaluate("Render.draw(Game.world,Game.time)")
    check(A.evaluate("Game.hero.atkAnim")is None,'після замаху меч повертається на місце')
    A.evaluate("Game.hero.attackCd=5;heroBasicAttack(false)")
    check(A.evaluate("!Game.hero.atkAnim"),'під час перезарядки замаху немає')
    # навичка теж рухає зброю (довше)
    A.evaluate("Game.heroData.res=999;castSkill(0,false)")
    d=A.evaluate("Game.hero.atkAnim&&Game.hero.atkAnim.dur")
    check(d and d>CONFIG_SWING if (CONFIG_SWING:=A.evaluate("CONFIG.weaponAnim.swing")) else False,f'навичка — довший замах ({d})')
    # кооператив: гість-лучник натягує лук — хост бачить
    A.evaluate("Net.hostRoom()");code=A.evaluate("Net.room")
    B.goto(GAME);B.wait_for_timeout(400);B.evaluate(f"Net.join('Лучник','{code}','local')");B.wait_for_timeout(700)
    B.evaluate("UI.cc.cls='archer'");B.click('#btnStart');B.wait_for_timeout(2600)
    B.evaluate("Game.hero.attackCd=0;heroBasicAttack(false)");A.wait_for_timeout(250)
    check(B.evaluate("Game.hero.atkAnim&&Game.hero.atkAnim.kind")=='draw','лук гостя натягується')
    check(A.evaluate("Net.remotes[0].atkAnim&&Net.remotes[0].atkAnim.kind")=='draw','хост бачить, як гість натягує лук')
    B.evaluate("Game.hero.atkAnim.dur=1000");B.wait_for_timeout(150);B.screenshot(path=SHOTS+'w27_bow.png')
    # самостріл на тренувальному майданчику не закритий деревами
    occ=A.evaluate("""(()=>{const W=Game.world,o=W.turrets[0],sx=(o.x-o.y)*16,sy=(o.x+o.y)*8;
      return W.objects.filter(q=>q!==o&&q.spr&&q.kind!=='post'&&(q.sortKey??q.x+q.y)>o.x+o.y&&Math.abs((q.x-q.y)*16-sx)<q.spr.canvas.width/2+12&&((q.x+q.y)*8-q.spr.ay)<sy&&(q.x+q.y)*8>sy-40).map(q=>q.kind)})()""")
    check(occ==[],f'самостріл не закритий ({occ})')
    # вороги лікуються повільніше й не повністю одразу вдома
    r=A.evaluate("""(()=>{const e=Game.combatants.find(c=>c.isEnemy&&!c.dead);e.hp=Math.round(e.maxHp*0.3);e.state='return';e.x=e.home.x+0.3;e.y=e.home.y;
      for(let i=0;i<30;i++)e.update(1/30);return [e.state,+(e.hp/e.maxHp).toFixed(2)]})()""")
    check(r[0]=='idle' and r[1]<0.6,f'дійшовши додому, ворог не лікується одразу повністю {r}')
    print('ERRORS',errs[:6]);b.close()
