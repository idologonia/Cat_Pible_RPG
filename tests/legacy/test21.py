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
def qs(pg): return pg.evaluate("JSON.stringify(Object.fromEntries(Object.entries(Game.flags.q||{}).filter(([k])=>k.startsWith('witch')).map(([k,v])=>[k,v.state+':'+v.step])))")
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':760})
    pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:400]))
    pg.goto(GAME);pg.wait_for_timeout(400);pg.click('#btnNew');pg.click('#btnSkip');pg.click('#btnStart');pg.wait_for_timeout(600)
    pg.evaluate("while(Game.heroData.level<16)gainXp(xpToNext(Game.heroData.level))")
    pg.evaluate("Game.changeLocation('swamp',null)");pg.wait_for_timeout(1300);pg.evaluate("Game.hero.iframe=1e9")
    print('npcs',pg.evaluate("Game.npcs.map(n=>n.id)"))
    talk(pg,'ropukha');pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'f1_frog.png');print(opts(pg))
    i=[k for k,o in enumerate(opts(pg)) if 'вариш' in o][0];pick(pg,i);pick(pg,0);pick(pg,0);print(qs(pg))
    pg.evaluate("for(const o of Game.world.objects)if(o.kind==='node'&&o.res==='fly_agaric')gatherNode(o)")
    pg.evaluate("giveItem(makeItem('fly_agaric'),6)");pg.wait_for_timeout(1700);print(qs(pg))
    talk(pg,'ropukha');print(opts(pg));i=[k for k,o in enumerate(opts(pg)) if 'приніс' in o][0];pick(pg,i);pick(pg,0);print(qs(pg),pg.evaluate("[Inv.count(Game.heroData,'weak_tincture'),Game.flags.tincW,UI.hotSlots.map(s=>s.s.act).join(',')]"))
    talk(pg,'ropukha');print(opts(pg));i=[k for k,o in enumerate(opts(pg)) if 'рецепти' in o][0];pick(pg,i);pick(pg,0);pick(pg,0);print(qs(pg))
    # слиз з п'явок
    pg.evaluate("for(const c of [...Game.combatants])if(c.isEnemy&&!c.dead&&c.group==='s2'){c.hp=1;hitTarget(c,{mult:900});}");pg.wait_for_timeout(500)
    print('slime drops',pg.evaluate("Game.groundItems.filter(g=>g.it.base==='leech_slime').length"))
    pg.evaluate("giveItem(makeItem('leech_slime'),4)");pg.wait_for_timeout(1700)
    talk(pg,'ropukha');i=[k for k,o in enumerate(opts(pg)) if 'приніс' in o][0];pick(pg,i);pick(pg,0);print(qs(pg),pg.evaluate("Inv.count(Game.heroData,'poison_tincture')"))
    # кидання
    pg.evaluate("UI.closeDialog&&UI.closeDialog()");
    pg.evaluate("(()=>{const e=Game.combatants.find(c=>c.isEnemy&&!c.dead&&c.group==='s1');Game.hero.x=e.x+4;Game.hero.y=e.y+1;})()");pg.wait_for_timeout(400)
    tgt=pg.evaluate("(()=>{const e=Game.combatants.find(c=>c.isEnemy&&!c.dead&&c.group==='s1');return Render.worldToScreenCss(e.x,e.y,20)})()")
    pg.mouse.move(tgt[0],tgt[1]);pg.wait_for_timeout(100)
    pg.keyboard.press('KeyF');pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'f2_throw.png');pg.wait_for_timeout(600)
    print('weak',pg.evaluate("Game.combatants.filter(c=>c.group==='s1'&&c.st.weak>0).map(c=>c.lvlMult.toFixed(2)+'/'+c.baseLvlMult.toFixed(2))"))
    pg.wait_for_timeout(1300);pg.keyboard.press('KeyG');pg.wait_for_timeout(900)
    print('poison',pg.evaluate("Game.combatants.filter(c=>c.group==='s1'&&c.st.poison>0).length"),pg.evaluate("[Inv.count(Game.heroData,'weak_tincture'),Inv.count(Game.heroData,'poison_tincture')]"))
    pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'f3_poison.png')
    # крафт рецепту
    print('recipes',pg.evaluate("[knowsRecipe('weak_tincture'),knowsRecipe('poison_tincture')]"))
    print('ERRORS',errs[:5]);b.close()
