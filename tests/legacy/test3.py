import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
S=SHOTS
url=GAME
errs=[]
def start(pg,cls,race=1):
    pg.goto(url); pg.wait_for_timeout(600)
    pg.click('#btnNew'); pg.click('#btnSkip')
    pg.click(f'#raceSeg button:nth-child({race})')
    pg.click(f'#classCards .cls:nth-child({cls})')
    pg.click('#btnStart');pg.wait_for_timeout(300);pg.evaluate("Game.loadLocation('outskirts');applyWorldFlags()"); pg.wait_for_timeout(500)
def toYard(pg):
    pg.evaluate('Game.hero.x=42.6;Game.hero.y=29.6;Game.heroData.res=999;const [a,b]=Render.proj(42.6,29.6);Game.cam.x=a;Game.cam.y=b-12')
    pg.wait_for_timeout(300)
def mouseAt(pg,wx,wy):
    p=pg.evaluate(f'Render.worldToScreenCss({wx},{wy},10)')
    pg.mouse.move(p[0],p[1]); return p
def hp(pg): return pg.evaluate('Game.combatants.map(c=>Math.round(c.hp)+(c.dead?"x":"")+(c.st.freeze>0?"F":"")+(c.st.stun>0?"S":"")+(c.st.slow>0?"L":"")+(c.st.burn>0?"B":""))')
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_page(viewport={'width':1280,'height':760})
    pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:300]))
    # KNIGHT
    start(pg,1)
    pg.screenshot(path=S+'k0_start.png')
    toYard(pg)
    d=pg.evaluate('Game.combatants[0]'); # dummy at 42.1,28.9
    mouseAt(pg,42.1,28.9)
    print('before',hp(pg))
    pg.mouse.down(); pg.wait_for_timeout(1200); pg.mouse.up()
    print('after basic',hp(pg))
    pg.keyboard.press('Digit1'); pg.wait_for_timeout(100)
    print('heavy',hp(pg))
    pg.screenshot(path=S+'k1_hit.png')
    mouseAt(pg,44.5,28.1); pg.keyboard.press('Digit2'); pg.wait_for_timeout(250)
    print('charge',hp(pg), pg.evaluate('[Game.hero.x,Game.hero.y]'))
    pg.keyboard.press('Digit1'); pg.wait_for_timeout(80); print('heavy on stunned',hp(pg))
    pg.keyboard.press('Digit3'); pg.wait_for_timeout(100)
    pg.keyboard.press('Digit4'); pg.wait_for_timeout(350); pg.screenshot(path=S+'k2_whirl.png'); pg.wait_for_timeout(600)
    print('whirl',hp(pg), 'buffs',pg.evaluate('JSON.stringify(Game.hero.buffs)'))
    # crossbow + block
    pg.evaluate('Game.hero.x=45.6;Game.hero.y=31.0'); pg.wait_for_timeout(200)
    print('interact target',pg.evaluate('Game.interactTarget&&Game.interactTarget.kind'))
    pg.keyboard.press('KeyE'); pg.wait_for_timeout(100)
    pg.evaluate('Game.hero.x=42.0;Game.hero.y=29.0;Game.heroData.hp=Game.derived.maxHp')
    xb=pg.evaluate('[Game.world.turrets[0].x,Game.world.turrets[0].y]')
    mouseAt(pg,xb[0],xb[1]); pg.mouse.down(button='right'); pg.wait_for_timeout(3000)
    pg.screenshot(path=S+'k3_block.png')
    pg.mouse.up(button='right')
    print('hp after block',pg.evaluate('[Game.heroData.hp,Game.heroData.res,Game.derived.maxHp]'))
    pg.wait_for_timeout(2500); print('hp unblocked',pg.evaluate('Game.heroData.hp'))
    # death
    pg.evaluate('Game.heroData.hp=3;Game.heroData.xp=50'); pg.wait_for_timeout(3000)
    print('state',pg.evaluate('Game.state')); pg.screenshot(path=S+'k4_dead.png')
    pg.click('#btnRespawn'); pg.wait_for_timeout(600)
    print('respawn',pg.evaluate('[Game.state,Game.hero.x,Game.hero.y,Game.heroData.xp,Game.heroData.hp]'))
    pg.screenshot(path=S+'k5_respawn.png')
    # tree interact
    pg.keyboard.press('KeyE'); pg.wait_for_timeout(200); print('tree dialog',pg.evaluate('Game.state'), pg.evaluate("document.getElementById('dlgName').textContent"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    # controls rebind
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150); pg.click('#btnControls2'); pg.wait_for_timeout(200)
    pg.click('#bindTable tr:nth-child(1) button'); pg.keyboard.press('KeyQ'); pg.wait_for_timeout(100)
    print('bind',pg.evaluate('Input.binds.skill1'), pg.evaluate("document.querySelector('#hotbar .hslot:nth-of-type(2) .key')?.textContent"))
    pg.screenshot(path=S+'k6_binds.png')
    pg.click('#btnResetBinds'); print('reset',pg.evaluate('Input.binds.skill1')); pg.click('#btnCloseControls')
    # MAGE
    start(pg,2,2); toYard(pg)
    mouseAt(pg,42.1,28.9)
    pg.keyboard.press('Digit2'); pg.wait_for_timeout(100); print('nova',hp(pg))
    pg.keyboard.press('Digit3'); pg.wait_for_timeout(100); print('lightning',hp(pg))
    pg.screenshot(path=S+'m1_lightning.png')
    pg.wait_for_timeout(1700); pg.keyboard.press('Digit1'); pg.wait_for_timeout(400); print('fireball',hp(pg)); pg.screenshot(path=S+'m2_fire.png')
    pg.evaluate('Game.heroData.hp=20'); pg.keyboard.press('Digit4'); pg.wait_for_timeout(100); print('heal',pg.evaluate('Game.heroData.hp'))
    pg.mouse.down(); pg.wait_for_timeout(1000); pg.mouse.up(); print('bolts',hp(pg))
    pg.keyboard.press('Space'); pg.wait_for_timeout(300)
    # ARCHER
    start(pg,3); toYard(pg); mouseAt(pg,44.5,28.1)
    pg.mouse.down(); pg.wait_for_timeout(800); pg.mouse.up(); print('arrows',hp(pg))
    pg.keyboard.press('Digit1'); pg.wait_for_timeout(700); print('power',hp(pg))
    pg.keyboard.press('Digit2'); pg.wait_for_timeout(400); print('multi',hp(pg))
    mouseAt(pg,43.5,29.5); pg.keyboard.press('Digit4'); pg.wait_for_timeout(700); pg.screenshot(path=S+'a1_rain.png'); pg.wait_for_timeout(1500); print('rain',hp(pg))
    pg.keyboard.press('Digit3'); pg.wait_for_timeout(400); print('disengage',hp(pg),pg.evaluate('[Game.hero.x,Game.hero.y]'))
    pg.screenshot(path=S+'a2.png')
    # MOBILE
    m=b.new_context(viewport={'width':844,'height':390},has_touch=True,is_mobile=True,device_scale_factor=2).new_page()
    m.on('pageerror',lambda e: errs.append('M:'+str(e)))
    m.goto(url); m.wait_for_timeout(500); m.tap('#btnNew'); m.tap('#btnSkip'); m.tap('#btnStart');m.wait_for_timeout(300);m.evaluate("Game.loadLocation('outskirts');applyWorldFlags()"); m.wait_for_timeout(600)
    m.evaluate('Game.hero.x=42.6;Game.hero.y=29.6'); m.wait_for_timeout(300)
    m.dispatch_event('#touchBtns .t-basic','pointerdown'); m.wait_for_timeout(900); m.dispatch_event('#touchBtns .t-basic','pointerup')
    m.dispatch_event('#touchBtns .t-skill0','pointerdown'); m.wait_for_timeout(200)
    print('mobile hits',hp(m)); m.screenshot(path=S+'mob1.png')
    print('ERRORS',errs)
    b.close()
