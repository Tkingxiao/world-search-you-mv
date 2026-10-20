"""Fix the validation wording in README (34 PASS + 2 INFO, 0 FAIL)."""
import io

P = r'D:\Code\Code MV\new-word.search(you)\README.md'
s = io.open(P, encoding='utf-8').read()
old = '34/34 项自动校验 PASS，报告见 '
new = '自动校验 34 PASS / 2 INFO / 0 FAIL，报告见 '
assert old in s
s = s.replace(old, new, 1)
io.open(P, 'w', encoding='utf-8').write(s)
print('[ok] README validation wording fixed')
