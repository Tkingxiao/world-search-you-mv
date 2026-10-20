import io
import py_compile

p = 'mv/tools/supervise.py'
s = io.open(p, encoding='utf-8').read()

helper = '''
def actual_renderers():
    """Count live blender processes currently rendering a shot (any owner)."""
    ps = ('Get-WmiObject Win32_Process -Filter "Name=\\'blender.exe\\'" | '
          'ForEach-Object { $_.CommandLine }')
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                           capture_output=True, text=True, timeout=120)
    except Exception:
        return 0
    return sum(1 for line in (r.stdout or '').splitlines() if '--shot' in line and 'render_shot.py' in line)


def main():'''
if 'def actual_renderers' not in s:
    s = s.replace('def main():', helper, 1)

old = '        slots_busy = len(ours) + len(busy)'
new = ('        slots_busy = max(len(ours) + len(busy), actual_renderers())')
if old not in s:
    raise SystemExit('slots_busy marker not found')
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8').write(s)
py_compile.compile(p, doraise=True)
print('patched + compiles')
