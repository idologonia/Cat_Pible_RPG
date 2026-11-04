"""Перевірка синтаксису JS усередині cat-pibble-rpg.html (потрібен Node.js)."""
import pathlib,re,subprocess,sys,tempfile
root=pathlib.Path(__file__).resolve().parents[1]
s=(root/'cat-pibble-rpg.html').read_text(encoding='utf-8')
js='\n'.join(re.findall(r'<script>(.*?)</script>',s,re.S))
with tempfile.NamedTemporaryFile('w',suffix='.js',delete=False,encoding='utf-8') as f:f.write(js);p=f.name
r=subprocess.run(['node','-e',f"new Function(require('fs').readFileSync({p!r},'utf8'));console.log('syntax ok')"],capture_output=True,text=True)
print(r.stdout or r.stderr);sys.exit(r.returncode)
