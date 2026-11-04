import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':1280,'height':760})
    pg.on('pageerror',lambda e: errs.append(str(e)+' '+(e.stack or '')[:400]))
    pg.on('console',lambda m: errs.append('console:'+m.text) if m.type=='error' else None)
    pg.goto(GAME);pg.wait_for_timeout(400)
    pg.click('#btnNew');pg.wait_for_timeout(300)
    print('audio',pg.evaluate("[AudioSys.ok,AudioSys.ctx&&AudioSys.ctx.state,AudioSys.cur&&AudioSys.cur.id]"))
    pg.click('#btnSkip');pg.click('#btnStart');pg.wait_for_timeout(1200)
    print('music after start',pg.evaluate("[AudioSys.wantTrack,AudioSys.cur&&AudioSys.cur.id,Game.locationId]"))
    pg.evaluate("window._snd=[];const p=AudioSys.play.bind(AudioSys);AudioSys.play=function(n,o){_snd.push(n);return p(n,o);}")
    for n in pg.evaluate("Object.keys(SFX)"): pg.evaluate(f"AudioSys.last={{}};AudioSys.play('{n}')");
    pg.wait_for_timeout(500);print('all sfx ok')
    pg.evaluate("window._snd=[]")
    pg.evaluate("Game.changeLocation('outskirts',{x:44,y:28})");pg.wait_for_timeout(1500)
    pg.evaluate("Game.heroData.hp=9999;Game.derived.maxHp=9999")
    # атакуємо опудало, отримуємо удари
    pg.mouse.move(700,380);pg.mouse.down();pg.wait_for_timeout(700);pg.mouse.up()
    pg.keyboard.press('Digit1');pg.wait_for_timeout(400);pg.keyboard.press('Space');pg.wait_for_timeout(400)
    pg.evaluate("gainXp(xpToNext(Game.heroData.level));Game.coins.push({x:Game.hero.x,y:Game.hero.y,z:0,vz:0,amount:5,t:1})");pg.wait_for_timeout(600)
    pg.evaluate("heroTakeDamage(5,Game.hero.x+1,Game.hero.y)");pg.wait_for_timeout(200)
    print('sounds',sorted(set(pg.evaluate("_snd"))))
    print('music now',pg.evaluate("AudioSys.cur&&AudioSys.cur.id"))
    for loc in ['city','cemetery','crypt','outpost','village','cheese','swamp','forest']:
        pg.evaluate(f"Game.changeLocation('{loc}',null)");pg.wait_for_timeout(1300)
        print(' ',loc,pg.evaluate("AudioSys.cur&&AudioSys.cur.id"))
    pg.evaluate("const e=Game.combatants.find(c=>c.isEnemy);e.aggro(false);Game.hero.x=e.x+2;Game.hero.y=e.y");pg.wait_for_timeout(1200)
    print('combat',pg.evaluate("AudioSys.combat"))
    # різниця рівнів
    print('gap',pg.evaluate("""(()=>{const hd=Game.heroData;hd.level=8;const r=[];for(const L of [6,8,10,14]){const e=makeCombatant({type:'enemy',etype:'bandit',x:5,y:5,level:L});Game.combatants.push(e);e.update(0.01);
      const hp0=e.hp;let s=0;for(let i=0;i<40;i++){e.hp=hp0;e.dead=false;hitTarget(e,{mult:1});s+=hp0-e.hp;}r.push(L+': dmgTaken '+Math.round(s/40)+' lvlMult '+e.lvlMult.toFixed(2)+' base '+e.baseLvlMult.toFixed(2)+' xp '+enemyXp(e));}return r})()"""))
    print('xp table',pg.evaluate("[2,5,10,15,20,25].map(l=>l+':'+xpToNext(l))"))
    pg.keyboard.press('Escape');pg.wait_for_timeout(300);pg.screenshot(path=SHOTS+'b1_pause.png')
    pg.evaluate("$('volMusic').value=20;$('volMusic').oninput()");print('vol',pg.evaluate("[AudioSys.vol.music,localStorage.getItem('cpg_audio')]"))
    print('ERRORS',errs[:6]);b.close()
