import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
S=SHOTS
url=GAME
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':760})
    pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:400]))
    pg.goto(url);pg.wait_for_timeout(500)
    # sprite sheet
    pg.evaluate("""(()=>{const cv=document.createElement('canvas');cv.id='sheet';cv.width=300;cv.height=200;cv.style.cssText='position:fixed;left:0;top:0;width:900px;height:600px;image-rendering:pixelated;z-index:999;background:#7cc35a';document.body.appendChild(cv);
     const c=cv.getContext('2d');c.imageSmoothingEnabled=false;
     Object.keys(ENEMY_DEFS).forEach((k,i)=>{const L=ENEMY_DEFS[k].look;[['down',4],['side',0],['up',4],['side',6],['side',7],['down',6]].forEach(([d,f],j)=>{const s=getRatSprite(L,d,f);c.drawImage(s.canvas,j*48,i*38-6);});});})()""")
    pg.wait_for_timeout(100);pg.screenshot(path=S+'rats.png');pg.evaluate("document.getElementById('sheet').remove()")
    pg.click('#btnNew');pg.click('#btnSkip');pg.click('#btnStart');pg.wait_for_timeout(300);pg.evaluate("Game.loadLocation('outskirts');applyWorldFlags()");pg.wait_for_timeout(500)
    print('enemies',pg.evaluate("Game.combatants.filter(c=>c.isEnemy).map(e=>e.type+'@'+e.x.toFixed(1)+','+e.y.toFixed(1))"))
    # walk toward camp: teleport near entrance
    pg.evaluate('Game.hero.x=48;Game.hero.y=39.5;const [a,b]=Render.proj(48,39.5);Game.cam.x=a;Game.cam.y=b-12;Game.heroData.hp=9999;Game.derived.maxHp=9999')
    pg.wait_for_timeout(1500)
    print('states',pg.evaluate("Game.combatants.filter(c=>c.isEnemy).map(e=>e.type[0]+':'+e.state+(e.wind?'W':''))"))
    pg.screenshot(path=S+'e1_aggro.png')
    pg.wait_for_timeout(2500)
    print('hero hp',pg.evaluate('Game.heroData.hp'))
    pg.screenshot(path=S+'e2_fight.png')
    # fight: hold attack at nearest enemy for several seconds
    for i in range(16):
        tgt=pg.evaluate("(()=>{const h=Game.hero;let b=null,bd=99;for(const c of Game.combatants)if(c.isEnemy&&!c.dead){const d=Math.hypot(c.x-h.x,c.y-h.y);if(d<bd){bd=d;b=c;}}return b?Render.worldToScreenCss(b.x,b.y,20):null})()")
        if tgt: pg.mouse.move(tgt[0],tgt[1])
        pg.mouse.down();pg.wait_for_timeout(400);pg.keyboard.press('Digit1');pg.wait_for_timeout(300);pg.mouse.up()
        pg.evaluate('Game.heroData.res=Game.derived.maxRes')
    print('after fight',pg.evaluate("Game.combatants.filter(c=>c.isEnemy).map(e=>e.type[0]+':'+(e.dead?'dead':Math.round(e.hp)+e.state))"),'hero',pg.evaluate('Math.round(Game.heroData.hp)'))
    pg.screenshot(path=S+'e3.png')
    # leash: teleport hero to tree
    pg.evaluate('Game.hero.x=16.7;Game.hero.y=21;Game.heroData.hp=50;Game.derived.maxHp=128')
    pg.wait_for_timeout(3000)
    print('return',pg.evaluate("Game.combatants.filter(c=>c.isEnemy&&!c.dead).map(e=>e.type[0]+':'+e.state+':'+Math.round(e.hp))"))
    # ambush test with archer class? check archer telegraphs
    pg.evaluate('Game.hero.x=22;Game.hero.y=47;Game.heroData.hp=9999;Game.derived.maxHp=9999;const [a,b]=Render.proj(22,47);Game.cam.x=a;Game.cam.y=b-12')
    pg.wait_for_timeout(2200);pg.screenshot(path=S+'e4_ambush.png')
    print('ambush',pg.evaluate("Game.combatants.filter(c=>c.group==='ambush').map(e=>e.type[0]+':'+e.state+(e.wind?'W':'')+(e.dash?'D':''))"),pg.evaluate('Game.projectiles.length'))
    print('ERRORS',errs)
    b.close()
