#!/usr/bin/env python3
"""
Marker part8.md → Part 8 JSON 변환

Part 11 형식으로 출력:
- [ARTICLE:ID:Title] 마커
- <table class="obc-table"> HTML 테이블
- <h5 class="table-notes-title">Notes to Table X:</h5>
"""

import json
import re
from pathlib import Path

MARKER_PATH = Path(__file__).parent.parent / "data" / "marker" / "part8.md"
OUTPUT_PATH = Path(__file__).parent.parent / "codevault" / "public" / "data" / "part8.json"

# Section 제목 매핑
SECTION_TITLES = {
    "8.1": "General",
    "8.2": "Design Standards",
    "8.3": "Class 1 Sewage Systems",
    "8.4": "Class 2 Sewage Systems",
    "8.5": "Class 3 Sewage Systems",
    "8.6": "Class 4 Sewage Systems",
    "8.7": "Leaching Beds",
    "8.8": "Class 5 Sewage Systems",
    "8.9": "Operation and Maintenance"
}

SUBSECTION_TITLES = {
    "8.1.1": "Scope",
    "8.1.2": "Application",
    "8.1.3": "Limitations",
    "8.2.1": "General Requirements",
    "8.2.2": "Treatment and Holding Tanks",
    "8.3.1": "General Requirements",
    "8.3.2": "Superstructure Requirements",
    "8.3.3": "Earth Pit Privy",
    "8.3.4": "Privy Vaults and Pail Privy",
    "8.3.5": "Portable Privy",
    "8.4.1": "General Requirements",
    "8.4.2": "Design and Construction Requirements",
    "8.5.1": "General Requirements",
    "8.5.2": "Design and Construction Requirements",
    "8.6.1": "General Requirements",
    "8.6.2": "Treatment Units",
    "8.7.1": "General Requirements",
    "8.7.2": "Design and Construction Requirements",
    "8.7.3": "Absorption Trench Construction",
    "8.7.4": "Fill Based Absorption Trenches",
    "8.7.5": "Filter Beds",
    "8.7.6": "Shallow Buried Trench",
    "8.7.7": "Type A Dispersal Beds",
    "8.7.8": "Type B Dispersal Beds",
    "8.8.1": "Application",
    "8.8.2": "General Requirements",
    "8.9.1": "General",
    "8.9.2": "Operation",
    "8.9.3": "Maintenance"
}


def clean_text(text: str) -> str:
    """텍스트 정리"""
    # 이미지 참조 제거
    text = re.sub(r'!\[\]\([^)]+\)', '', text)
    # span 태그 제거
    text = re.sub(r'<span[^>]*>|</span>', '', text)
    # 연속 빈 줄 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_markdown_table(table_text: str) -> str:
    """Markdown 파이프 테이블 → HTML 테이블 변환"""
    lines = [l.strip() for l in table_text.strip().split('\n') if l.strip()]

    if len(lines) < 2:
        return table_text

    # 헤더 파싱
    if not lines[0].startswith('|'):
        return table_text

    headers = [cell.strip() for cell in lines[0].split('|')[1:-1]]

    # 구분선 확인
    if len(lines) > 1 and re.match(r'\|[\s\-:]+\|', lines[1]):
        data_start = 2
    else:
        data_start = 1

    # 데이터 행 파싱
    rows = []
    for line in lines[data_start:]:
        if line.startswith('|'):
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            rows.append(cells)

    # HTML 생성
    html = ['<table class="obc-table">']

    if headers:
        html.append('<thead><tr>')
        for h in headers:
            html.append(f'<th>{h}</th>')
        html.append('</tr></thead>')

    if rows:
        html.append('<tbody>')
        for row in rows:
            html.append('<tr>')
            for cell in row:
                html.append(f'<td>{cell}</td>')
            html.append('</tr>')
        html.append('</tbody>')

    html.append('</table>')
    return ''.join(html)


def convert_tables_in_content(content: str) -> str:
    """Content 내의 Markdown 테이블을 HTML로 변환"""
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 파이프 테이블 시작 감지
        if line.strip().startswith('|') and '|' in line[1:]:
            table_lines = [line]
            i += 1

            while i < len(lines):
                next_line = lines[i]
                if next_line.strip().startswith('|') or re.match(r'^\|?[\s\-:]+\|', next_line.strip()):
                    table_lines.append(next_line)
                    i += 1
                else:
                    break

            if len(table_lines) >= 2:
                html_table = parse_markdown_table('\n'.join(table_lines))
                result.append(html_table)
            else:
                result.extend(table_lines)
        else:
            result.append(line)
            i += 1

    return '\n'.join(result)


def convert_table_headings(content: str) -> str:
    """테이블 헤딩을 HTML로 변환"""
    # ### Table X.X.X.X.-X Title → <h4 class="table-title">...</h4>
    # **Table X.X.X.X. Title** → <h4 class="table-title">...</h4>

    # Pattern 1: Markdown heading format (### Table ...)
    pattern1 = r'^#{1,4}\s*(Table 8\.\d+\.\d+\.\d+\.(?:-[A-Z])?(?:\s*\(Cont\'d\))?)\s*(.*)$'

    # Pattern 2: Bold format (**Table 8.x.x.x. Title**)
    pattern2 = r'^\*{1,2}(Table 8\.\d+\.\d+\.\d+\.?(?:-[A-Z])?[^*]*)\*{1,2}\s*(.*)$'

    def replace(m):
        table_id = m.group(1).strip()
        rest = m.group(2).strip()
        if rest:
            return f'\n<h4 class="table-title">{table_id} {rest}</h4>'
        return f'\n<h4 class="table-title">{table_id}</h4>'

    content = re.sub(pattern1, replace, content, flags=re.MULTILINE)
    content = re.sub(pattern2, replace, content, flags=re.MULTILINE)
    return content


def convert_notes_headings(content: str) -> str:
    """Notes to Table 헤딩 변환"""
    pattern = r'^#{1,5}\s*\*{0,2}(Notes to Table[^:*\n]+):?\*{0,2}\s*$'

    def replace(m):
        notes_text = m.group(1).strip()
        return f'\n<h5 class="table-notes-title">{notes_text}:</h5>'

    return re.sub(pattern, replace, content, flags=re.MULTILINE)


def convert_article_markers(content: str) -> str:
    """Article 헤딩을 [ARTICLE:ID:Title] 마커로 변환"""
    # ### 8.1.1.1. Scope → [ARTICLE:8.1.1.1:Scope]
    pattern = r'^#{1,4}\s*(8\.\d+\.\d+\.\d+\.)\s*(.+)$'

    def replace(m):
        article_id = m.group(1).rstrip('.')
        title = m.group(2).strip()
        # **(See Note...)** 같은 거 제거
        title = re.sub(r'\s*\*{0,2}\(See Note[^)]+\)\*{0,2}', '', title)
        return f'\n[ARTICLE:{article_id}:{title}]'

    return re.sub(pattern, replace, content, flags=re.MULTILINE)


def process_clauses(content: str) -> str:
    """Clause 형식 정리"""
    # - **(1)** → (1)
    content = re.sub(r'^-\s*\*{0,2}\((\d+)\)\*{0,2}', r'(\1)', content, flags=re.MULTILINE)
    # - (a) → (a)
    content = re.sub(r'^-\s*\(([a-z])\)', r'(\1)', content, flags=re.MULTILINE)
    # - (i) → (i)
    content = re.sub(r'^-\s*\(([ivx]+)\)', r'(\1)', content, flags=re.MULTILINE)
    # **(1)** → (1)
    content = re.sub(r'\*{2}\((\d+)\)\*{2}', r'(\1)', content)
    return content


def parse_marker_file():
    """Marker part8.md 파싱"""

    with open(MARKER_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # 목차 부분 제거 (첫 번째 Section 시작 전까지)
    section_start = content.find('# <span id="page-680-0"></span>Section 8.1.')
    if section_start == -1:
        section_start = content.find('Section 8.1.')

    if section_start > 0:
        content = content[section_start:]

    # 기본 정리
    content = clean_text(content)

    # Section 분리
    section_pattern = r'(?:^#\s*(?:<span[^>]*>)?Section\s*(8\.\d+)\.\s*([^\n<]+)|^#\s*(8\.\d+)\.\d+\.\s)'

    sections = []
    current_section = None
    current_subsection = None

    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Section 헤딩 감지: # Section 8.1. General 또는 ## 8.6.2. Treatment Units
        # span 태그 처리: <span id="page-xxx"></span> 가 있을 수 있음
        # (?!\d) 로 Article (8.x.x.x)이 Subsection으로 매칭되는 것 방지
        section_match = re.match(r'^#{1,4}\s*(?:<span[^>]*>)?(?:</span>)?\s*Section\s*(8\.\d+)\.', line)
        subsection_match = re.match(r'^#{1,4}\s*(?:<span[^>]*>)?(?:</span>)?\s*(8\.\d+\.\d+)\.(?!\d)', line)

        if section_match:
            section_id = section_match.group(1)
            if current_section:
                if current_subsection:
                    current_section['subsections'].append(current_subsection)
                sections.append(current_section)

            current_section = {
                'id': section_id,
                'title': SECTION_TITLES.get(section_id, ''),
                'subsections': []
            }
            current_subsection = None
            i += 1
            continue

        if subsection_match:
            subsection_id = subsection_match.group(1)

            # 이전 Subsection 저장
            if current_subsection and current_section:
                current_section['subsections'].append(current_subsection)

            # Section이 없으면 생성
            if not current_section:
                section_id = '.'.join(subsection_id.split('.')[:2])
                current_section = {
                    'id': section_id,
                    'title': SECTION_TITLES.get(section_id, ''),
                    'subsections': []
                }

            current_subsection = {
                'id': subsection_id,
                'title': SUBSECTION_TITLES.get(subsection_id, ''),
                'content': ''
            }
            i += 1
            continue

        # Content 수집
        if current_subsection is not None:
            current_subsection['content'] += line + '\n'

        i += 1

    # 마지막 저장
    if current_subsection and current_section:
        current_section['subsections'].append(current_subsection)
    if current_section:
        sections.append(current_section)

    # Content 후처리
    for section in sections:
        for subsection in section['subsections']:
            content = subsection['content']

            # 변환 적용
            content = convert_article_markers(content)
            content = convert_table_headings(content)
            content = convert_notes_headings(content)
            content = convert_tables_in_content(content)
            content = process_clauses(content)
            content = clean_text(content)

            subsection['content'] = content

    return {
        'id': '8',
        'title': 'Sewage Systems',
        'sections': sections
    }


def main():
    print("=== Marker part8.md → JSON 변환 ===\n")

    data = parse_marker_file()

    # 통계
    total_subsections = sum(len(s['subsections']) for s in data['sections'])
    total_articles = 0
    total_tables = 0

    for section in data['sections']:
        for subsection in section['subsections']:
            content = subsection['content']
            total_articles += len(re.findall(r'\[ARTICLE:', content))
            total_tables += len(re.findall(r'<table class="obc-table">', content))

    print(f"Sections: {len(data['sections'])}")
    print(f"Subsections: {total_subsections}")
    print(f"Articles: {total_articles}")
    print(f"Tables: {total_tables}")

    # 저장
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n저장됨: {OUTPUT_PATH}")

    # 샘플 출력
    print("\n=== 샘플 (8.2.1 처음 1000자) ===")
    for section in data['sections']:
        for subsection in section['subsections']:
            if subsection['id'] == '8.2.1':
                print(subsection['content'][:1000])
                break


if __name__ == "__main__":
    main()
