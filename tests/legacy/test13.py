import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
url=GAME
errs=[]
def tp(pg,x,y): pg.evaluate(f'Game.hero.x={x};Game.hero.y={y};const [a,b]=Render.proj({x},{y});Game.cam.x=a;Game.cam.y=b-12');pg.wait_for_timeout(250)
def go(pg,loc,pos=None):
    pg.evaluate(f"Game.changeLocation('{loc}',{pos or 'null'})");pg.wait_for_timeout(1000)
def talk(pg,npc):
    pg.evaluate(f"(()=>{{const n=Game.npcs.find(n=>n.id==='{npc}');Game.hero.x=n.x+0.6;Game.hero.y=n.y+0.6;}})()");pg.wait_for_timeout(300)
    pg.evaluate(f"Game.interact(Game.npcs.find(n=>n.id==='{npc}'))");pg.wait_for_timeout(150)
def opts(pg): return pg.evaluate("[...document.querySelectorAll('#dlgBtns button')].map(b=>b.textContent)")
def pick(pg,i): pg.locator('#dlgBtns button').nth(i).click();pg.wait_for_timeout(150)
def qs(pg): return pg.evaluate("JSON.stringify(Object.fromEntries(Object.entries(Game.flags.q||{}).filter(([k])=>['outpost','partisans','monument'].includes(k)).map(([k,v])=>[k,v.state+':'+v.step+':'+v.cnt])))")
def killall(pg,cond='true'): pg.evaluate(f"for(const c of [...Game.combatants])if(c.isEnemy&&!c.dead&&({cond})){{c.hp=1;hitTarget(c,{{mult:500}});}}");pg.wait_for_timeout(300)
def interact_obj(pg,kind,extra=''):
    pg.evaluate(f"(()=>{{Game.groundItems.length=0;const o=Game.world.objects.find(o=>o.kind==='{kind}'{extra});Game.hero.x=o.x+0.7;Game.hero.y=o.y+0.9;}})()");pg.wait_for_timeout(350)
    print('  target',pg.evaluate("Game.interactTarget&&(Game.interactTarget.kind||Game.interactTarget.id)"));pg.keyboard.press('KeyE');pg.wait_for_timeout(200)
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':760})
    pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:600]))
    pg.goto(url);pg.wait_for_timeout(400);pg.click('#btnNew');pg.click('#btnSkip');pg.click('#btnStart');pg.wait_for_timeout(600)
    pg.evaluate('gainXp(30000)');pg.wait_for_timeout(200);print('lvl',pg.evaluate('Game.heroData.level'))
    pg.evaluate('Game.heroData.hp=99999;Game.derived.maxHp=99999')
    # --- ящики в Околицях
    go(pg,'outskirts',"{x:22,y:30}")
    print('breakables outskirts',pg.evaluate("Game.combatants.filter(c=>c.isBreakable).length"),'keep objs',pg.evaluate("Game.world.objects.filter(o=>o.kind==='crate'||o.kind==='barrel').length"))
    pg.evaluate("Game.groundItems.length=0;Game.coins.length=0;for(const c of Game.combatants)if(c.isBreakable)hitTarget(c,{mult:1})")
    pg.wait_for_timeout(300);print('loot from boxes: coins',pg.evaluate("Game.coins.length"),'items',pg.evaluate("Game.groundItems.map(g=>g.it.base).join(',')"))
    # --- головний квест і барикада
    print('west locked?');tp(pg,4.5,22.5);pg.keyboard.down('KeyA');pg.wait_for_timeout(700);pg.keyboard.up('KeyA');print('  x',pg.evaluate('Math.round(Game.hero.x*10)/10'),pg.evaluate('Game.locationId'))
    pg.evaluate("Quests.start('main');Quests.complete('main');applyWorldFlags()");pg.wait_for_timeout(300)
    talk(pg,'elder');print(opts(pg));
    i=[k for k,o in enumerate(opts(pg)) if 'далі' in o.lower()][0];pick(pg,i);pick(pg,0);pick(pg,0);print('outpost q',qs(pg))
    tp(pg,4.5,22.5);pg.screenshot(path=SHOTS+'x0_road.png');tp(pg,0.6,22.5);pg.wait_for_timeout(1200)
    print('loc',pg.evaluate('[Game.locationId,Math.round(Game.hero.x),Math.round(Game.hero.y)]'))
    tp(pg,44,28.6);pg.wait_for_timeout(600);print('reach',qs(pg));pg.screenshot(path=SHOTS+'x1_outpost.png')
    print('outpost enemies',pg.evaluate("Game.combatants.filter(e=>e.isEnemy).map(e=>e.name+e.level).join(', ')"))
    tp(pg,30,27);pg.wait_for_timeout(500);pg.screenshot(path=SHOTS+'x2_fort.png')
    # бос: перевірка AI (кілька секунд бою)
    pg.evaluate("const b=Game.combatants.find(e=>e.type==='captain');b.aggro(false);Game.hero.x=b.x+4;Game.hero.y=b.y+0.5;")
    pg.wait_for_timeout(4000);print('captain state',pg.evaluate("(()=>{const b=Game.combatants.find(e=>e.type==='captain');return [b.state,Math.round(b.hp),b.maxHp,!!b.dash,b.chargeT&&b.chargeT.toFixed(1)]})()"))
    pg.screenshot(path=SHOTS+'x3_captain.png')
    pg.evaluate("const b=Game.combatants.find(e=>e.type==='captain');b.hp=b.maxHp*0.5;hitTarget(b,{mult:1})");pg.wait_for_timeout(500)
    print('summoned',pg.evaluate("Game.combatants.filter(e=>e.temp).map(e=>e.name).join(',')"))
    killall(pg);print('after kill',qs(pg),pg.evaluate("Inv.count(Game.heroData,'captain_report')"),pg.evaluate("Game.groundItems.map(g=>g.it.name).filter(n=>n.includes('Сірохвост'))"))
    interact_obj(pg,'chest',"&&o===Game.world.capChest");print('cap chest',pg.evaluate('Game.flags.outpostChest'))
    print('npcs',pg.evaluate("Game.npcs.map(n=>n.id)"))
    go(pg,'outskirts',"{x:28,y:18}");talk(pg,'elder');print(opts(pg))
    i=[k for k,o in enumerate(opts(pg)) if 'донесення' in o][0];pick(pg,i);pick(pg,0);pick(pg,0);print('after elder',qs(pg))
    # --- Піблівка
    go(pg,'outpost',"{x:3,y:28.5}");tp(pg,0.6,28.5);pg.wait_for_timeout(1300)
    print('loc',pg.evaluate('[Game.locationId,Math.round(Game.hero.x),Math.round(Game.hero.y)]'))
    pg.screenshot(path=SHOTS+'x4_village_entry.png')
    tp(pg,30,41);pg.wait_for_timeout(600);print('reach village',qs(pg));pg.screenshot(path=SHOTS+'x5_village.png')
    print('village enemies',pg.evaluate("Game.combatants.filter(e=>e.isEnemy).length"),'boxes',pg.evaluate("Game.combatants.filter(e=>e.isBreakable).length"))
    talk(pg,'tuzya');print(opts(pg));pick(pg,0);pick(pg,0);pick(pg,0);pick(pg,0);print('tuzya',qs(pg))
    pg.screenshot(path=SHOTS+'x6_camp.png');pg.evaluate('UI.closeDialog()')
    killall(pg);print('village kills',qs(pg))
    interact_obj(pg,'monument');pg.wait_for_timeout(200);pg.evaluate('UI.closeDialog()')
    tp(pg,30.5,18.2);pg.wait_for_timeout(400);pg.screenshot(path=SHOTS+'x7_minegate.png')
    pg.keyboard.press('KeyE');pg.wait_for_timeout(1300)
    print('mine',pg.evaluate('[Game.locationId,Game.combatants.filter(e=>e.isEnemy).length,(Game.world.cages||[]).length,Game.npcs.filter(n=>n.cage).length,Game.combatants.filter(e=>e.isBreakable).length]'))
    pg.wait_for_timeout(500);pg.screenshot(path=SHOTS+'x8_mine_fog.png')
    print('fog revealed',pg.evaluate("Game.world.fog.reduce((a,b)=>a+b,0)"))
    print('target',pg.evaluate("JSON.stringify(Quests.target('partisans'))"))
    # клітка, поки вороги поруч
    pg.evaluate("(()=>{const o=Game.world.cages[0];Game.hero.x=o.x+0.8;Game.hero.y=o.y+0.9})()");pg.wait_for_timeout(1500)
    print('fog after walk',pg.evaluate("Game.world.fog.reduce((a,b)=>a+b,0)"))
    pg.screenshot(path=SHOTS+'x9_cage.png')
    pg.evaluate("freeMole(Game.world.cages[0])");print('mole w/ enemies',pg.evaluate("Game.world.cages[0].opened"))
    killall(pg,"c.type!=='overseer'")
    for i in range(6):
        pg.evaluate(f"(()=>{{const o=Game.world.cages[{i}];if(!o)return;Game.hero.x=o.x+0.7;Game.hero.y=o.y+0.9}})()");pg.wait_for_timeout(250)
        if i==0:
            pg.evaluate("Game.interact(Game.npcs.find(n=>n.cage===Game.world.cages[0]))");pg.wait_for_timeout(150);print(' mole talk',opts(pg));pick(pg,0)
        else: pg.evaluate(f"Game.world.cages[{i}]&&freeMole(Game.world.cages[{i}])")
    print('moles',qs(pg),pg.evaluate('Game.flags.molesFreed'))
    pg.evaluate("const b=Game.combatants.find(e=>e.boss);Game.hero.x=b.x+3;Game.hero.y=b.y+2;b.aggro(false)");pg.wait_for_timeout(3000);pg.screenshot(path=SHOTS+'x10_boss.png')
    print('overseer',pg.evaluate("(()=>{const b=Game.combatants.find(e=>e.boss);return [b.name,b.state,Math.round(b.hp)]})()"),'hazards',pg.evaluate('Game.hazards.length'))
    killall(pg);pg.wait_for_timeout(500);print('boss dead',qs(pg),pg.evaluate("Game.groundItems.map(g=>g.it.name).filter(n=>n.includes('наглядача'))"),pg.evaluate("Game.world.cleared"))
    pg.evaluate("Game.groundItems.length=0");interact_obj(pg,'chest',"&&o===Game.world.bossChest");print('boss chest',pg.evaluate("Game.world.bossChest.opened"))
    pg.evaluate("Game.travelTo('village')");pg.wait_for_timeout(1000)
    talk(pg,'tuzya');print(opts(pg));pick(pg,0);pg.wait_for_timeout(100);print(opts(pg));pick(pg,0);print('partisans done',qs(pg))
    print('npcs now',pg.evaluate("Game.npcs.map(n=>n.id)"))
    talk(pg,'tuzya');print(opts(pg));
    i=[k for k,o in enumerate(opts(pg)) if 'допомогти' in o][0];pick(pg,i);pick(pg,0);pick(pg,0);print('monument',qs(pg))
    pg.evaluate("giveItem(makeItem('iron_scrap'),8);");pg.evaluate("const it=makeItem('crystal_shard');it.qty=3;Game.groundItems.push({it,x:Game.hero.x,y:Game.hero.y,z:0,t:1,isGround:true});pickUpGround(Game.groundItems[Game.groundItems.length-1])");pg.wait_for_timeout(200)
    print('mon steps',qs(pg))
    talk(pg,'tuzya');print(opts(pg));
    i=[k for k,o in enumerate(opts(pg)) if 'пам' in o.lower()][0];pick(pg,i);print(opts(pg));pick(pg,0);pg.wait_for_timeout(300)
    print('restored',qs(pg),pg.evaluate('[Game.flags.monumentRestored,JSON.stringify(Game.world.respawn),Game.npcs.map(n=>n.id).join(",")]'))
    tp(pg,29,40.5);pg.wait_for_timeout(800);pg.screenshot(path=SHOTS+'x11_restored.png')
    talk(pg,'kopach');print(opts(pg));pick(pg,0);pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'x12_moleshop.png');pg.evaluate('UI.closeShop?UI.closeShop():Game.closeShop()');pg.wait_for_timeout(200)
    # смерть у селі → відродження біля пам'ятника
    pg.evaluate("Game.heroData.hp=1;Game.derived.maxHp=100;heroTakeDamage(9999)");pg.wait_for_timeout(1500);print('death text',pg.evaluate("$('deathText').textContent.slice(0,60)"))
    pg.evaluate("Game.respawn()");pg.wait_for_timeout(300);print('respawn at',pg.evaluate('[Game.locationId,Math.round(Game.hero.x),Math.round(Game.hero.y)]'))
    pg.evaluate('Game.heroData.hp=99999;Game.derived.maxHp=99999')
    # --- мисливці в Густому лісі
    go(pg,'forest',"{x:12,y:22}");pg.wait_for_timeout(500);pg.screenshot(path=SHOTS+'x13_hunters.png')
    interact_obj(pg,'chest',"&&o===Game.world.huntChest")
    killall(pg,"c.group==='fH'");print('hunters',pg.evaluate('Game.world.huntChest.ready'))
    interact_obj(pg,'chest',"&&o===Game.world.huntChest");print('hunt chest loot',pg.evaluate("Game.groundItems.map(g=>g.it.name).join(',')"),pg.evaluate('Game.world.huntChest.ready'))
    # мапа світу
    pg.evaluate("Game.openWorldMap()");pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'x14_map.png');pg.evaluate('Game.closePanel()')
    # збереження/завантаження
    pg.evaluate("Game.closePanel&&Game.closePanel();Game.manualSave()");pg.wait_for_timeout(300)
    print('saved ok',pg.evaluate("!!SaveSys.list()[Game.saveSlot]"))
    print('ERRORS',errs[:5])
    b.close()
