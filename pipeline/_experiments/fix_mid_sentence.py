"""Fix mid-sentence newline issue (e.g., Supplementary\nStandard)"""
import re

with open('parse_obc_v4.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 찾을 코드: 하위 조항 줄바꿈 추가 후, return 전
old_code = """    # 하위 조항 (a), (b), (i), (ii) 앞에 줄바꿈 추가
    text = re.sub(r'\\s{2,}(\\([a-z]\\))', r'\\n\\1', text)  # (a), (b), ...
    text = re.sub(r'\\s{2,}(\\([ivxlc]+\\))', r'\\n\\1', text)  # (i), (ii), ...

    return text.strip()"""

# 새 코드: 문장 중간 줄바꿈 제거 추가
new_code = """    # 하위 조항 (a), (b), (i), (ii) 앞에 줄바꿈 추가
    text = re.sub(r'\\s{2,}(\\([a-z]\\))', r'\\n\\1', text)  # (a), (b), ...
    text = re.sub(r'\\s{2,}(\\([ivxlc]+\\))', r'\\n\\1', text)  # (i), (ii), ...

    # 문장 중간 줄바꿈 제거 (PDF 줄넘김)
    # 소문자 + \\n + 대문자단어 (Table, Notes, Section, 9. 제외)
    text = re.sub(r'([a-z])\n(?!Table|Notes|Section|Article|Forming|9\\.)([A-Z][a-z]{2,})', r'\\1 \\2', text)

    return text.strip()"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('parse_obc_v4.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed: Mid-sentence newline removal added")
else:
    print("ERROR: Target code not found")
    # 디버깅: 현재 코드 확인
    match = re.search(r'# 하위 조항.+?return text\.strip\(\)', content, re.DOTALL)
    if match:
        print("Current code:")
        print(repr(match.group()))
