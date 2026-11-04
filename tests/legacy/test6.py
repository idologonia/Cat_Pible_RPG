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
    print('inv start',pg.evaluate("Game.heroData.inventory.items.map(e=>e.it.name+'x'+(e.it.qty||1)+'@'+e.x+','+e.y)"),pg.evaluate('Game.heroData.gold'))
    # kill patrol with god mode to get loot/xp
    pg.evaluate('Game.hero.x=50;Game.hero.y=34.5;Game.heroData.hp=9999;Game.derived.maxHp=9999;const [a,b]=Render.proj(50,34.5);Game.cam.x=a;Game.cam.y=b-12')
    for i in range(30):
        tgt=pg.evaluate("(()=>{const h=Game.hero;let b=null,bd=99;for(const c of Game.combatants)if(c.isEnemy&&!c.dead&&c.state==='fight'){const d=Math.hypot(c.x-h.x,c.y-h.y);if(d<bd){bd=d;b=c;}}return b?Render.worldToScreenCss(b.x,b.y,20):null})()")
        if not tgt and i>3: break
        if tgt: pg.mouse.move(tgt[0],tgt[1])
        pg.mouse.down();pg.wait_for_timeout(500);pg.mouse.up();pg.evaluate('Game.heroData.res=Game.derived.maxRes')
    print('xp',pg.evaluate('[Game.heroData.level,Game.heroData.xp,Game.heroData.statPoints]'),'ground',pg.evaluate("Game.groundItems.map(g=>g.it.name+'/'+g.it.rarity)"),'coins',pg.evaluate('Game.coins.length'))
    # force a set of rare drops near hero
    pg.evaluate("""for(let r=0;r<5;r++)dropItem(Game.hero.x+1,Game.hero.y+0.5,generateItem(pickLootBase(),3,r));dropItem(Game.hero.x+1,Game.hero.y,generateItem('greatsword',3,3));dropItem(Game.hero.x+1,Game.hero.y,generateItem('iron_shield',2,2));Game.heroData.hp=50;Game.derived.maxHp=128;Game.refreshHero();""")
    pg.wait_for_timeout(1500)
    pg.screenshot(path=SHOTS+'l1_loot.png')
    # pick up everything via E
    for i in range(12):
        pg.evaluate("const g=Game.groundItems[0];if(g){Game.hero.x=g.x;Game.hero.y=g.y+0.2;}")
        pg.wait_for_timeout(80);pg.keyboard.press('KeyE');pg.wait_for_timeout(80)
    print('after pickup ground',len(pg.evaluate('Game.groundItems')),'inv',pg.evaluate("Game.heroData.inventory.items.length"),'gold',pg.evaluate('Game.heroData.gold'))
    # open inventory
    pg.keyboard.press('KeyI');pg.wait_for_timeout(300);print('state',pg.evaluate('Game.state'))
    pg.screenshot(path=SHOTS+'l2_inv.png')
    # equip greatsword via dblclick
    idx=pg.evaluate("Game.heroData.inventory.items.findIndex(e=>e.it.base==='greatsword')")
    pg.locator('#invGrid .invItem').nth(idx).dblclick();pg.wait_for_timeout(200)
    print('weapon',pg.evaluate("[Game.heroData.equipment.weapon.name,!!Game.heroData.equipment.shield,Game.derived.atkMin,Game.derived.atkMax]"))
    # drag iron shield onto shield slot
    idx=pg.evaluate("Game.heroData.inventory.items.findIndex(e=>e.it.base==='iron_shield')")
    el=pg.locator('#invGrid .invItem').nth(idx);bb=el.bounding_box();sl=pg.locator('.eqSlot[data-slot=shield]').bounding_box()
    pg.mouse.move(bb['x']+10,bb['y']+10);pg.mouse.down();pg.mouse.move(bb['x']+40,bb['y']+40,steps=4);pg.mouse.move(sl['x']+20,sl['y']+20,steps=6);pg.mouse.up();pg.wait_for_timeout(200)
    print('after shield',pg.evaluate("[Game.heroData.equipment.weapon&&Game.heroData.equipment.weapon.name,Game.heroData.equipment.shield&&Game.heroData.equipment.shield.name]"))
    # select & tooltip
    pg.locator('#invGrid .invItem').nth(0).click();pg.wait_for_timeout(200)
    pg.screenshot(path=SHOTS+'l3_inv2.png')
    pg.keyboard.press('KeyI');pg.wait_for_timeout(200)
    # potion
    hp0=pg.evaluate('Game.heroData.hp');pg.keyboard.press('KeyQ');pg.wait_for_timeout(100);print('potion',hp0,pg.evaluate('Game.heroData.hp'),pg.evaluate("Inv.count(Game.heroData,'hp_potion')"))
    # level up & alloc
    pg.evaluate('gainXp(900)');pg.wait_for_timeout(300);print('lvl',pg.evaluate('[Game.heroData.level,Game.heroData.statPoints,JSON.stringify(Game.heroData.stats)]'))
    pg.keyboard.press('KeyC');pg.wait_for_timeout(200)
    pg.locator('#csStats .plusBtn').nth(1).click();pg.locator('#csStats .plusBtn').nth(1).click();pg.wait_for_timeout(100)
    pg.screenshot(path=SHOTS+'l4_char.png')
    pg.click('#btnAllocOk');pg.wait_for_timeout(100)
    print('alloc',pg.evaluate('[Game.heroData.statPoints,Game.heroData.stats.vit]'))
    pg.keyboard.press('KeyC')
    pg.screenshot(path=SHOTS+'l5_hud.png')
    # death gold
    pg.evaluate('Game.heroData.gold=100;Game.heroData.hp=1;Game.hero.x=50;Game.hero.y=46');pg.wait_for_timeout(4000)
    print('state',pg.evaluate('Game.state'),pg.evaluate("document.getElementById('deathText').textContent"))
    print('ERRORS',errs)
    b.close()
