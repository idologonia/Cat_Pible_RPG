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
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':760})
    pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:400]))
    pg.goto(GAME);pg.wait_for_timeout(400);pg.click('#btnNew');pg.click('#btnSkip');pg.click('#btnStart');pg.wait_for_timeout(800)
    print('loc',pg.evaluate("Game.locationId"),pg.evaluate("Game.npcs.map(n=>n.id).includes('guide')"))
    talk(pg,'guide');print(opts(pg));pick(pg,0);print(pg.evaluate("$('dlgText').textContent"));pg.screenshot(path=SHOTS+'g1_guide.png')
    pick(pg,len(opts(pg))-1);pick(pg,1);print(pg.evaluate("$('dlgText').textContent")[:300]);pg.evaluate("UI.closeDialog()")
    # реген поза безпечною зоною
    pg.evaluate("Game.changeLocation('outskirts',{x:47,y:30})");pg.wait_for_timeout(1300)
    pg.evaluate("Game.heroData.hp=10");pg.wait_for_timeout(2000);print('regen outside',pg.evaluate("[Math.round(Game.heroData.hp),Game.inSafeZone(Game.hero)]"))
    pg.evaluate("Game.hero.x=22.5;Game.hero.y=24");pg.wait_for_timeout(300);print('safe here?',pg.evaluate("Game.inSafeZone(Game.hero)"))
    # корчма
    pg.evaluate("while(Game.heroData.level<16)gainXp(xpToNext(Game.heroData.level))")
    pg.evaluate("Game.changeLocation('inn',null)");pg.wait_for_timeout(1300);pg.evaluate("Game.hero.iframe=1e9")
    talk(pg,'gouda');print(opts(pg));pg.screenshot(path=SHOTS+'g2_tavern.png');pg.evaluate("UI.closeDialog()")
    pg.evaluate("Quests.st.cheese={state:'done',step:6,cnt:0}")
    talk(pg,'gouda');print(opts(pg));pg.evaluate("Game.heroData.gold=500;Game.heroData.hp=5")
    i=[k for k,o in enumerate(opts(pg)) if 'кімнату' in o][0]
    print('dbg',pg.evaluate("[Game.state,(()=>{const r=document.querySelectorAll('#dlgBtns button')[1].getBoundingClientRect();const el=document.elementFromPoint(r.x+20,r.y+8);return el&&(el.id||el.className)+'|'+(el.parentElement&&el.parentElement.id)})()]"))
    pick(pg,i);pg.wait_for_timeout(1500)
    print('rest',pg.evaluate("[Math.round(Game.heroData.hp),Game.derived.maxHp,Math.round(Game.hero.buffs.rested),Game.heroData.gold]"))
    talk(pg,'gouda');i=[k for k,o in enumerate(opts(pg)) if 'сир і вино' in o][0];pick(pg,i);pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'g3_shop.png');pg.evaluate("Game.closeShop()")
    pg.evaluate("Game.openBoard('tavern')");pg.wait_for_timeout(300);print('offers',pg.evaluate("Game.flags.tboard.offers.map(o=>o.title+': '+o.steps[0].text)"));pg.screenshot(path=SHOTS+'g4_tboard.png')
    # взяти всі три типи
    for k in ['parcel','escort','thieves']:
        pg.evaluate(f"(()=>{{let o=Game.flags.tboard.offers.find(o=>o.key==='{k}');if(!o){{o=genOffer('tavern');while(o.key!=='{k}')o=genOffer('tavern');Game.flags.tboard.offers.push(o);}}CONFIG.board.maxActive=5;takeContract(o);}})()")
    pg.evaluate("Game.closePanel()")
    print('active',pg.evaluate("Object.values(Game.flags.repDefs).map(d=>d.key+':'+JSON.stringify(Quests.q(d.id)))"),'allies',pg.evaluate("Game.allies.map(a=>a.name)"),'parcel',pg.evaluate("Inv.count(Game.heroData,'parcel')"))
    esc=pg.evaluate("Object.values(Game.flags.repDefs).find(d=>d.escort).escort.dest");thv=pg.evaluate("Object.values(Game.flags.repDefs).find(d=>d.thieves).thieves.loc");par=pg.evaluate("JSON.stringify(Object.values(Game.flags.repDefs).find(d=>d.parcel).parcel)")
    print('esc',esc,'thv',thv,'parcel',par)
    pg.evaluate(f"Game.changeLocation('{thv}',null)");pg.wait_for_timeout(1300)
    print('thieves',pg.evaluate("Game.combatants.filter(c=>c.group&&c.group.startsWith('thv_')).length"),'escort here',pg.evaluate("Game.allies.map(a=>a.name)"))
    pg.evaluate("for(const c of [...Game.combatants])if(c.group&&c.group.startsWith('thv_')&&!c.dead){c.hp=1;hitTarget(c,{mult:900});}");pg.wait_for_timeout(400)
    print('after thieves',pg.evaluate("Object.values(Game.flags.repDefs).map(d=>d.key+':'+Quests.q(d.id).step)"))
    pg.evaluate(f"Game.changeLocation('{esc}',null)");pg.wait_for_timeout(2500)
    print('after escort',pg.evaluate("Object.values(Game.flags.repDefs).map(d=>d.key+':'+Quests.q(d.id).step)"),pg.evaluate("Game.allies.map(a=>a.name)"))
    import json;P=json.loads(par)
    pg.evaluate(f"Game.changeLocation('{P['loc']}',null)");pg.wait_for_timeout(1300)
    talk(pg,P['npc']);pg.wait_for_timeout(300);pg.evaluate("UI.closeDialog()");pg.wait_for_timeout(200)
    print('after parcel',pg.evaluate("Object.values(Game.flags.repDefs||{}).map(d=>d.key+':'+(Quests.q(d.id)||{}).step)"),pg.evaluate("Inv.count(Game.heroData,'parcel')"))
    pg.evaluate("Game.changeLocation('cheese',null)");pg.wait_for_timeout(1300)
    pg.evaluate("Game.openBoard('tavern')");pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'g5_handin.png')
    print('ready buttons',pg.evaluate("[...document.querySelectorAll('#boardList .bActs button')].map(b=>b.textContent+':'+b.disabled)"))
    pg.evaluate("for(const b of [...document.querySelectorAll('#boardList .bActs button')])if(b.textContent==='Здати'&&!b.disabled)b.click()");pg.wait_for_timeout(300)
    pg.evaluate("for(const b of [...document.querySelectorAll('#boardList .bActs button')])if(b.textContent==='Здати'&&!b.disabled)b.click()");pg.wait_for_timeout(300)
    print('left',pg.evaluate("Object.keys(Game.flags.repDefs||{}).length"),'rep',pg.evaluate("JSON.stringify(Game.flags.rep)"))
    pg.evaluate("Game.closePanel();Game.manualSave()");pg.wait_for_timeout(300)
    print('ERRORS',errs[:5]);b.close()
