# Кооператив (етап 26): ефекти навичок інших гравців, замахи ворогів у гостя, інші гравці на мінікарті
import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
errs=[]
def check(cond,what):
    print(('ok  ' if cond else 'FAIL'),what)
    if not cond:errs.append(what)
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':1280,'height':760})
    A=ctx.new_page();B=ctx.new_page()
    for pg,n in [(A,'A'),(B,'B')]:pg.on('pageerror',lambda e,n=n: errs.append(n+': '+str(e)+' '+(e.stack or '')[:300]))
    A.goto(GAME);A.wait_for_timeout(400);A.click('#btnNew');A.click('#btnSkip');A.click('#btnStart');A.wait_for_timeout(1000)
    A.evaluate("setInterval(()=>{Game.hero.iframe=99},100);Game.changeLocation('outskirts',{x:40,y:40})");A.wait_for_timeout(1300)
    A.evaluate("Net.hostRoom()");code=A.evaluate("Net.room")
    B.goto(GAME);B.wait_for_timeout(400);B.evaluate(f"Net.join('Маг','{code}','local')");B.wait_for_timeout(700)
    B.evaluate("UI.cc.cls='mage'");B.click('#btnStart');B.wait_for_timeout(2800)
    B.evaluate("setInterval(()=>{if(Game.hero)Game.hero.iframe=99},100)")
    check(B.evaluate("Net.isGuest()&&Game.locationId==='outskirts'"),'гість у грі')
    # навичка хоста (кільце) видно в гостя
    A.evaluate("addVfx({type:'ring',x:Game.hero.x,y:Game.hero.y,r0:0.2,r1:2.4,col:'#ffd23a',col2:'#fff2a8',dur:2})");B.wait_for_timeout(400)
    check(B.evaluate("Game.vfx.some(v=>v.type==='ring'&&v._n&&v.dur===2)"),'кільце навички хоста видно в гостя')
    # навичка гостя (крижане кільце мага) — у хоста
    B.evaluate("Game.heroData.res=999;castSkill(1,false)");A.wait_for_timeout(500)
    check(A.evaluate("Game.vfx.some(v=>v._n&&v.type==='ring')") ,'навичка гостя видна в хоста')
    B.screenshot(path=SHOTS+'co26_guest_skill.png');A.screenshot(path=SHOTS+'co26_host_sees.png')
    # спалахи частинок і зони
    n0=B.evaluate("Game.particles.length");A.evaluate("spawnBurst(Game.hero.x,Game.hero.y,10,'#ff00ff',30,2)");B.wait_for_timeout(300)
    check(B.evaluate("Game.particles.filter(p=>p.col==='#ff00ff').length")>=20,'спалах хоста видно в гостя')
    A.evaluate("Game.zones.push({x:Game.hero.x+2,y:Game.hero.y,r:2,t:0,dur:3,tick:0.5,next:0.15,spec:{mult:5,tags:['ranged']}})");B.wait_for_timeout(400)
    z=B.evaluate("(()=>{const z=Game.zones.find(z=>z._n&&z.r===2);return z?[!!z.spec,z.dur]:null})()")
    check(z is not None and z[0] is False,f'зона дощу стріл хоста видна в гостя без бойової частини {z}')
    # замах ворога видно в гостя
    A.evaluate("(()=>{const e=Game.combatants.find(c=>c.isEnemy&&!c.dead);addVfx({type:'slash',x:e.x,y:e.y,dx:1,dy:0,range:1.2,arc:120,col:'#ff7a6a',col2:'#ffd0c8',dur:1,thick:2});})()");B.wait_for_timeout(400)
    check(B.evaluate("Game.vfx.some(v=>v.type==='slash'&&v.col==='#ff7a6a')"),'замах ворога видно в гостя')
    # вихор не «прилипає» до чужого героя
    A.evaluate("addVfx({type:'slash',x:Game.hero.x,y:Game.hero.y,dx:1,dy:0,range:2,arc:360,col:'#ffffff',col2:'#cfd6dc',dur:1,thick:2,follow:true})");B.wait_for_timeout(400)
    check(B.evaluate("Game.vfx.filter(v=>v.arc===360&&v._n).every(v=>!v.follow)"),'вихор хоста не прилипає до героя гостя')
    # без петлі: отримані ефекти не пересилаються назад
    A.evaluate("addVfx({type:'ring',x:Game.hero.x,y:Game.hero.y,r0:0.2,r1:1,col:'#123456',dur:9})");A.wait_for_timeout(1500)
    ca=A.evaluate("Game.vfx.filter(v=>v.col==='#123456').length");cb=B.evaluate("Game.vfx.filter(v=>v.col==='#123456').length")
    check(ca==1 and cb==1,f'ефекти не ходять по колу (хост {ca}, гість {cb})')
    # мінікарта: інший гравець — блакитна крапка
    A.evaluate("Net.remotes[0].x=Game.hero.x+3;Net.remotes[0].tx=Game.hero.x+3")
    px=A.evaluate("""(()=>{Render.drawMinimap();const W=Game.world,k=W.minimapScale,r=Net.remotes[0],x=Math.round((W.groundOX+(r.x-r.y)*16)*k),y=Math.round(((r.x+r.y)*8)*k);
      return Array.from($('minimap').getContext('2d').getImageData(x,y,1,1).data)})()""")
    check(px[2]>200 and px[0]<180,f'інший гравець на мінікарті блакитний {px}')
    print('ERRORS',errs[:6]);b.close()
