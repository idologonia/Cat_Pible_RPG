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
    pg.evaluate(f"(()=>{{const n=Game.npcs.find(n=>n.id==='{npc}');Game.hero.x=n.x+0.6;Game.hero.y=n.y+0.6;}})()");pg.wait_for_timeout(150)
    pg.evaluate(f"Game.interact(Game.npcs.find(n=>n.id==='{npc}'))");pg.wait_for_timeout(150)
def opts(pg): return pg.evaluate("[...document.querySelectorAll('#dlgBtns button')].map(b=>b.textContent)")
def pick(pg,i): pg.locator('#dlgBtns button').nth(i).click();pg.wait_for_timeout(120)
def killgroup(pg,g): pg.evaluate(f"for(const c of Game.combatants)if(c.group==='{g}'&&!c.dead){{c.hp=1;hitTarget(c,{{mult:50}});}}");pg.wait_for_timeout(200)
def qs(pg): return pg.evaluate("JSON.stringify(Object.fromEntries(Object.entries(Game.flags.q||{}).map(([k,v])=>[k,v.state+':'+v.step+':'+v.cnt])))")
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':760})
    pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:500]))
    pg.goto(url);pg.wait_for_timeout(400);pg.click('#btnNew');pg.click('#btnSkip');pg.click('#btnStart');pg.wait_for_timeout(300);pg.evaluate("Game.loadLocation('outskirts');applyWorldFlags()");pg.wait_for_timeout(600)
    pg.evaluate('Game.heroData.hp=9999;Game.derived.maxHp=9999')
    print('marks',pg.evaluate("Game.npcs.map(n=>n.id+':'+Quests.npcMark(n))"))
    tp(pg,28.6,17.6);pg.screenshot(path=SHOTS+'q0_marks.png')
    # main quest
    talk(pg,'elder');print('elder opts',opts(pg));pg.screenshot(path=SHOTS+'q1_elder.png')
    pick(pg,0);print(opts(pg));pick(pg,0);print(opts(pg));pick(pg,0);pg.wait_for_timeout(100);pick(pg,0)
    print('after accept',qs(pg),pg.evaluate('Game.state'))
    pg.screenshot(path=SHOTS+'q2_tracker.png')
    talk(pg,'guard');print('guard',opts(pg));pick(pg,0);pick(pg,0);pick(pg,0);print(qs(pg),pg.evaluate('Game.state'))
    # training
    talk(pg,'trainer');print('trainer',opts(pg));pick(pg,0);pick(pg,0);print(qs(pg))
    pg.evaluate("for(const c of Game.combatants)if(c instanceof Dummy&&!c.armored){c.hp=1;hitTarget(c,{mult:50});}");pg.wait_for_timeout(100)
    print('dummies',qs(pg))
    for i in range(3): pg.evaluate("Game.hero.iframe=1;Quests.emit('evade')")
    print('evade',qs(pg))
    talk(pg,'trainer');print(opts(pg));pick(pg,0);pick(pg,0);print('training done',qs(pg),pg.evaluate("Inv.count(Game.heroData,'hp_potion')"))
    # patrol -> deserter
    killgroup(pg,'patrol');pg.wait_for_timeout(3000);print('after patrol',qs(pg),pg.evaluate("Game.npcs.map(n=>n.id)"))
    tp(pg,18.2,38.8);pg.screenshot(path=SHOTS+'q3_deserter.png')
    talk(pg,'shkryab');print('shkryab',opts(pg));pick(pg,0);print(opts(pg));pg.screenshot(path=SHOTS+'q4_choice.png')
    pick(pg,0);pick(pg,0);print('freed',qs(pg),pg.evaluate("Game.npcs.map(n=>n.id)"))
    # stash
    tp(pg,7.6,34.9);pg.wait_for_timeout(400);print('it',pg.evaluate('Game.interactTarget&&Game.interactTarget.kind'));pg.keyboard.press('KeyE');pg.wait_for_timeout(200);print('stash',qs(pg),pg.evaluate('Game.flags.stashOpened'))
    # sausage
    talk(pg,'merchant');print('merchant',opts(pg));pick(pg,0);pick(pg,0);print(qs(pg))
    killgroup(pg,'ambush');pg.wait_for_timeout(300);print('ambush',qs(pg),pg.evaluate("Inv.count(Game.heroData,'pampushka_sausage')"))
    # camp/chief
    killgroup(pg,'camp');pg.wait_for_timeout(300);print('camp',qs(pg),pg.evaluate("[Game.flags.gryzDead,Game.flags.campCleared,Inv.count(Game.heroData,'royal_order')]"))
    talk(pg,'merchant');print('merchant2',opts(pg),pg.evaluate("document.getElementById('dlgText').textContent"))
    pick(pg,0);pick(pg,0);print('sausage done',qs(pg),pg.evaluate('priceMod()'))
    talk(pg,'merchant');pick(pg,0);pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'q5_shop.png');pg.keyboard.press('Escape')
    # journal
    pg.keyboard.press('KeyJ');pg.wait_for_timeout(200);pg.screenshot(path=SHOTS+'q6_journal.png');pg.keyboard.press('KeyJ')
    # hand-in main
    talk(pg,'elder');print('elder2',opts(pg));pick(pg,0);pick(pg,0);print(opts(pg));pg.screenshot(path=SHOTS+'q7_reward.png')
    pick(pg,2);pg.wait_for_timeout(200);print('main',qs(pg),pg.evaluate('[Game.heroData.statPoints,Inv.count(Game.heroData,"royal_order")]'))
    # save & reload persistence
    pg.evaluate("Game.manualSave()");pg.reload();pg.wait_for_timeout(400);pg.click('#btnContinue');pg.wait_for_timeout(300);pg.evaluate("if(Game.locationId!=='outskirts'){Game.loadLocation('outskirts');applyWorldFlags()}");pg.wait_for_timeout(500)
    print('after reload',qs(pg),pg.evaluate("[Game.flags.gryzDead,Game.combatants.find(c=>c.type==='chief').dead,Game.world.stash.spr===spriteChest(true)]"))
    talk(pg,'elder');print(pg.evaluate("document.getElementById('dlgText').textContent"));pick(pg,0)
    print('ERRORS',errs)
    # fail path new game: eat sausage
    pg2=b.new_page(viewport={'width':1280,'height':760});pg2.on('pageerror',lambda e: errs.append('2:'+str(e)))
    pg2.goto(url);pg2.wait_for_timeout(400);pg2.click('#btnNew');pg2.click('#btnSkip');pg2.click('#btnStart');pg2.wait_for_timeout(300);pg2.evaluate("Game.loadLocation('outskirts');applyWorldFlags()");pg2.wait_for_timeout(500)
    pg2.evaluate('Game.heroData.hp=9999;Game.derived.maxHp=9999')
    talk(pg2,'merchant');pick(pg2,0);pick(pg2,0)
    killgroup(pg2,'ambush')
    pg2.evaluate("useConsumable(Game.heroData.inventory.items.find(e=>e.it.base==='pampushka_sausage').it)");pg2.wait_for_timeout(200)
    print('fail',qs(pg2),pg2.evaluate('priceMod()'))
    talk(pg2,'merchant');print(pg2.evaluate("document.getElementById('dlgText').textContent"))
    # fight deserter
    pg2.keyboard.press('Escape');killgroup(pg2,'patrol');pg2.wait_for_timeout(3000)
    talk(pg2,'shkryab');pick(pg2,0);pick(pg2,2);pg2.wait_for_timeout(300)
    print('fight',pg2.evaluate("Game.combatants.filter(c=>c.unique).map(c=>c.name+c.state)"))
    pg2.evaluate("const c=Game.combatants.find(c=>c.unique);c.hp=1;hitTarget(c,{mult:50})");pg2.wait_for_timeout(200)
    print('deserter',qs(pg2))
    print('ERRORS',errs)
    b.close()
