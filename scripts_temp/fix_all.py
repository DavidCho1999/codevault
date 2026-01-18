"""Apply all newline fixes to parse_obc_v4.py"""

with open('parse_obc_v4.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: 하위 조항 줄바꿈 + 문장 중간 줄바꿈 수정
old_code = "    return text.strip()"

# extract_page_text_sorted 함수 내의 첫 번째 return text.strip() 찾기
# 라인 252 근처
lines = content.split('\n')
found = False
for i, line in enumerate(lines):
    if line.strip() == 'return text.strip()' and 245 < i < 260:
        print(f"Found 'return text.strip()' at line {i+1}")

        new_lines = [
            '    # 하위 조항 (a), (b), (i), (ii) 앞에 줄바꿈 추가',
            "    text = re.sub(r'\\s{2,}(\\([a-z]\\))', r'\\n\\1', text)  # (a), (b), ...",
            "    text = re.sub(r'\\s{2,}(\\([ivxlc]+\\))', r'\\n\\1', text)  # (i), (ii), ...",
            '',
            '    # 문장 중간 줄바꿈 제거 (PDF 줄넘김)',
            '    # 소문자 + newline + 대문자단어 (Table, Notes, Section, 9. 제외)',
            "    text = re.sub(r'([a-z])\\n(?!Table|Notes|Section|Article|Forming|9\\.)([A-Z][a-z]{2,})', r'\\1 \\2', text)",
            '',
            '    return text.strip()'
        ]

        lines[i] = '\n'.join(new_lines)
        found = True
        break

if found:
    with open('parse_obc_v4.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print("All fixes applied successfully!")
else:
    print("ERROR: Target not found")
