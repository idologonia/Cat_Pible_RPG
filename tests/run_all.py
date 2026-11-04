"""Запуск усіх регресійних тестів. Використання: python tests/run_all.py [фільтр]"""
import pathlib,subprocess,sys
here=pathlib.Path(__file__).resolve().parent
flt=sys.argv[1] if len(sys.argv)>1 else ''
r=subprocess.run([sys.executable,str(here/'check_syntax.py')]);
if r.returncode:sys.exit(1)
bad=[]
for t in sorted((here/'legacy').glob('test*.py'),key=lambda p:int(''.join(c for c in p.stem if c.isdigit()) or 0)):
    if flt not in t.name:continue
    p=subprocess.run([sys.executable,str(t)],capture_output=True,text=True,timeout=600)
    tail=(p.stdout.strip().splitlines() or [''])[-1]
    ok=p.returncode==0 and 'ERRORS []' in p.stdout
    print(('OK  ' if ok else 'FAIL'),t.name,'|',tail[:110])
    if not ok:bad.append(t.name);print(p.stderr[-1500:])
print('\nУсе пройшло.' if not bad else f'\nВпали: {bad}');sys.exit(1 if bad else 0)
