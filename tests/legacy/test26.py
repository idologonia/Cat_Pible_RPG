# Мобільний HUD: верхні кнопки, сенсорні кнопки й дерево навичок не виходять за екран і не перекриваються
import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
GAME=(ROOT/'cat-pibble-rpg.html').as_uri()
SHOTS=str(ROOT/'tests'/'shots')+'/'
os.makedirs(SHOTS,exist_ok=True)
from playwright.sync_api import sync_playwright
errs=[]
CHECK="""(()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&e.offsetParent!==null};
 const els=[...document.querySelectorAll('#heroBox,#mapBox,#hudBtns button,#safeTag,#tracker,#coopTag,#touchBtns .hslot,#btnInteract')].filter(vis);const bad=[];
 for(let i=0;i<els.length;i++){const a=els[i].getBoundingClientRect();if(a.left<0||a.right>innerWidth||a.top<0||a.bottom>innerHeight)bad.push('за екраном: '+(els[i].id||els[i].className));
  for(let j=i+1;j<els.length;j++){if(els[i].contains(els[j]))continue;const c=els[j].getBoundingClientRect();
   if(els[i].closest('#touchBtns')&&els[j].closest('#touchBtns'))continue;
   const w=Math.min(a.right,c.right)-Math.max(a.left,c.left),h=Math.min(a.bottom,c.bottom)-Math.max(a.top,c.top);if(w>2&&h>2)bad.push((els[i].id||els[i].className)+' x '+(els[j].id||els[j].className));}}
 return bad;})()"""
with sync_playwright() as p:
    b=p.chromium.launch()
    for dev in ['iPhone SE','iPhone 13','Pixel 7','iPhone 13 landscape','Pixel 7 landscape','iPad Mini']:
        ctx=b.new_context(**p.devices[dev]);pg=ctx.new_page();pg.on('pageerror',lambda e: errs.append(str(e)))
        pg.goto(GAME);pg.wait_for_timeout(500);pg.tap('#btnNew');pg.tap('#btnSkip');pg.tap('#btnStart');pg.wait_for_timeout(1200)
        pg.evaluate("Quests.start('main')");pg.wait_for_timeout(300);pg.evaluate("$('ptsBadge').classList.remove('hidden');$('skBadge').classList.remove('hidden');$('btnInteract').classList.remove('hidden');$('coopTag').textContent='Кімната ABCD · гравців 4/4';$('coopTag').classList.remove('hidden')")
        for w,c in [('clear',500),('fog',1150)]:
            pg.evaluate(f"Game.flags.clock={c};Game.weather={{type:'{w}',k:1,until:1e9}};Game.refreshHud&&Game.refreshHud()");pg.wait_for_timeout(700)
            bad=pg.evaluate(CHECK);print(dev,w,bad or 'OK')
            if bad:errs.append(f'{dev} {w}: {bad}')
        pg.tap('#btnSkills');pg.wait_for_timeout(300)
        sk=pg.evaluate("(()=>{const g=$('skGrid').getBoundingClientRect();return !$('skills').classList.contains('hidden')&&g.left>=0&&g.right<=innerWidth})()")
        print(dev,'дерево навичок',sk,pg.evaluate("$('skRule').textContent"))
        if not sk:errs.append(dev+': дерево навичок')
        pg.screenshot(path=SHOTS+'m_'+dev.replace(' ','_')+'.png');ctx.close()
    print('ERRORS',errs[:5]);b.close()
