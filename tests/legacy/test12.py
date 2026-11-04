import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
url=GAME
errs=[]
def tp(pg,x,y): pg.evaluate(f'Game.hero.x={x};Game.hero.y={y};const [a,b]=Render.proj({x},{y});Game.cam.x=a;Game.cam.y=b-12');pg.wait_for_timeout(200)
def go(pg,loc,pos=None):
    pg.evaluate(f"Game.changeLocation('{loc}',{pos or 'null'})");pg.wait_for_timeout(900)
def talk(pg,npc):
    pg.evaluate(f"(()=>{{const n=Game.npcs.find(n=>n.id==='{npc}');Game.hero.x=n.x+0.6;Game.hero.y=n.y+0.6;}})()");pg.wait_for_timeout(300)
    pg.evaluate(f"Game.interact(Game.npcs.find(n=>n.id==='{npc}'))");pg.wait_for_timeout(150)
def opts(pg): return pg.evaluate("[...document.querySelectorAll('#dlgBtns button')].map(b=>b.textContent)")
def pick(pg,i): pg.locator('#dlgBtns button').nth(i).click();pg.wait_for_timeout(150)
def qs(pg): return pg.evaluate("JSON.stringify(Object.fromEntries(Object.entries(Game.flags.q||{}).map(([k,v])=>[k,v.state+':'+v.step+':'+v.cnt])))")
def killall(pg,cond='true'): pg.evaluate(f"for(const c of [...Game.combatants])if(c.isEnemy&&!c.dead&&({cond})){{c.hp=1;hitTarget(c,{{mult:500}});}}");pg.wait_for_timeout(300)
def interact_obj(pg,kind,extra=''):
    pg.evaluate(f"(()=>{{const o=Game.world.objects.find(o=>o.kind==='{kind}'{extra});Game.hero.x=o.x+0.7;Game.hero.y=o.y+0.9;}})()");pg.wait_for_timeout(350)
    print('  target',pg.evaluate("Game.interactTarget&&(Game.interactTarget.kind||Game.interactTarget.id)"));pg.keyboard.press('KeyE');pg.wait_for_timeout(200)
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':760})
    pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:600]))
    pg.goto(url);pg.wait_for_timeout(400);pg.click('#btnNew');pg.click('#btnSkip');pg.click('#btnStart');pg.wait_for_timeout(600)
    print('hp lv1',pg.evaluate('Game.derived.maxHp'))
    pg.evaluate('gainXp(4000)');pg.wait_for_timeout(200);print('lvl',pg.evaluate('Game.heroData.level'))
    pg.evaluate('Game.heroData.hp=99999;Game.derived.maxHp=99999')
    go(pg,'outskirts',"{x:56,y:22}")
    print('outskirts npcs',pg.evaluate("Game.npcs.map(n=>n.id)"))
    talk(pg,'smetanko');print(opts(pg));pick(pg,0);pick(pg,0);pick(pg,0);print('caravan',qs(pg))
    # walk east exit
    tp(pg,61.5,22.5);pg.keyboard.down('KeyD');pg.keyboard.down('KeyS');pg.wait_for_timeout(700);pg.keyboard.up('KeyD');pg.keyboard.up('KeyS');pg.wait_for_timeout(900)
    print('loc',pg.evaluate('[Game.locationId,Math.round(Game.hero.x),Math.round(Game.hero.y)]'))
    pg.screenshot(path=SHOTS+'w1_forest.png')
    print('forest enemies',pg.evaluate("Game.combatants.filter(e=>e.isEnemy).map(e=>e.name.split(' ')[0].slice(0,4)+e.level).join(',')"))
    tp(pg,20,32.6);pg.wait_for_timeout(400);print('reach',qs(pg))
    interact_obj(pg,'wagon');pg.keyboard.press('Escape');print('clue1',qs(pg))
    interact_obj(pg,'prints');pg.keyboard.press('Escape');interact_obj(pg,'scarf');pg.keyboard.press('Escape');print('clues',qs(pg))
    tp(pg,47,16);pg.wait_for_timeout(500);pg.screenshot(path=SHOTS+'w2_hideout.png')
    killall(pg,"c.group==='hideout'");print('otaman',qs(pg),pg.evaluate("Game.groundItems.map(g=>g.it.name).filter(n=>n.includes('Чорнохвост'))"))
    interact_obj(pg,'chest',"&&o===Game.world.goods");pg.wait_for_timeout(200);print(opts(pg));pick(pg,1)
    interact_obj(pg,'cage');pg.wait_for_timeout(200);print(opts(pg));pick(pg,0);pg.wait_for_timeout(200);pg.keyboard.press('Escape');print('cage',qs(pg))
    interact_obj(pg,'chest',"&&o===Game.world.secretChest");print('secret',pg.evaluate('Game.flags.secrets'))
    print('target',pg.evaluate("JSON.stringify(Quests.target('caravan'))"))
    pg.evaluate("Game.openWorldMap()");pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'w3_map.png')
    pg.locator('.wmNode',has_text='Околиці').click();pg.wait_for_timeout(100);pg.locator('#wmInfo button').click();pg.wait_for_timeout(900)
    print('travel',pg.evaluate('Game.locationId'))
    talk(pg,'smetanko');print(opts(pg));pick(pg,0);pg.wait_for_timeout(100);print(opts(pg));pick(pg,0);pick(pg,0);print('caravan done',qs(pg),pg.evaluate('Game.flags.smetankoInCity'))
    # cemetery locked
    tp(pg,22.5,61.6);pg.keyboard.down('KeyS');pg.wait_for_timeout(800);pg.keyboard.up('KeyS');pg.wait_for_timeout(300);print('locked',pg.evaluate('Game.locationId'))
    pg.evaluate("Game.flags.cemeteryKey=true");tp(pg,22.5,61.6);pg.keyboard.down('KeyS');pg.wait_for_timeout(800);pg.keyboard.up('KeyS');pg.wait_for_timeout(900)
    print('cemetery',pg.evaluate('[Game.locationId,Math.round(Game.hero.x),Math.round(Game.hero.y)]'))
    pg.screenshot(path=SHOTS+'w4_cem.png')
    talk(pg,'murana');print(opts(pg));pick(pg,0);pick(pg,0);pick(pg,0);print('anc',qs(pg))
    killall(pg,"c.group==='c1'||c.group==='c2'||c.group==='c3'");print('anc kills',qs(pg))
    pg.evaluate("Game.groundItems.length=0;Game.coins.length=0")
    for i in range(3): interact_obj(pg,'relic',f"&&o.relic==={i}")
    print('relics',qs(pg))
    interact_obj(pg,'slab');print('secret',pg.evaluate('Game.flags.secrets'))
    tp(pg,41,44.6);pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'w5_crypt_door.png');pg.keyboard.press('KeyE');pg.wait_for_timeout(1200)
    print('crypt',pg.evaluate('[Game.locationId,Game.combatants.filter(e=>e.isEnemy).length,Game.world.objects.length]'))
    pg.screenshot(path=SHOTS+'w6_crypt.png')
    # go to boss
    pg.evaluate("const b=Game.combatants.find(e=>e.boss);Game.hero.x=b.x+3;Game.hero.y=b.y+2;");pg.wait_for_timeout(1500);pg.screenshot(path=SHOTS+'w7_boss.png')
    print('boss',pg.evaluate("(()=>{const b=Game.combatants.find(e=>e.boss);return [b.name,b.level,b.maxHp,b.state]})()"))
    pg.evaluate("const b=Game.combatants.find(e=>e.boss);b.hp=b.maxHp*0.55;hitTarget(b,{mult:1})");pg.wait_for_timeout(2500);pg.screenshot(path=SHOTS+'w8_boss2.png')
    print('summoned',pg.evaluate("Game.combatants.filter(e=>e.temp).length"),'hazards',pg.evaluate("Game.hazards.length"))
    killall(pg);pg.wait_for_timeout(500)
    print('cleared',pg.evaluate('Game.world.cleared'),qs(pg),pg.evaluate("Game.groundItems.map(g=>g.it.name).filter(n=>n.includes('Гнилозуб'))"))
    interact_obj(pg,'chest',"&&o===Game.world.bossChest");print('chest',pg.evaluate("Game.groundItems.length"))
    pg.screenshot(path=SHOTS+'w9_cleared.png')
    # exit stairs
    pg.evaluate("const ex=Game.world.exits[0];Game.hero.x=(ex.x0+ex.x1)/2;Game.hero.y=(ex.y0+ex.y1)/2+1.4");pg.keyboard.down('KeyW');pg.wait_for_timeout(600);pg.keyboard.up('KeyW');pg.wait_for_timeout(900)
    print('exit',pg.evaluate('Game.locationId'))
    talk(pg,'murana');print(opts(pg));pick(pg,0);pick(pg,0);print('anc done',qs(pg),pg.evaluate("Game.heroData.inventory.items.map(e=>e.it.name).filter(n=>n.includes('Медальйон'))"))
    # events
    go(pg,'outskirts',"{x:40,y:22}");
    for ev in ['ambush','traveler','merchant','caravan']:
        pg.evaluate("Game.event=null;for(const id of ['traveler','peddler','carter'])removeNpc(id,false)")
        r=pg.evaluate(f"EVENTS.{ev}()");pg.wait_for_timeout(400);print('event',ev,r,pg.evaluate("Game.npcs.filter(n=>n.eventNpc).map(n=>n.id)"),pg.evaluate("Game.combatants.filter(e=>e.temp&&!e.dead).length"))
        if ev=='caravan':
            pg.screenshot(path=SHOTS+'w10_event.png');killall(pg,"c.temp");talk(pg,'carter');print(opts(pg));pick(pg,0);pick(pg,0)
        if ev=='traveler':
            talk(pg,'traveler');print(opts(pg));pick(pg,0);pick(pg,0);pg.keyboard.press('Escape')
        killall(pg,"c.temp")
    # save/reload
    pg.evaluate('Game.manualSave()');pg.reload();pg.wait_for_timeout(400);pg.click('#btnContinue');pg.wait_for_timeout(600)
    print('reload',pg.evaluate("[Game.locationId,JSON.stringify(Game.flags.visited),Game.flags.smetankoInCity,Game.flags.secrets]"))
    go(pg,'city');print('city npcs',pg.evaluate("Game.npcs.map(n=>n.id).filter(i=>i==='smetanko'||i==='pushok')"))
    print('ERRORS',errs)
    b.close()
