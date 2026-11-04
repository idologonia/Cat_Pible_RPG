import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':760})
    pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:400]))
    pg.goto(GAME);pg.wait_for_timeout(400);pg.click('#btnNew');pg.click('#btnSkip')
    pg.click('#raceCards .race:nth-child(2)') if pg.locator('#raceCards .race').count()>1 else None
    pg.click('#btnStart');pg.wait_for_timeout(600)
    print('race',pg.evaluate("Game.heroData.race"))
    pg.evaluate("while(Game.heroData.level<7)gainXp(xpToNext(Game.heroData.level))")
    for loc in ['outskirts','forest','cemetery','outpost','village','cheese','swamp']:
        pg.evaluate(f"Game.changeLocation('{loc}',null)");pg.wait_for_timeout(1200)
        print(loc,pg.evaluate("(()=>{const l=Game.combatants.filter(c=>c.isEnemy).map(c=>c.level);return Math.min(...l)+'-'+Math.max(...l)})()"))
    print('xp bandit 7/15/20',pg.evaluate("[7,15,20].map(L=>{const e=makeCombatant({type:'enemy',etype:'bandit',x:1,y:1,level:L});return enemyXp(e)})"),pg.evaluate("[7,15,20].map(l=>xpToNext(l))"))
    # без воскресіння
    pg.evaluate("Game.changeLocation('crypt',null)");pg.wait_for_timeout(1300)
    n0=pg.evaluate("Game.combatants.filter(c=>c.isEnemy).length")
    pg.evaluate("for(const c of Game.combatants)if(c.isEnemy&&!c.boss){c.hp=1;hitTarget(c,{mult:900});}");pg.evaluate("for(const c of Game.combatants)if(c.isEnemy&&c.dead)c.awayT=999,c.deadT=99")
    pg.wait_for_timeout(1500);print('crypt alive after kill',n0,pg.evaluate("Game.combatants.filter(c=>c.isEnemy&&!c.dead).length"))
    pg.evaluate("for(let y=0;y<64;y++)for(let x=0;x<64;x++)revealTile(Game.world,x,y)");pg.wait_for_timeout(200);pg.locator('#minimap').screenshot(path=SHOTS+'e1_maze.png')
    # підйом рівня не більше +5 від героя
    pg.evaluate("Game.flags.grpFloor={'outskirts:camp':40};Game.changeLocation('outskirts',null)");pg.wait_for_timeout(1200)
    print('camp cap',pg.evaluate("[Game.heroData.level,Game.combatants.filter(c=>c.group==='camp').map(c=>c.level).join(',')]"))
    pg.evaluate("Game.heroData.race='pibble';Quests.st.partisans={state:'done',step:6,cnt:0};checkAchievements()");pg.wait_for_timeout(800)
    print('secret ach',pg.evaluate("!!(Game.flags.ach||{}).pibble_home"))
    print('ERRORS',errs[:5]);b.close()
