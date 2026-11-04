import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
url=GAME
errs=[]
def tp(pg,x,y): pg.evaluate(f'Game.hero.x={x};Game.hero.y={y};const [a,b]=Render.proj({x},{y});Game.cam.x=a;Game.cam.y=b-12');pg.wait_for_timeout(150)
def hp(pg): return pg.evaluate('Game.combatants.filter(c=>c instanceof Dummy).map(c=>Math.round(c.hp)+(c.dead?"x":"")+(c.st.freeze>0?"F":"")+(c.st.stun>0?"S":"")+(c.st.slow>0?"L":"")+(c.st.burn>0?"B":"")+(c.st.poison>0?"P"+c.st.poisonStacks:""))')
def learn(pg,ids):
    pg.evaluate("(ids)=>{for(const id of ids){const n=nodeOf(Game.heroData.cls,id);const max=maxRank(n);Game.heroData.skills[id]=Math.max(Game.heroData.skills[id]||0,1);}Game.refreshHero();}",ids)
with sync_playwright() as p:
    b=p.chromium.launch()
    for cls,news in [(1,['shield_bash','ground_slam','fortify']),(2,['ice_lance','meteor','mana_shield']),(3,['trap','poison_arrow','eagle_eye'])]:
        pg=b.new_page(viewport={'width':1280,'height':760});pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:500]))
        pg.goto(url);pg.wait_for_timeout(400);pg.click('#btnNew');pg.click('#btnSkip');pg.click(f'#classCards .cls:nth-child({cls})');pg.click('#btnStart');pg.wait_for_timeout(300);pg.evaluate("Game.loadLocation('outskirts');applyWorldFlags()");pg.wait_for_timeout(400)
        pg.evaluate('gainXp(3000)');pg.wait_for_timeout(200)
        print(cls,'lvl',pg.evaluate('[Game.heroData.level,Game.heroData.skillPoints,JSON.stringify(Game.heroData.skills),JSON.stringify(Game.heroData.hotbar)]'))
        # open skills, learn via UI
        pg.keyboard.press('KeyK');pg.wait_for_timeout(300)
        pg.screenshot(path=SHOTS+f'k{cls}_tree.png')
        tree=pg.evaluate('SKILL_TREE[Game.heroData.cls].map(n=>n.id)')
        # learn: click first node + learn twice
        pg.locator(f'#skGrid [data-id="{tree[0]}"]').click();pg.locator('#skDetail .skActs button').nth(0).click();pg.locator('#skDetail .skActs button').nth(0).click()
        pg.locator(f'#skGrid [data-id="{tree[2]}"]').click();pg.locator('#skDetail .skActs button').nth(0).click()
        pg.wait_for_timeout(100);pg.screenshot(path=SHOTS+f'k{cls}_tree2.png')
        pg.click('#btnSkOk');pg.wait_for_timeout(100)
        print('after learn',pg.evaluate('[Game.heroData.skillPoints,JSON.stringify(Game.heroData.skills)]'))
        pg.keyboard.press('KeyK')
        learn(pg,news)
        pg.evaluate("(ids)=>{Game.heroData.hotbar=[ids[0],ids[1],ids[2],Game.heroData.hotbar[0]];UI.buildHotbar();Game.heroData.res=999;Game.derived.maxRes=999;}",news)
        tp(pg,42.6,29.6)
        pt=pg.evaluate('Render.worldToScreenCss(42.1,28.9,20)');pg.mouse.move(pt[0],pt[1])
        if cls==1:
            pg.evaluate("Game.heroData.equipment.shield||0");pg.keyboard.press('Digit1');pg.wait_for_timeout(150);print('bash',hp(pg))
            pg.keyboard.press('Digit2');pg.wait_for_timeout(600);print('slam',hp(pg))
            pg.keyboard.press('Digit3');pg.wait_for_timeout(100);pg.evaluate('heroTakeDamage(40,Game.hero.x+1,Game.hero.y)');print('fortify hp',pg.evaluate('[Math.round(Game.heroData.hp),Game.derived.maxHp]'))
        if cls==2:
            pg.keyboard.press('Digit4');pg.wait_for_timeout(100);print('nova',hp(pg))
            pg.keyboard.press('Digit1');pg.wait_for_timeout(500);print('icelance',hp(pg))
            pg.keyboard.press('Digit2');pg.wait_for_timeout(400);pg.screenshot(path=SHOTS+'k_meteor.png');pg.wait_for_timeout(900);print('meteor',hp(pg))
            pg.keyboard.press('Digit3');pg.wait_for_timeout(100);r0=pg.evaluate('Game.heroData.res');pg.evaluate('heroTakeDamage(30,Game.hero.x+1,Game.hero.y)');print('mana shield',pg.evaluate('[Math.round(Game.heroData.hp),Game.derived.maxHp]'),r0,pg.evaluate('Math.round(Game.heroData.res)'))
        if cls==3:
            pg.keyboard.press('Digit2');pg.wait_for_timeout(500);pg.wait_for_timeout(2600);pg.keyboard.press('Digit2');pg.wait_for_timeout(500);print('poison',hp(pg))
            pg.keyboard.press('Digit3');pg.wait_for_timeout(100);print('eagle',pg.evaluate('Game.hero.buffs.eagle'))
            # trap: place trap near patrol
            tp(pg,50,34.5);pg.keyboard.press('Digit1');pg.wait_for_timeout(100);print('traps',pg.evaluate('Game.traps.length'))
            pg.wait_for_timeout(2500);print('trap left',pg.evaluate('Game.traps.length'),pg.evaluate("Game.combatants.filter(c=>c.group==='patrol').map(c=>Math.round(c.hp)+(c.st.stun>0?'S':''))"))
        pg.screenshot(path=SHOTS+f'k{cls}_fight.png')
        # save reload keeps skills
        pg.evaluate('Game.manualSave()');pg.reload();pg.wait_for_timeout(300);pg.click('#btnContinue');pg.wait_for_timeout(300);pg.evaluate("if(Game.locationId!=='outskirts'){Game.loadLocation('outskirts');applyWorldFlags()}");pg.wait_for_timeout(300)
        print('reload',pg.evaluate('[Game.heroData.skillPoints,JSON.stringify(Game.heroData.hotbar)]'))
        pg.close()
    print('ERRORS',errs)
    b.close()
