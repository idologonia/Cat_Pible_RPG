import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page();pg.set_viewport_size({'width':1280,'height':760})
    pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:500]))
    pg.goto(GAME);pg.wait_for_timeout(400);pg.click('#btnNew');pg.click('#btnSkip');pg.click('#btnStart');pg.wait_for_timeout(800)
    pg.evaluate("Game.heroData.level=16;Game.heroData.gold=500;Quests.st.cheese={state:'done',step:0,cnt:0};Game.flags.clock=500;setInterval(()=>{Game.hero.iframe=99},100)")
    pg.evaluate("Game.changeLocation('cheese',{x:43.5,y:36})");pg.wait_for_timeout(1300)
    pg.evaluate("$('dialog')&&UI.closeDialog&&UI.closeDialog()")
    pg.screenshot(path=SHOTS+'i_out.png')
    print('interact out',pg.evaluate("(()=>{const t=Game.findInteract();return t&&(t.interact?t.interact.name:t.name)})()"))
    pg.evaluate("Game.interact()");pg.wait_for_timeout(1300)
    print('loc',pg.evaluate("[Game.locationId,Game.world.name,Game.npcs.map(n=>n.id).join(',')]"))
    pg.screenshot(path=SHOTS+'i_in_day.png')
    pg.evaluate("Game.flags.clock=1500");pg.wait_for_timeout(1200);pg.screenshot(path=SHOTS+'i_in_night.png')
    # гауда
    pg.evaluate("Game.hero.x=8.6;Game.hero.y=9.4");pg.wait_for_timeout(300)
    print('near counter',pg.evaluate("(()=>{const t=Game.findInteract();return t&&(t.id||t.interact&&t.interact.name)})()"))
    pg.evaluate("Game.interact()");pg.wait_for_timeout(400);pg.screenshot(path=SHOTS+'i_gouda.png')
    print('dialog opts',pg.evaluate("[...document.querySelectorAll('#dialog button')].map(b=>b.textContent).join(' | ')"))
    pg.evaluate("UI.closeDialog()")
    # сходи
    pg.evaluate("Game.hero.x=18.2;Game.hero.y=8");pg.wait_for_timeout(300)
    print('stairs',pg.evaluate("(()=>{const t=Game.findInteract();return t&&t.interact&&Game.interactLabel(t)})()"))
    pg.evaluate("Game.interact()");pg.wait_for_timeout(1500);print('after sleep',pg.evaluate("[Game.heroData.gold,clockStr(),Game.hero.buffs.rested]"))
    # дошка
    pg.evaluate("Game.hero.x=5.6;Game.hero.y=15.6");pg.wait_for_timeout(300)
    print('board',pg.evaluate("(()=>{const t=Game.findInteract();return t&&t.interact&&t.interact.name})()"))
    pg.evaluate("Game.interact()");pg.wait_for_timeout(400);print('board open',pg.evaluate("Game.panel"))
    pg.evaluate("Game.takeContract?0:0");
    # взяти завдання, перевірити ціль
    pg.evaluate("Game.closePanel()")
    pg.evaluate("(()=>{const B=boardState('tavern');refreshBoard&&0;Game.boardId='tavern';const o=genOffer('tavern');takeContract(o);Game.flags.tracked=o.id;})()")
    pg.evaluate("Game.openWorldMap()");pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'i_map.png');pg.evaluate("Game.closePanel()")
    # вийти
    pg.evaluate("Game.hero.x=12;Game.hero.y=17.6");pg.wait_for_timeout(1500)
    print('exit',pg.evaluate("[Game.locationId,Game.hero.x.toFixed(1),Game.hero.y.toFixed(1)]"))
    # з міста ціль до дошки корчми
    pg.evaluate("Game.changeLocation('forest',null)");pg.wait_for_timeout(1300)
    print('target hop', pg.evaluate("nextHop('forest','inn')+' '+nextHop('cheese','inn')+' '+nextHop('inn','city')+' '+JSON.stringify(routeLocs('city','inn'))"))
    pg.evaluate("Game.changeLocation('cheese',null)");pg.wait_for_timeout(1300)
    print('target in cheese for tboard',pg.evaluate("(()=>{const D=Game.flags.repDefs;const id=Object.keys(D)[0];const q=Quests.q(id);q.step=1;return JSON.stringify(Quests.target(id))})()"))
    # збереження і завантаження всередині
    pg.evaluate("Game.changeLocation('inn',INN.entry)");pg.wait_for_timeout(1300);pg.evaluate("Game.manualSave()")
    pg.reload();pg.wait_for_timeout(500);pg.evaluate("Game.loadSlot?0:0")
    print('ERRORS',errs[:5]);b.close()
