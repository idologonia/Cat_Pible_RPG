import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':760})
    pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:400]))
    pg.goto(GAME);pg.wait_for_timeout(400);pg.click('#btnNew');pg.click('#btnSkip');pg.click('#btnStart');pg.wait_for_timeout(600)
    pg.evaluate("Game.changeLocation('outskirts',{x:47,y:40})");pg.wait_for_timeout(1300)
    pg.evaluate("Game.heroData.hp=99999;Game.derived.maxHp=99999")
    pg.evaluate("for(const c of [...Game.combatants])if(c.isEnemy&&!c.dead){c.hp=1;hitTarget(c,{mult:900});}");pg.wait_for_timeout(2500)
    print('stats',pg.evaluate("JSON.stringify(Game.flags.stats)"),'rep',pg.evaluate("JSON.stringify(Game.flags.rep)"),'ach',pg.evaluate("Object.keys(Game.flags.ach||{})"))
    pg.evaluate("addRep('murch',400)");pg.wait_for_timeout(1500)
    print('tier',pg.evaluate("[repTier('murch'),repOf('murch')]"))
    pg.evaluate("Game.openShop('pampushka')");pg.wait_for_timeout(200);print('priceMod',pg.evaluate("priceMod()"));pg.evaluate("Game.closeShop()")
    # набори
    print('set gen',pg.evaluate("(()=>{let n=0;for(let i=0;i<200;i++){const it=generateItem('chainmail',10,2);if(it.set)n++;}return n})()"))
    pg.evaluate("""(()=>{const hd=Game.heroData;for(const [b,sl] of [['knight_helm','helmet'],['chainmail','armor'],['iron_gauntlets','gloves'],['iron_boots','boots']]){let it;do{it=generateItem(b,10,2);}while(!it.set);hd.equipment[sl]=it;}Game.onEquipChange();})()""")
    print('set bonus',pg.evaluate("(()=>{const d=Game.derived;return [d.armor,d.maxHp,d.atkMin,setCount(Game.heroData,'guard')]})()"))
    print('tip',pg.evaluate("UI.itemTip(Game.heroData.equipment.armor).replace(/<[^>]+>/g,' | ').slice(-260)"))
    pg.wait_for_timeout(2500);print('ach',pg.evaluate("Object.keys(Game.flags.ach||{})"))
    pg.evaluate("UI.openJournal();Game.state='journal'");pg.wait_for_timeout(200);pg.evaluate("UI.setJTab('rep')");pg.wait_for_timeout(200);pg.screenshot(path=SHOTS+'d1_rep.png')
    pg.evaluate("UI.setJTab('ach')");pg.wait_for_timeout(200);pg.screenshot(path=SHOTS+'d2_ach.png')
    pg.evaluate("UI.setJTab('q')");pg.wait_for_timeout(100)
    pg.evaluate("Game.manualSave()");pg.wait_for_timeout(300)
    print('ERRORS',errs[:5]);b.close()
