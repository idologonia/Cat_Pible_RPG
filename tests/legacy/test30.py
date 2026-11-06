# Кооператив (етап 25): гості в мирному житті — торгівля, коваль, алхімія, сховище, розмови; спільні нагороди за завдання
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
OPTS="[...document.querySelectorAll('#dlgBtns button')].map(b=>b.textContent)"
def talk(pg,npc):
    pg.evaluate(f"(()=>{{const n=Game.npcs.find(n=>n.id==='{npc}');Game.hero.x=n.x+0.6;Game.hero.y=n.y+0.6;}})()");pg.wait_for_timeout(250)
    pg.evaluate(f"Game.interact(Game.npcs.find(n=>n.id==='{npc}'))");pg.wait_for_timeout(200)
    return pg.evaluate(OPTS)
def close(pg):pg.evaluate("UI.closeDialog&&UI.closeDialog();if(Game.panel)Game.closePanel();if(Game.state==='shop')Game.closeShop();");pg.wait_for_timeout(150)
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':1280,'height':760})
    A=ctx.new_page();B=ctx.new_page()
    for pg,n in [(A,'A'),(B,'B')]:pg.on('pageerror',lambda e,n=n: errs.append(n+': '+str(e)+' '+(e.stack or '')[:300]))
    A.goto(GAME);A.wait_for_timeout(400);A.click('#btnNew');A.click('#btnSkip');A.click('#btnStart');A.wait_for_timeout(1000)
    A.evaluate("setInterval(()=>{Game.hero.iframe=99},100);Net.hostRoom()");code=A.evaluate("Net.room")
    B.goto(GAME);B.wait_for_timeout(400);B.evaluate(f"Net.join('Гість','{code}','local')");B.wait_for_timeout(700);B.click('#btnStart');B.wait_for_timeout(2500)
    check(B.evaluate("Net.isGuest()&&Game.state==='play'&&Game.locationId==='city'"),'гість у Мурчанську')
    # торгівля
    o=talk(B,'magpie');print('  Сорока:',o)
    check(any('Торгувати' in x for x in o),'гість може торгувати')
    B.evaluate("Game.heroData.gold=500");close(B)
    B.evaluate("Game.interact(Game.npcs.find(n=>n.id==='magpie'))");B.wait_for_timeout(200)
    B.locator('#dlgBtns button',has_text='Торгувати').click();B.wait_for_timeout(300)
    check(B.evaluate("Game.state")=='shop','крамниця відкрилася в гостя')
    g0=B.evaluate("Game.heroData.gold");n0=B.evaluate("Game.heroData.inventory.items.length")
    B.evaluate("UI.buy(makeItem('hp_potion'),30,false)");B.wait_for_timeout(200)
    B.screenshot(path=SHOTS+'co25_shop.png')
    check(B.evaluate("Game.heroData.gold")<g0 and B.evaluate("Game.heroData.inventory.items.length")>=n0,'гість купив товар за своє золото')
    close(B)
    # коваль, алхімія, сховище
    o=talk(B,'smith');check(any('Покращення' in x for x in o),'коваль доступний гостю');close(B)
    o=talk(B,'alchemist');check(any('Варити' in x for x in o),'алхімік доступний гостю');close(B)
    o=talk(B,'banker');check(any('сховище' in x for x in o),'скарбник доступний гостю')
    B.locator('#dlgBtns button',has_text='сховище').click();B.wait_for_timeout(300)
    check(B.evaluate("Game.panel")=='stash','сховище відкрилося');close(B)
    # квестові пункти в розмові гостя замінено підказкою
    o=talk(B,'magpie');close(B)
    A.evaluate("Game.changeLocation('outskirts',{x:40,y:40})");B.wait_for_timeout(2500)
    o=talk(B,'elder');print('  Староста (гість):',o)
    check(not any('Що тут сталося' in x for x in o) and any('Про завдання' in x for x in o),'у гостя замість квестових пунктів — підказка')
    B.locator('#dlgBtns button',has_text='Про завдання').click();B.wait_for_timeout(200)
    check('хост' in B.evaluate("document.querySelector('#dlgText')?.textContent||document.querySelector('#dialog').textContent"),'підказка пояснює, що завдання веде хост')
    B.screenshot(path=SHOTS+'co25_elder.png');close(B)
    check(B.evaluate("Quests.state('main')")=='none','гість не взяв завдання сам')
    # двері, скрині й дошки — у хоста
    st=B.evaluate("(()=>{const o=Game.world.objects.find(o=>o.interact&&!o.res&&!coopGuestObject(o));Game.interact(o);return Game.state})()")
    check(st=='play','чужі обʼєкти світу гість не відкриває')
    # спільна нагорода за завдання
    g0=B.evaluate("Game.heroData.gold");x0=B.evaluate("Game.heroData.xp+Game.heroData.level*1e6")
    A.evaluate("Quests.start('main');Quests.complete('main')");B.wait_for_timeout(600)
    g1=B.evaluate("Game.heroData.gold");x1=B.evaluate("Game.heroData.xp+Game.heroData.level*1e6")
    check(g1>g0 and x1>x0,f'гість отримав нагороду за завдання загону: золото {g0}→{g1}')
    B.wait_for_timeout(2600)
    check(B.evaluate("Quests.state('main')")=='done','журнал гостя бачить виконане завдання загону')
    # досягнення гостя не повторюються, коли хост оновлює прапорці
    B.evaluate("Game.heroData.level=10");B.wait_for_timeout(2500)
    ga=B.evaluate("Game.heroData.gold")
    for i in range(3):
        A.evaluate(f"Game.flags.testTick={i}");B.wait_for_timeout(2600)
    gb=B.evaluate("Game.heroData.gold")
    check(gb==ga,f'досягнення гостя не нараховуються повторно ({ga} → {gb})')
    check(B.evaluate("Object.keys(Game.heroData.coopAch||{}).length")>0,'досягнення записані в герої гостя')
    print('ERRORS',errs[:6]);b.close()
