import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
errs=[]
def opts(pg): return pg.evaluate("[...document.querySelectorAll('#dlgBtns button')].map(b=>b.textContent)")
def pick(pg,i): pg.locator('#dlgBtns button').nth(i).click();pg.wait_for_timeout(150)
def talk(pg,npc):
    pg.evaluate(f"(()=>{{const n=Game.npcs.find(n=>n.id==='{npc}');Game.hero.x=n.x+0.6;Game.hero.y=n.y+0.6;}})()");pg.wait_for_timeout(300)
    pg.evaluate(f"Game.interact(Game.npcs.find(n=>n.id==='{npc}'))");pg.wait_for_timeout(150)
def qs(pg): return pg.evaluate("JSON.stringify(Object.fromEntries(Object.entries(Game.flags.q||{}).filter(([k])=>['partisans','monument'].includes(k)).map(([k,v])=>[k,v.state+':'+v.step+':'+v.cnt])))")
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':760})
    pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:400]))
    pg.goto(GAME);pg.wait_for_timeout(400);pg.click('#btnNew');pg.click('#btnSkip');pg.click('#btnStart');pg.wait_for_timeout(600)
    # очки раз на 5 рівнів
    r=[]
    for i in range(7):
        pg.evaluate("gainXp(xpToNext(Game.heroData.level))");r.append(pg.evaluate("[Game.heroData.level,Game.heroData.statPoints,Game.heroData.skillPoints]"))
    print('points',r)
    pg.evaluate("for(let i=0;i<5;i++)gainXp(xpToNext(Game.heroData.level))")
    print('lvl',pg.evaluate("[Game.heroData.level,Game.heroData.statPoints,Game.heroData.skillPoints]"))
    # лут: 300 вбивств бандитів
    print('loot sim',pg.evaluate("""(()=>{Game.loadLocation('outskirts');Game.groundItems.length=0;let it=0,pot=0,mat=0;
      for(let i=0;i<300;i++){const e=makeCombatant({type:'enemy',etype:'bandit',x:30,y:30,level:12});Game.groundItems.length=0;rollLoot(e);for(const g of Game.groundItems){if(g.it.type==='equip')it++;else if(g.it.type==='potion')pot++;else mat++;}}
      return {items:it,potions:pot,other:mat};})()"""))
    pg.evaluate("Quests.start('main');Quests.complete('main');Quests.start('outpost');Quests.complete('outpost');Quests.start('partisans');(Game.flags.killed||(Game.flags.killed={})).sirokhvist=true")
    pg.evaluate('Game.heroData.hp=99999;Game.derived.maxHp=99999')
    pg.evaluate("Game.changeLocation('village',{x:30,y:41})");pg.wait_for_timeout(1300)
    talk(pg,'tuzya');pick(pg,0);pick(pg,0);pick(pg,0);print(opts(pg));pick(pg,1);pg.wait_for_timeout(400)
    print('mode',pg.evaluate("Game.flags.partisansMode"),'allies',pg.evaluate("Game.allies.map(a=>a.id)"),'npcs',pg.evaluate("Game.npcs.map(n=>n.id)"))
    # бій: союзники мають бити ворогів
    pg.evaluate("(()=>{const e=Game.combatants.find(c=>c.isEnemy&&!c.dead&&c.group==='v1');Game.hero.x=e.x+2;Game.hero.y=e.y+1.5;for(const a of Game.allies){a.x=Game.hero.x+0.5;a.y=Game.hero.y+0.5;}e.aggro(true);})()")
    hp0=pg.evaluate("Game.combatants.filter(c=>c.group==='v1').map(c=>Math.round(c.hp))")
    pg.wait_for_timeout(5000);pg.screenshot(path=SHOTS+'z1_allies.png')
    print('v1 hp before/after',hp0,pg.evaluate("Game.combatants.filter(c=>c.group==='v1').map(c=>c.dead?'x':Math.round(c.hp))"))
    pg.evaluate("Game.changeLocation('mine',null)");pg.wait_for_timeout(1300);print('mine allies',pg.evaluate("Game.allies.length"))
    pg.evaluate("for(const c of [...Game.combatants])if(c.isEnemy&&!c.dead){c.hp=1;hitTarget(c,{mult:500});}");pg.wait_for_timeout(2500)
    print('after kailo allies',pg.evaluate("Game.allies.length"),qs(pg))
    pg.evaluate("Game.flags.molesFreed=5;Quests.st.partisans.step=5");
    pg.evaluate("Game.changeLocation('village',{x:30,y:41})");pg.wait_for_timeout(1300)
    talk(pg,'tuzya');print(opts(pg));pick(pg,0);pick(pg,1);print('done',qs(pg),pg.evaluate("Game.combatants.filter(c=>c.isEnemy&&!c.dead&&/^v[123]$/.test(c.group)).length"))
    # дошка
    pg.evaluate("Game.changeLocation('village',{x:25,y:36})");pg.wait_for_timeout(1300)
    print('board',pg.evaluate("!!Game.world.vboard"))
    pg.evaluate("Game.openBoard('village')");pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'z2_vboard.png')
    print('offers',pg.evaluate("Game.flags.vboard.offers.map(o=>o.title+'|'+o.boardId)"))
    pg.evaluate("Game.closePanel()")
    pg.evaluate("Game.openBoard('city')");print('city offers',pg.evaluate("Game.flags.board.offers.map(o=>o.title)"));pg.evaluate("Game.closePanel()")
    # взяти deliver-контракт у Піблівці і здати
    pg.evaluate("Game.boardId='village';const o=Game.flags.vboard.offers.find(o=>o.steps[0].type==='deliver')||null;if(o){takeContract(o);giveItem(makeItem(o.steps[0].item),20);}")
    pg.wait_for_timeout(200);print('target',pg.evaluate("JSON.stringify(Quests.target(Object.keys(Game.flags.repDefs).find(k=>Game.flags.repDefs[k].boardId==='village')))"))
    pg.evaluate("const id=Object.keys(Game.flags.repDefs).find(k=>Game.flags.repDefs[k].boardId==='village');if(id)finishContract(id)");pg.wait_for_timeout(900)
    print('restore',pg.evaluate("Game.flags.vilRestore"))
    pg.evaluate("addVilRestore(8,'тест')");pg.wait_for_timeout(500)
    print('restore',pg.evaluate("[Game.flags.vilRestore,Game.world.vilHouses.filter(h=>h.fixed).length,Game.npcs.map(n=>n.id).join(',')]"))
    pg.evaluate("Game.changeLocation('village',{x:36,y:34})");pg.wait_for_timeout(1300);pg.screenshot(path=SHOTS+'z3_rebuilt.png')
    # набіг
    pg.evaluate("Game.flags.lastRaidAt=0;Game.flags.forceRaid=true;CONFIG.village.raidDelay=0.5;Game.changeLocation('village',{x:29,y:41})");pg.wait_for_timeout(2500)
    print('raid',pg.evaluate("[!!Game.raid,Game.combatants.filter(c=>c.group==='raid'&&!c.dead).length,Game.allies.map(a=>a.id).join(',')]"))
    pg.wait_for_timeout(3000);pg.screenshot(path=SHOTS+'z4_raid.png')
    pg.evaluate("for(const c of [...Game.combatants])if(c.group==='raid'&&!c.dead){c.hp=1;hitTarget(c,{mult:500});}");pg.wait_for_timeout(3500)
    print('raid end',pg.evaluate("[!!Game.raid,Game.flags.vilRestore,Game.flags.raidsRepelled,Game.allies.length]"))
    pg.evaluate("Game.manualSave()");pg.wait_for_timeout(300)
    print('ERRORS',errs[:5]);b.close()
