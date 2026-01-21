"""
섹션 콘텐츠에서 중복된 테이블 참조 제거
- 같은 테이블이 여러 번 언급되면 첫 번째만 유지
- Notes to Table은 테이블 바로 다음에만 유지
"""

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

INPUT_FILE = Path(__file__).parent.parent / 'codevault/public/data/part9.json'
OUTPUT_FILE = Path(__file__).parent.parent / 'codevault/public/data/part9_fixed.json'


def remove_duplicate_table_refs(content: str) -> str:
    """콘텐츠에서 중복된 테이블 블록 제거"""
    lines = content.split('\n')
    result = []
    seen_tables = set()
    skip_until_next_article = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # 테이블 시작 패턴 감지
        table_match = re.match(r'^Table\s+(9\.\d+\.\d+\.\d+)(.-[A-G])?\.?\s*', line)

        if table_match:
            table_id = f"Table {table_match.group(1)}{table_match.group(2) or ''}"

            if table_id in seen_tables:
                # 이미 본 테이블 - 다음 Article까지 스킵
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    # 새 Article 시작 감지
                    if re.match(r'^\d+\.\d+\.\d+\.\d+\.', next_line):
                        break
                    # 다른 테이블 시작 감지
                    if re.match(r'^Table\s+9\.\d+\.\d+\.\d+', next_line):
                        break
                    i += 1
                continue
            else:
                seen_tables.add(table_id)
                result.append(line)
        else:
            result.append(line)

        i += 1

    return '\n'.join(result)


def process_subsection(subsection: dict) -> dict:
    """하위 섹션 처리"""
    if 'content' in subsection:
        original = subsection['content']
        fixed = remove_duplicate_table_refs(original)

        # 변경사항 리포트
        orig_tables = len(re.findall(r'Table 9\.\d+\.\d+\.\d+', original))
        fixed_tables = len(re.findall(r'Table 9\.\d+\.\d+\.\d+', fixed))

        if orig_tables != fixed_tables:
            print(f"  {subsection.get('id')}: {orig_tables} -> {fixed_tables} 테이블 참조")

        subsection['content'] = fixed

    return subsection


def fix_part9_data():
    print("=== Part 9 콘텐츠 중복 제거 ===\n")

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    sections = data.get('sections', [])
    print(f"섹션 수: {len(sections)}")

    for section in sections:
        section_id = section.get('id', '')
        subsections = section.get('subsections', [])

        if subsections:
            print(f"\n[{section_id}] {section.get('title', '')}")
            for i, sub in enumerate(subsections):
                subsections[i] = process_subsection(sub)

    # 저장
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n저장됨: {OUTPUT_FILE}")


if __name__ == "__main__":
    fix_part9_data()
