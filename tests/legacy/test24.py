import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(accept_downloads=True);pg=ctx.new_page()
    pg.set_viewport_size({'width':1280,'height':760})
    pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:400]))
    pg.goto(GAME);pg.wait_for_timeout(400);pg.click('#btnNew');pg.click('#btnSkip');pg.click('#btnStart');pg.wait_for_timeout(800)
    pg.evaluate("Game.changeLocation('outskirts',{x:47.5,y:41})");pg.evaluate('setInterval(()=>{Game.hero.iframe=99;Game.hero.hp=Game.hero.maxHp},100)');pg.wait_for_timeout(1500)
    print('clock',pg.evaluate("[clockT(),clockStr(),phaseName(),nightLevel().toFixed(2),$('clockTag').textContent]"))
    vals=pg.evaluate("[0,60,150,600,1000,1100,1150,1200,1230,1300,1700,1799].map(t=>{Game.flags.clock=t;return t+':'+clockStr()+':'+nightLevel().toFixed(2)+':'+duskLevel().toFixed(2)})")
    print(vals)
    for t,name in [(500,'day'),(1120,'dusk'),(1500,'night'),(60,'dawn')]:
        pg.evaluate(f"Game.flags.clock={t};Game.weather={{type:'clear',k:0,until:1e9}}");pg.wait_for_timeout(1100);pg.screenshot(path=SHOTS+f'h_{name}.png')
    pg.evaluate("Game.flags.clock=500;Game.weather={type:'rain',k:1,until:1e9}");pg.wait_for_timeout(1100);pg.screenshot(path=SHOTS+'h_rain.png')
    pg.evaluate("Game.weather={type:'fog',k:1,until:1e9}");pg.wait_for_timeout(1100);pg.screenshot(path=SHOTS+'h_fog.png')
    pg.evaluate("Game.flags.clock=1500;Game.weather={type:'rain',k:1,until:1e9}");pg.wait_for_timeout(1100);pg.screenshot(path=SHOTS+'h_nightrain.png')
    print('night enemy',pg.evaluate("(()=>{const e=Game.combatants.find(c=>c.isEnemy&&!c.dead);e.update(0.01);const a=e.lvlMult;Game.flags.clock=500;e.update(0.01);return [a.toFixed(2),e.lvlMult.toFixed(2)]})()"))
    # експорт / імпорт
    pg.evaluate("Game.heroData.gold=4321;Game.manualSave()")
    pg.keyboard.press('Escape');pg.wait_for_timeout(300);print('pausevis',pg.evaluate("!$('pause').classList.contains('hidden')"));pg.screenshot(path=SHOTS+'h_pause.png');pg.click('#btnSaveIO2',timeout=4000);pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'h_saveio.png')
    with pg.expect_download() as dl: pg.click('#btnExportFile')
    path=dl.value.path();print('download',dl.value.suggested_filename)
    code=pg.evaluate("$('saveIOCode').value");print('code len',len(code))
    # нова сторінка з чистим сховищем
    ctx2=b.new_context();pg2=ctx2.new_page();pg2.on('pageerror',lambda e: errs.append('p2 '+str(e)))
    pg2.goto(GAME);pg2.wait_for_timeout(500)
    pg2.click('#btnSaveIO1');pg2.wait_for_timeout(300)
    pg2.set_input_files('#saveIOFile',path);pg2.wait_for_timeout(1500)
    print('imported file',pg2.evaluate("[Game.state,Game.heroData&&Game.heroData.gold,Game.locationId,Object.keys(localStorage)]"))
    ctx3=b.new_context();pg3=ctx3.new_page();pg3.goto(GAME);pg3.wait_for_timeout(500)
    pg3.click('#btnSaveIO1');pg3.wait_for_timeout(300);pg3.fill('#saveIOCode',code);pg3.click('#btnPasteCode');pg3.wait_for_timeout(1500)
    print('imported code',pg3.evaluate("[Game.state,Game.heroData&&Game.heroData.gold]"))
    print('ERRORS',errs[:5]);b.close()
