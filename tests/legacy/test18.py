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
    pg.goto(GAME);pg.wait_for_timeout(400);pg.click('#btnNew');pg.click('#btnSkip');pg.click('#btnStart');pg.wait_for_timeout(600)
    r=[]
    for i in range(14):
        pg.evaluate("gainXp(xpToNext(Game.heroData.level))");r.append(pg.evaluate("Game.heroData.level+':'+Game.heroData.statPoints+'/'+Game.heroData.skillPoints"))
    print('points',r)
    pg.evaluate("Game.heroData.hp=99999;Game.derived.maxHp=99999")
    pg.evaluate("Game.changeLocation('outskirts',{x:47,y:40})");pg.wait_for_timeout(1300)
    print('camp',pg.evaluate("Game.combatants.filter(c=>c.group==='camp').map(c=>c.type+c.level+(c.elite?'*':'')).join(',')"))
    print('guards',pg.evaluate("Game.allies.map(a=>a.name+':'+a.maxHp)"))
    # мінікарта: до побачення ворогів не видно
    print('seen before',pg.evaluate("Game.combatants.filter(c=>c.isEnemy&&c.seenT!=null).length"))
    pg.wait_for_timeout(500);print('seen after',pg.evaluate("Game.combatants.filter(c=>c.isEnemy&&c.seenT!=null).map(c=>c.type).join(',')"))
    # щитоносець блокує
    print('shield',pg.evaluate("""(()=>{const e=Game.combatants.find(c=>c.type==='shield');e.state='fight';e.wind=null;e.strikeT=0;let s=0;const hp=e.hp;for(let i=0;i<20;i++){e.hp=hp;hitTarget(e,{mult:1});s+=hp-e.hp;}
      const a=s/20;e.wind={t:0,dx:1,dy:0};s=0;for(let i=0;i<20;i++){e.hp=hp;hitTarget(e,{mult:1});s+=hp-e.hp;}e.wind=null;e.hp=hp;return [Math.round(a),Math.round(s/20)]})()"""))
    # знахар лікує
    print('healer',pg.evaluate("""(()=>{const hl=Game.combatants.find(c=>c.type==='healer'),o=Game.combatants.find(c=>c.group==='camp'&&c.type==='bandit');o.hp=o.maxHp*0.3;const before=Math.round(o.hp);hl.state='fight';hl.healT=0;
      ENEMY_AI.healer(hl,Game.hero,6,0.016);return [before,Math.round(o.hp),o.maxHp]})()"""))
    # повторна зачистка: +5 рівнів
    pg.evaluate("for(const c of [...Game.combatants])if(c.group==='camp'&&!c.dead){c.hp=1;hitTarget(c,{mult:900});}");pg.wait_for_timeout(2000)
    print('floor',pg.evaluate("JSON.stringify(Game.flags.grpFloor)"))
    pg.evaluate("Game.changeLocation('city',null)");pg.wait_for_timeout(1200);pg.evaluate("Game.changeLocation('outskirts',{x:47,y:40})");pg.wait_for_timeout(1200)
    print('camp after',pg.evaluate("Game.combatants.filter(c=>c.group==='camp').map(c=>c.level).join(',')"),'hero',pg.evaluate("Game.heroData.level"))
    # варта б'ється із засідкою в селі
    pg.evaluate("Game.hero.x=22;Game.hero.y=23;for(let i=0;i<3;i++){const e=makeCombatant({type:'enemy',etype:'bandit',x:23.5+i,y:21,group:'evtX',level:Game.heroData.level,temp:true});Game.combatants.push(e);e.aggro(false);}")
    pg.wait_for_timeout(6000);pg.screenshot(path=SHOTS+'c1_guards.png')
    print('guards fight',pg.evaluate("[Game.combatants.filter(c=>c.group==='evtX').map(c=>c.dead?'x':Math.round(c.hp)).join(','),Game.allies.map(a=>Math.round(a.hp)+(a.downed?'D':'')).join(',')]"))
    # еліта
    print('elite',pg.evaluate("""(()=>{CONFIG.elite.chance=1;const e=makeCombatant({type:'enemy',etype:'bandit',x:30,y:30,group:'gg',level:10,scale:true});CONFIG.elite.chance=0.07;
      const n=makeCombatant({type:'enemy',etype:'bandit',x:30,y:30,group:'gg',level:10});return [e.name,e.elite,e.maxHp,n.maxHp,e.lvlMult.toFixed(2),n.lvlMult.toFixed(2),enemyXp(e),enemyXp(n)]})()"""))
    pg.evaluate("CONFIG.elite.chance=1;const e=makeCombatant({type:'enemy',etype:'brute',x:Game.hero.x+3,y:Game.hero.y+2,group:'gg',level:Game.heroData.level});Game.combatants.push(e);CONFIG.elite.chance=0.07");
    pg.wait_for_timeout(600);pg.screenshot(path=SHOTS+'c2_elite.png')
    # порівняння
    pg.evaluate("Game.heroData.inventory.items=[];giveItem(generateItem('chainmail',8,2));giveItem(generateItem('copper_ring',8,2));giveItem(generateItem('copper_ring',8,1));")
    pg.evaluate("equipItem(Game.heroData.inventory.items.find(e=>e.it.base==='copper_ring').it)")
    print('cmp',pg.evaluate("UI.itemTipCompare(Game.heroData.inventory.items.find(e=>e.it.base==='chainmail').it,true).replace(/<[^>]+>/g,' | ').slice(0,500)"))
    print('cmp ring',pg.evaluate("UI.itemTipCompare(Game.heroData.inventory.items.find(e=>e.it.base==='copper_ring').it,true).replace(/<[^>]+>/g,' | ').slice(0,300)"))
    pg.evaluate("Game.openInventory&&Game.openInventory()");pg.wait_for_timeout(300)
    # спрайти
    pg.evaluate("""(()=>{const cv=document.createElement('canvas');cv.width=560;cv.height=130;cv.id='tt';document.body.appendChild(cv);cv.style='position:fixed;left:0;top:0;z-index:999;background:#7a6;image-rendering:pixelated';
      const c=cv.getContext('2d');c.imageSmoothingEnabled=false;let x=0;for(const et of ['shield','healer'])for(const [d,f] of [['down',4],['side',4],['up',4],['side',6],['down',7]]){const s=getRatSprite(ENEMY_DEFS[et].look,d,f);c.drawImage(s.canvas,x,0,s.canvas.width*2,s.canvas.height*2);x+=56;}})()""")
    pg.locator('#tt').screenshot(path=SHOTS+'c3_spr.png')
    print('ERRORS',errs[:5]);b.close()
