import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
url=GAME
errs=[]
def fight(pg,secs,skill=True):
    for i in range(int(secs/0.6)):
        tgt=pg.evaluate("(()=>{const h=Game.hero;if(!h||h.dead)return null;let b=null,bd=99;for(const c of Game.combatants)if(c.isEnemy&&!c.dead&&c.state==='fight'){const d=Math.hypot(c.x-h.x,c.y-h.y);if(d<bd){bd=d;b=c;}}return b?[...Render.worldToScreenCss(b.x,b.y,20),bd]:null})()")
        if not tgt: break
        pg.mouse.move(tgt[0],tgt[1])
        if tgt[2]>1.4 and pg.evaluate("CLASSES[Game.heroData.cls].basic==='slash'"):
            pg.keyboard.down('KeyW' if False else 'KeyD'); pg.keyboard.up('KeyD')
        pg.mouse.down();pg.wait_for_timeout(450)
        if skill: pg.keyboard.press('Digit1')
        pg.wait_for_timeout(150);pg.mouse.up()
with sync_playwright() as p:
    b=p.chromium.launch()
    for cls in [1,2,3]:
        pg=b.new_page(viewport={'width':1280,'height':760})
        pg.on('pageerror',lambda e: errs.append(str(e)))
        pg.goto(url);pg.wait_for_timeout(400);pg.click('#btnNew');pg.click('#btnSkip');pg.click(f'#classCards .cls:nth-child({cls})');pg.click('#btnStart');pg.wait_for_timeout(300);pg.evaluate("Game.loadLocation('outskirts');applyWorldFlags()");pg.wait_for_timeout(400)
        pg.evaluate('Game.hero.x=50;Game.hero.y=32.5;const [a,b]=Render.proj(50,32.5);Game.cam.x=a;Game.cam.y=b-12')
        pg.keyboard.down('KeyS');pg.wait_for_timeout(700);pg.keyboard.up('KeyS')
        pg.wait_for_timeout(300)
        print(cls,'aggro',pg.evaluate("Game.combatants.filter(c=>c.isEnemy&&c.state==='fight').map(e=>e.type)"))
        fight(pg,12)
        print(cls,'result hp',pg.evaluate("[Game.state,Math.round(Game.heroData.hp)]"),pg.evaluate("Game.combatants.filter(c=>c.group==='patrol').map(e=>e.dead?'dead':Math.round(e.hp))"))
        pg.close()
    print('ERRORS',errs)
    b.close()
