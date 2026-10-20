import io
import py_compile

p = 'mv/tools/supervise.py'
s = io.open(p, encoding='utf-8').read()
if 'import re' not in s:
    s = s.replace('import argparse\nimport json', 'import argparse\nimport json\nimport re', 1)
old = '        pending = [s for s in ALL if not complete(s)]'
new = ('        claimed = planned_by_drivers()\n'
       '        pending = [s for s in ALL if not complete(s) and s not in claimed]')
if old not in s:
    raise SystemExit('marker line not found')
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8').write(s)
py_compile.compile(p, doraise=True)
print('patched + compiles')
