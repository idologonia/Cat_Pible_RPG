import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
url=GAME
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':1280,'height':760})
    pg=ctx.new_page();pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:400]))
    pg.goto(url);pg.wait_for_timeout(400)
    print('menu buttons',pg.evaluate("['btnContinue','btnLoad'].map(i=>!document.getElementById(i).classList.contains('hidden'))"))
    pg.click('#btnNew');pg.click('#btnSkip');pg.click('#classCards .cls:nth-child(2)');pg.fill('#heroName','Тестик');pg.click('#btnStart');pg.wait_for_timeout(300);pg.evaluate("Game.loadLocation('outskirts');applyWorldFlags()");pg.wait_for_timeout(500)
    print('slot',pg.evaluate('Game.saveSlot'),'saved?',pg.evaluate("!!localStorage.getItem('cpr_save_0')"))
    # progress
    pg.evaluate("gainXp(300);Game.heroData.gold=777;Inv.add(Game.heroData,generateItem('crystal_staff',3,3));Game.hero.x=30;Game.hero.y=22.5;Game.openShop('pampushka')")
    pg.wait_for_timeout(300);rare=pg.evaluate("Game.shops.pampushka.rare.map(i=>i.name)")
    pg.keyboard.press('Escape');pg.wait_for_timeout(1500)
    print('autosave after shop',pg.evaluate("JSON.parse(localStorage.getItem('cpr_save_0')).meta"))
    # manual save via pause
    pg.keyboard.press('Escape');pg.wait_for_timeout(200);pg.click('#btnSave');pg.wait_for_timeout(200)
    print('pause info',pg.evaluate("document.getElementById('pauseSaveInfo').textContent"))
    pg.screenshot(path=SHOTS+'s1_pause.png')
    st=pg.evaluate("[Game.heroData.level,Game.heroData.xp,Game.heroData.gold,Game.heroData.inventory.items.length,Math.round(Game.hero.x*10)/10,Math.round(Game.hero.y*10)/10]")
    print('state before reload',st)
    # reload page
    pg.reload();pg.wait_for_timeout(500)
    print('menu buttons',pg.evaluate("['btnContinue','btnLoad'].map(i=>!document.getElementById(i).classList.contains('hidden'))"))
    pg.click('#btnContinue');pg.wait_for_timeout(300);pg.evaluate("if(Game.locationId!=='outskirts'){Game.loadLocation('outskirts');applyWorldFlags()}");pg.wait_for_timeout(600)
    st2=pg.evaluate("[Game.heroData.level,Game.heroData.xp,Game.heroData.gold,Game.heroData.inventory.items.length,Math.round(Game.hero.x*10)/10,Math.round(Game.hero.y*10)/10]")
    print('after reload',st2,'match',st==st2,'state',pg.evaluate('Game.state'),'cls',pg.evaluate('Game.heroData.cls'),'name',pg.evaluate('Game.heroData.name'))
    print('shop rare kept',rare==pg.evaluate("Game.shops.pampushka?Game.shops.pampushka.rare.map(i=>i.name):null"))
    pg.screenshot(path=SHOTS+'s2_loaded.png')
    # second hero
    pg.keyboard.press('Escape');pg.click('#btnQuit');pg.wait_for_timeout(300)
    pg.click('#btnNew');pg.click('#btnSkip');pg.click('#raceSeg button:nth-child(2)');pg.click('#classCards .cls:nth-child(3)');pg.click('#btnStart');pg.wait_for_timeout(300);pg.evaluate("Game.loadLocation('outskirts');applyWorldFlags()");pg.wait_for_timeout(400)
    print('second slot',pg.evaluate('Game.saveSlot'))
    pg.keyboard.press('Escape');pg.click('#btnQuit');pg.wait_for_timeout(300)
    # corrupt slot 3
    pg.evaluate("localStorage.setItem('cpr_save_3','{broken')")
    pg.click('#btnLoad');pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'s3_slots.png')
    # load slot 0 from list
    pg.locator('.slotCard').nth(0).locator('button',has_text='Завантажити').click();pg.wait_for_timeout(500)
    print('loaded slot',pg.evaluate('[Game.saveSlot,Game.heroData.name]'))
    # death save
    pg.evaluate("Game.heroData.hp=1;Game.hero.x=50;Game.hero.y=46");pg.wait_for_timeout(3500)
    print('dead state',pg.evaluate('Game.state'))
    pg.click('#btnRespawn');pg.wait_for_timeout(1500)
    print('after respawn save gold',pg.evaluate("JSON.parse(localStorage.getItem('cpr_save_0')).meta.gold"))
    # storage failure simulation
    pg.evaluate("(()=>{Object.defineProperty(Storage.prototype,'setItem',{configurable:true,value:function(){const e=new Error('q');e.name='QuotaExceededError';throw e;}});})()")
    pg.keyboard.press('Escape');pg.click('#btnSave');pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'s4_err.png')
    print('ERRORS',errs)
    # private mode
    c2=b.new_context();p2=c2.new_page();p2.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('denied')}})")
    p2.on('pageerror',lambda e: errs.append('P2:'+str(e)))
    p2.goto(url);p2.wait_for_timeout(400);p2.click('#btnNew');p2.click('#btnSkip');p2.click('#btnStart');p2.wait_for_timeout(300);p2.evaluate("Game.loadLocation('outskirts');applyWorldFlags()");p2.wait_for_timeout(600)
    print('private state',p2.evaluate('[Game.state,Game.saveSlot]'));p2.screenshot(path=SHOTS+'s5_private.png')
    print('ERRORS',errs)
    b.close()
