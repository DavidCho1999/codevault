"""Fix newline for sub-clauses (a), (i), etc. - v2"""
import re

with open('parse_obc_v4.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 찾을 코드 (return text.strip() 전)
old_code = "return text.strip()"

# 새 코드: 공백 2개 이상 + (a), (i) 패턴을 줄바꿈으로
new_code = r"""# 하위 조항 (a), (b), (i), (ii) 앞에 줄바꿈 추가
    text = re.sub(r'\s{2,}(\([a-z]\))', r'\n\1', text)  # (a), (b), ...
    text = re.sub(r'\s{2,}(\([ivxlc]+\))', r'\n\1', text)  # (i), (ii), ...

    return text.strip()"""

# extract_page_text_sorted 함수 내의 return text.strip() 찾기
# 해당 함수는 라인 252 근처에 있음
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'return text.strip()' in line and i > 240 and i < 260:
        print(f"Found at line {i+1}: {line}")
        indent = len(line) - len(line.lstrip())
        lines[i] = ' ' * indent + '# 하위 조항 (a), (b), (i), (ii) 앞에 줄바꿈 추가\n'
        lines[i] += ' ' * indent + "text = re.sub(r'\\s{2,}(\\([a-z]\\))', r'\\n\\1', text)  # (a), (b), ...\n"
        lines[i] += ' ' * indent + "text = re.sub(r'\\s{2,}(\\([ivxlc]+\\))', r'\\n\\1', text)  # (i), (ii), ...\n"
        lines[i] += ' ' * indent + '\n'
        lines[i] += ' ' * indent + 'return text.strip()'

        with open('parse_obc_v4.py', 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print("Fixed: Added newline before (a), (i) patterns")
        break
else:
    print("ERROR: Target not found")
