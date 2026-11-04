import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
import sys,time
from playwright.sync_api import sync_playwright
S=SHOTS
url=GAME
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_page(viewport={'width':1280,'height':760})
    errs=[]
    pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None)
    pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.goto(url); pg.wait_for_timeout(1200)
    pg.screenshot(path=S+'1_menu.png')
    pg.click('#btnNew'); pg.wait_for_timeout(500); pg.screenshot(path=S+'2_intro.png')
    pg.click('#btnNext'); pg.wait_for_timeout(300); pg.screenshot(path=S+'2b_intro.png')
    pg.click('#btnNext'); pg.click('#btnNext'); pg.wait_for_timeout(500)
    pg.screenshot(path=S+'3_create.png')
    pg.click('#raceSeg button:nth-child(2)'); pg.click('#classCards .cls:nth-child(2)'); pg.wait_for_timeout(300)
    pg.screenshot(path=S+'3b_create.png')
    pg.click('#raceSeg button:nth-child(1)'); pg.click('#classCards .cls:nth-child(1)')
    pg.click('#btnStart');pg.wait_for_timeout(300);pg.evaluate("Game.loadLocation('outskirts');applyWorldFlags()"); pg.wait_for_timeout(1200)
    pg.screenshot(path=S+'4_game.png')
    pos0=pg.evaluate('[Game.hero.x,Game.hero.y]')
    pg.keyboard.down('w'); pg.wait_for_timeout(1200); pg.keyboard.up('w')
    pg.keyboard.down('d'); pg.wait_for_timeout(900); pg.keyboard.up('d')
    pos1=pg.evaluate('[Game.hero.x,Game.hero.y]')
    print('moved',pos0,pos1)
    pg.wait_for_timeout(400); pg.screenshot(path=S+'5_moved.png')
    # teleport near elder & talk
    pg.evaluate('Game.hero.x=28.6;Game.hero.y=17.8')
    pg.wait_for_timeout(500); pg.keyboard.press('e'); pg.wait_for_timeout(400)
    print('state',pg.evaluate('Game.state'))
    pg.screenshot(path=S+'6_dialog.png')
    for i in range(5): pg.keyboard.press('e'); pg.wait_for_timeout(100)
    print('state after',pg.evaluate('Game.state'))
    pg.keyboard.press('c'); pg.wait_for_timeout(300); pg.screenshot(path=S+'7_char.png')
    pg.keyboard.press('c'); pg.keyboard.press('Escape'); pg.wait_for_timeout(200); pg.screenshot(path=S+'8_pause.png')
    pg.keyboard.press('Escape')
    # camp
    pg.evaluate('Game.hero.x=45;Game.hero.y=41'); pg.wait_for_timeout(800); pg.screenshot(path=S+'9_camp.png')
    # walls: try walking into house
    pg.evaluate('Game.hero.x=15.5;Game.hero.y=17.6')
    pg.keyboard.down('w'); pg.wait_for_timeout(1500); pg.keyboard.up('w')
    print('house test',pg.evaluate('[Game.hero.x,Game.hero.y]'))
    print('fps-ish')
    t=pg.evaluate('(async()=>{let n=0;const s=performance.now();await new Promise(r=>{function f(){n++;if(performance.now()-s<1000)requestAnimationFrame(f);else r();}requestAnimationFrame(f)});return n})()')
    print('frames/s',t)
    # mobile
    m=b.new_context(viewport={'width':844,'height':390},has_touch=True,is_mobile=True,device_scale_factor=2).new_page()
    m.on('pageerror',lambda e: errs.append('M:'+str(e)))
    m.goto(url); m.wait_for_timeout(800); m.screenshot(path=S+'m1_menu.png')
    m.tap('#btnNew'); m.tap('#btnSkip'); m.wait_for_timeout(400); m.screenshot(path=S+'m2_create.png')
    m.tap('#btnStart');m.wait_for_timeout(300);m.evaluate("Game.loadLocation('outskirts');applyWorldFlags()"); m.wait_for_timeout(1000)
    m.evaluate("""(()=>{const g=document.getElementById('game');const mk=(type,x,y)=>{const t=new Touch({identifier:1,target:g,clientX:x,clientY:y});g.dispatchEvent(new TouchEvent(type,{touches:type==='touchend'?[]:[t],changedTouches:[t],bubbles:true,cancelable:true}));};mk('touchstart',150,280);mk('touchmove',150,230);window._mk=mk;})()""")
    m.wait_for_timeout(800); m.screenshot(path=S+'m3_game.png')
    m.evaluate("window._mk('touchend',150,230)")
    print('mobile pos',m.evaluate('[Game.hero.x,Game.hero.y]'))
    m2=b.new_context(viewport={'width':390,'height':844},has_touch=True,is_mobile=True,device_scale_factor=2).new_page()
    m2.goto(url); m2.wait_for_timeout(600); m2.tap('#btnNew'); m2.tap('#btnSkip'); m2.wait_for_timeout(300); m2.screenshot(path=S+'p1_create.png',full_page=False)
    m2.tap('#btnStart');m2.wait_for_timeout(300);m2.evaluate("Game.loadLocation('outskirts');applyWorldFlags()"); m2.wait_for_timeout(800); m2.screenshot(path=S+'p2_game.png')
    print('ERRORS',errs)
    b.close()
