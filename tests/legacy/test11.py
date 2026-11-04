import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
url=GAME
errs=[]
def tp(pg,x,y): pg.evaluate(f'Game.hero.x={x};Game.hero.y={y};const [a,b]=Render.proj({x},{y});Game.cam.x=a;Game.cam.y=b-12');pg.wait_for_timeout(150)
def talk(pg,npc):
    pg.evaluate(f"(()=>{{const n=Game.npcs.find(n=>n.id==='{npc}');Game.hero.x=n.x+0.6;Game.hero.y=n.y+0.6;}})()");pg.wait_for_timeout(450)
    pg.evaluate(f"Game.interact(Game.npcs.find(n=>n.id==='{npc}'))");pg.wait_for_timeout(150)
def opts(pg): return pg.evaluate("[...document.querySelectorAll('#dlgBtns button')].map(b=>b.textContent)")
def pickt(pg,t): pg.locator('#dlgBtns button',has_text=t).click();pg.wait_for_timeout(200)
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':760})
    pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:500]))
    pg.goto(url);pg.wait_for_timeout(400);pg.click('#btnNew');pg.click('#btnSkip');pg.click('#btnStart');pg.wait_for_timeout(1200)
    print('loc',pg.evaluate('[Game.locationId,Game.hero.x,Game.hero.y]'))
    pg.screenshot(path=SHOTS+'c1_city.png')
    tp(pg,26,34);pg.screenshot(path=SHOTS+'c2_city_s.png')
    tp(pg,26,14);pg.screenshot(path=SHOTS+'c3_city_n.png')
    # shops
    pg.evaluate('Game.heroData.gold=2000')
    for npc,label in [('weaponsmith','Торгувати'),('armorer','Торгувати'),('alchemist','Торгувати'),('magpie','Торгувати')]:
        talk(pg,npc);print(npc,opts(pg));pickt(pg,label);pg.wait_for_timeout(200)
        print(' stock',pg.evaluate("document.querySelectorAll('#shopStock .shopRow').length"),'rare',pg.evaluate("document.querySelectorAll('#shopRare .shopRow').length"))
        if npc=='magpie':
            pg.locator('#shopStock .shopRow',has_text='Рецепт').locator('button').click();pg.wait_for_timeout(100)
        pg.screenshot(path=SHOTS+f'c_shop_{npc}.png');pg.keyboard.press('Escape');pg.wait_for_timeout(150)
    # recipe learn & craft
    pg.evaluate("useConsumable(Game.heroData.inventory.items.find(e=>e.it.base==='recipe_rage').it)")
    pg.evaluate("for(const [k,n] of [['catnip',6],['glowcap',6],['arcane_dust',3],['leather_scrap',2],['crystal_shard',1]]){const m=makeItem(k);m.qty=n;Inv.add(Game.heroData,m);}")
    talk(pg,'alchemist');pickt(pg,'Варити');pg.wait_for_timeout(200);pg.screenshot(path=SHOTS+'c_craft.png')
    n0=pg.evaluate("Inv.count(Game.heroData,'hp_potion')");pg.locator('#craftList .shopRow').nth(0).locator('button').click();pg.locator('#craftList .shopRow').nth(3).locator('button').click()
    print('craft',n0,pg.evaluate("[Inv.count(Game.heroData,'hp_potion'),Inv.count(Game.heroData,'rage_potion'),Inv.count(Game.heroData,'catnip')]"))
    pg.keyboard.press('Escape');pg.wait_for_timeout(150)
    # smith
    pg.evaluate("Inv.add(Game.heroData,generateItem('broadsword',3,2));Inv.add(Game.heroData,generateItem('chainmail',2,1))")
    talk(pg,'smith');print('smith',opts(pg));pickt(pg,'Покращення');pg.wait_for_timeout(200)
    w0=pg.evaluate("[Game.heroData.equipment.weapon.name,Game.derived.atkMin,Game.derived.atkMax]")
    for i in range(4):
        btn=pg.locator('#smithDetail button',has_text='Покращити')
        if btn.count(): btn.click();pg.wait_for_timeout(100)
    print('upgrade',w0,pg.evaluate("[Game.heroData.equipment.weapon.name,Game.heroData.equipment.weapon.upg,Game.derived.atkMin,Game.derived.atkMax,Game.heroData.gold]"))
    pg.screenshot(path=SHOTS+'c_smith.png')
    pg.click('#smith .tabBtn[data-tab=skin]');pg.wait_for_timeout(150);pg.locator('#smithList .shopRow').nth(0).click();pg.wait_for_timeout(100)
    pg.screenshot(path=SHOTS+'c_skin.png')
    pg.locator('.skinBtn').nth(1).click();pg.wait_for_timeout(100);print('skin',pg.evaluate("[Game.heroData.equipment.weapon.skin,heroLook(Game.heroData).weapon]"))
    pg.click('#smith .tabBtn[data-tab=dismantle]');pg.wait_for_timeout(150)
    pg.screenshot(path=SHOTS+'c_dismantle.png')
    inv0=pg.evaluate("Game.heroData.inventory.items.length");pg.locator('#smithDetail button',has_text='Розібрати').click();pg.wait_for_timeout(100)
    print('dismantle',inv0,pg.evaluate("[Game.heroData.inventory.items.length,Inv.count(Game.heroData,'iron_scrap'),Inv.count(Game.heroData,'arcane_dust'),Inv.count(Game.heroData,'crystal_shard')]"))
    pg.keyboard.press('Escape');pg.wait_for_timeout(150)
    # stash
    talk(pg,'banker');pickt(pg,'сховище');pg.wait_for_timeout(200)
    pg.locator('#stashInv .invItem').nth(0).click();pg.wait_for_timeout(100)
    print('stash',pg.evaluate("[Game.heroData.stash.items.length,Game.heroData.inventory.items.length]"))
    pg.screenshot(path=SHOTS+'c_stash.png');pg.keyboard.press('Escape');pg.wait_for_timeout(150)
    # board
    tp(pg,30.2,21.4);pg.wait_for_timeout(300);print('it',pg.evaluate("Game.interactTarget&&Game.interactTarget.kind"));pg.keyboard.press('KeyE');pg.wait_for_timeout(300)
    pg.screenshot(path=SHOTS+'c_board.png')
    pg.locator('#boardList .bCard button',has_text='Взяти').nth(0).click();pg.wait_for_timeout(100)
    pg.locator('#boardList .bCard button',has_text='Взяти').nth(0).click();pg.wait_for_timeout(100)
    print('contracts',pg.evaluate("Object.values(Game.flags.repDefs).map(d=>d.key+':'+Quests.progressText(d.id))"))
    pg.keyboard.press('Escape');pg.wait_for_timeout(200)
    print('tracker',pg.evaluate("document.getElementById('tracker').innerText"))
    # travel to outskirts via gate
    tp(pg,26.5,48.5);pg.keyboard.down('KeyS');pg.wait_for_timeout(900);pg.keyboard.up('KeyS');pg.wait_for_timeout(900)
    print('travel',pg.evaluate('[Game.locationId,Game.state,Math.round(Game.hero.x),Math.round(Game.hero.y)]'))
    pg.screenshot(path=SHOTS+'c_outskirts.png')
    print('enemy levels',pg.evaluate("Game.combatants.filter(c=>c.isEnemy).map(e=>e.type[0]+e.level)"))
    # complete contracts: simulate kills
    pg.evaluate("for(const c of Game.combatants)if(c.isEnemy&&!c.dead&&c.group!=='camp'){c.hp=1;hitTarget(c,{mult:50});}");pg.wait_for_timeout(300)
    print('contracts after kills',pg.evaluate("Object.values(Game.flags.repDefs).map(d=>d.key+':'+Quests.progressText(d.id))"))
    # gather node
    pg.evaluate("const o=Game.world.objects.find(o=>o.kind==='node'&&o.res==='catnip');Game.hero.x=o.x+0.5;Game.hero.y=o.y+0.6;");pg.wait_for_timeout(300)
    print('node it',pg.evaluate("Game.interactTarget&&Game.interactTarget.kind"));c0=pg.evaluate("Inv.count(Game.heroData,'catnip')");pg.keyboard.press('KeyE');pg.wait_for_timeout(100);print('gather',c0,pg.evaluate("Inv.count(Game.heroData,'catnip')"))
    # die -> respawn in city
    pg.evaluate("Game.heroData.hp=1;heroTakeDamage(999,Game.hero.x+1,Game.hero.y)");pg.wait_for_timeout(1500);pg.click('#btnRespawn');pg.wait_for_timeout(400)
    print('respawn',pg.evaluate('[Game.locationId,Game.state]'))
    # board hand-in
    pg.evaluate("Game.openBoard()");pg.wait_for_timeout(200);pg.screenshot(path=SHOTS+'c_board2.png')
    btns=pg.locator('#boardList .bCard.act button',has_text='Здати')
    print('handin buttons',btns.count(),[btns.nth(i).is_enabled() for i in range(btns.count())])
    if btns.count() and btns.nth(0).is_enabled(): btns.nth(0).click();pg.wait_for_timeout(100)
    print('done',pg.evaluate("[Game.flags.contractsDone,JSON.stringify(Game.flags.board.done)]"))
    pg.keyboard.press('Escape')
    # save reload
    pg.evaluate('Game.manualSave()');pg.reload();pg.wait_for_timeout(300);pg.click('#btnContinue');pg.wait_for_timeout(500)
    print('reload',pg.evaluate("[Game.locationId,Game.heroData.stash.items.length,Game.heroData.equipment.weapon.upg,Object.keys(Game.flags.repDefs||{}).length,Object.keys(Game.flags.recipes||{})]"))
    print('ERRORS',errs)
    b.close()
