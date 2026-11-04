import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
url=GAME
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':760})
    pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:400]))
    pg.goto(url);pg.wait_for_timeout(400);pg.click('#btnNew');pg.click('#btnSkip');pg.click('#btnStart');pg.wait_for_timeout(300);pg.evaluate("Game.loadLocation('outskirts');applyWorldFlags()");pg.wait_for_timeout(500)
    pg.evaluate("Game.heroData.gold=200;for(let r=0;r<3;r++)Inv.add(Game.heroData,generateItem(pickLootBase(),2,r))")
    pg.evaluate('Game.hero.x=18.9;Game.hero.y=28.0');pg.wait_for_timeout(300)
    pg.keyboard.press('KeyE');pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'t1_dialog.png')
    pg.locator('#dlgBtns button',has_text='Торгувати').click();pg.wait_for_timeout(300)
    print('state',pg.evaluate('Game.state'))
    pg.screenshot(path=SHOTS+'t2_shop.png')
    n0=pg.evaluate("Inv.count(Game.heroData,'hp_potion')")
    pg.locator('#shopStock .shopRow button').nth(0).click();pg.wait_for_timeout(100)
    print('bought potion',n0,pg.evaluate("Inv.count(Game.heroData,'hp_potion')"),pg.evaluate('Game.heroData.gold'))
    pg.locator('#shopRare .shopRow button').nth(0).click();pg.wait_for_timeout(100)
    print('rare left',pg.evaluate("Game.shops.pampushka.rare.length"),pg.evaluate('Game.heroData.gold'))
    cnt=pg.evaluate('Game.heroData.inventory.items.length')
    pg.locator('#shopInv .invItem').nth(cnt-1).dblclick();pg.wait_for_timeout(150)
    print('sold',cnt,pg.evaluate('Game.heroData.inventory.items.length'),pg.evaluate('Game.heroData.gold'),'buyback',pg.evaluate('Game.shops.pampushka.buyback.length'))
    pg.locator('#shopInv .invItem').nth(0).click();pg.wait_for_timeout(150)
    pg.screenshot(path=SHOTS+'t3_shop.png')
    pg.locator('#shopBuyback .shopRow button').nth(0).click();pg.wait_for_timeout(150)
    print('buyback',pg.evaluate('Game.shops.pampushka.buyback.length'),pg.evaluate('Game.heroData.gold'))
    pg.keyboard.press('Escape');pg.wait_for_timeout(150);print('state',pg.evaluate('Game.state'))
    # restock
    pg.evaluate('Game.shops.pampushka.refreshAt=Game.time+0.5');pg.keyboard.press('KeyE');pg.wait_for_timeout(200);pg.locator('#dlgBtns button',has_text='Торгувати').click();pg.wait_for_timeout(1500)
    print('restocked',pg.evaluate("Game.shops.pampushka.rare.length"))
    print('ERRORS',errs)
    m=b.new_context(viewport={'width':390,'height':844},has_touch=True,is_mobile=True,device_scale_factor=2).new_page()
    m.goto(url);m.wait_for_timeout(400);m.tap('#btnNew');m.tap('#btnSkip');m.tap('#btnStart');m.wait_for_timeout(300);m.evaluate("Game.loadLocation('outskirts');applyWorldFlags()");m.wait_for_timeout(400)
    m.evaluate("Game.openShop('pampushka')");m.wait_for_timeout(300);m.screenshot(path=SHOTS+'t4_mob.png')
    b.close()
