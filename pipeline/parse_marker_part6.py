#!/usr/bin/env python3
"""
Marker 301880_full.md -> Part 6 JSON 변환

Part 6: Heating, Ventilating and Air-Conditioning
- Section: 6.1 ~ 6.9
- Subsection: 6.X.X (일반) 또는 6.X.XA (대안 subsection)
- Article: 6.X.X.X 또는 6.X.X.XA (Article suffix)
"""

import json
import re
from pathlib import Path

MARKER_PATH = Path(__file__).parent.parent / "data" / "marker" / "301880_full.md"
OUTPUT_PATH = Path(__file__).parent.parent / "codevault" / "public" / "data" / "part6.json"

# Section 제목 매핑
SECTION_TITLES = {
    "6.1": "General",
    "6.2": "Design and Installation",
    "6.3": "Ventilation Systems",
    "6.4": "Heating Appliances",
    "6.5": "Thermal Insulation Systems",
    "6.6": "Refrigeration and Cooling Systems",
    "6.7": "Piping Systems",
    "6.8": "Equipment Access",
    "6.9": "Fire Safety Systems"
}

# Subsection 제목 매핑 (목차에서 추출)
SUBSECTION_TITLES = {
    "6.1.1": "Application",
    "6.1.2": "Definitions",
    "6.2.1": "General",
    "6.2.2": "Incinerators",
    "6.2.3": "Solid Fuel Storage",
    "6.3.1": "Ventilation",
    "6.3.2": "Air Duct Systems",
    "6.3.3": "Chimneys and Venting Equipment",
    "6.3.4": "Ventilation for Laboratories",
    "6.4.1": "Heating Appliances, General",
    "6.4.2": "Unit Heaters",
    "6.4.3": "Radiators and Convectors",
    "6.5.1": "Insulation",
    "6.6.1": "Refrigerating Systems and Equipment for Air Conditioning",
    "6.7.1": "Piping for Heating and Cooling Systems",
    "6.7.2": "Storage Bins",
    "6.8.1": "Openings",
    "6.9.1": "General",
    "6.9.2": "Dampers and Ductwork",
    "6.9.3": "Carbon Monoxide Alarms",
    "6.9.4": "Ash Storage"
}


def convert_superscript(text: str) -> str:
    """<sup> 태그를 유니코드 위첨자로 변환"""
    superscript_map = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        '(': '⁽', ')': '⁾', '+': '⁺', '-': '⁻', '=': '⁼',
        'n': 'ⁿ', 'i': 'ⁱ',
    }

    def replace_sup(m):
        content = m.group(1)
        result = ''
        for char in content:
            result += superscript_map.get(char, char)
        return result

    return re.sub(r'<sup>([^<]+)</sup>', replace_sup, text, flags=re.IGNORECASE)


def clean_text(text: str) -> str:
    """텍스트 정리"""
    # 이미지 참조 제거 (줄바꿈 유지!)
    text = re.sub(r'!\[\]\([^)]+\)', '', text)
    # span 태그 제거
    text = re.sub(r'<span[^>]*>|</span>', '', text)
    # file:/// 링크 제거 (Word 문서 내부 링크) - [text](file:///...) → text
    text = re.sub(r'\[([^\]]+)\]\(file:///[^)]+\)', r'\1', text)
    # <sup> 태그를 유니코드 위첨자로 변환
    text = convert_superscript(text)
    # e1, e2, r1, r2 revision marker 제거
    text = re.sub(r'\s*\*{0,2}[er][12]\*{0,2}(?=\s|$|\.|\))', '', text)
    # 연속 빈 줄 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_markdown_table(table_text: str) -> str:
    """Markdown 파이프 테이블 -> HTML 테이블 변환"""
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
    """테이블 헤딩 정리 - Part 11 형식으로"""
    # Pattern 1: ### **Table X.X.X.X. Title** 또는 Bold로 감싸진 테이블 제목
    pattern1 = r'^#{0,4}\s*\*{2}(Table 6\.\d+\.\d+\.\d+\.?(?:-[A-Z])?[^*]*)\*{2}\s*(.*)$'

    def replace1(m):
        table_part = m.group(1).strip()
        rest = m.group(2).strip()
        table_part = re.sub(r'\s+', ' ', table_part)
        if rest:
            return f'#### {table_part} {rest}'
        return f'#### {table_part}'

    content = re.sub(pattern1, replace1, content, flags=re.MULTILINE)

    # Pattern 2: ### Table X.X.X.X. Title (Bold 없는 마크다운 헤딩)
    pattern2 = r'^#{1,4}\s*(Table 6\.\d+\.\d+\.\d+\.?(?:-[A-Z])?)\s*(.*)$'

    def replace2(m):
        table_id = m.group(1).strip()
        rest = m.group(2).strip()
        if rest:
            return f'#### {table_id} {rest}'
        return f'#### {table_id}'

    content = re.sub(pattern2, replace2, content, flags=re.MULTILINE)

    # Pattern 3: 줄바꿈으로 분리된 테이블 헤딩
    pattern3 = r'^(Table 6\.\d+\.\d+\.\d+\.?(?:-[A-Z])?)\s*\n\n(.+?)\n(Forming Part of.+)$'
    content = re.sub(pattern3, r'#### \1 \2 \3', content, flags=re.MULTILINE)

    return content


def convert_notes_headings(content: str) -> str:
    """Notes to Table 헤딩 변환"""
    # Pattern 1: ### Notes to Table... 또는 #### Notes to Table...
    pattern1 = r'^#{1,5}\s*\*{0,2}(Notes to Table[^:*\n]+):?\*{0,2}\s*$'
    content = re.sub(pattern1, r'\n<h5 class="table-notes-title">\1:</h5>', content, flags=re.MULTILINE)

    # Pattern 2: 마크다운 헤딩 없이 "Notes to Table X.X.X.X.:" 로 시작
    pattern2 = r'^(Notes to Table\s+\d+\.\d+\.\d+\.\d*\.?(?:-[A-Z])?):?\s*$'
    content = re.sub(pattern2, r'<h5 class="table-notes-title">\1:</h5>', content, flags=re.MULTILINE)

    return content


def add_dash_to_notes_items(content: str) -> str:
    """Notes 섹션 내의 (1), (2) 항목에 대시 추가"""
    def process_notes_section(m):
        notes_header = m.group(1)
        notes_content = m.group(2)
        notes_content = re.sub(r'^(\s*)(?!- )\((\d+)\)', r'\1- (\2)', notes_content, flags=re.MULTILINE)
        return notes_header + notes_content

    pattern = r'(<h5 class="table-notes-title">Notes to Table[^<]+</h5>\s*\n)(.*?)(?=\[ARTICLE:|#### Table|$)'
    content = re.sub(pattern, process_notes_section, content, flags=re.DOTALL)

    return content


def convert_article_markers(content: str) -> str:
    """Article 헤딩을 [ARTICLE:ID:Title] 마커로 변환"""
    # Article 패턴: ### 6.X.X.X. Title 또는 6.X.XA.X 또는 6.X.X.XA
    pattern = r'^#{1,4}\s*(6\.\d+\.\d+[A-Z]?\.\d+[A-Z]?)\.\s*(.+)$'

    def replace(m):
        article_id = m.group(1)
        title = m.group(2).strip()
        # Bold 제거
        title = re.sub(r'\*{1,2}', '', title)
        # (See Note...) 제거
        title = re.sub(r'\s*\(See Note[^)]+\)', '', title)
        # e1, e2 마커 제거
        title = re.sub(r'\s*\*{0,2}[er]\d+\*{0,2}$', '', title)
        return f'\n[ARTICLE:{article_id}:{title.strip()}]'

    return re.sub(pattern, replace, content, flags=re.MULTILINE)


def process_clauses(content: str) -> str:
    """Clause 형식 정리"""
    # Notes 섹션을 임시 마커로 보호
    notes_pattern = r'(<h5 class="table-notes-title">Notes to Table[^<]+</h5>.*?)(?=\[ARTICLE:|#### Table|\Z)'

    def protect_notes(m):
        notes_section = m.group(1)
        notes_section = re.sub(r'^- \((\d+)\)', r'__NOTES_ITEM__(\1)', notes_section, flags=re.MULTILINE)
        return notes_section

    content = re.sub(notes_pattern, protect_notes, content, flags=re.DOTALL)

    # 일반 clause에서 대시 제거
    content = re.sub(r'^\s*-\s*\*{0,2}\((\d+\.\d+)\)\*{0,2}', r'(\1)', content, flags=re.MULTILINE)
    content = re.sub(r'^\s*-\s*\*{0,2}\((\d+)\)\*{0,2}', r'(\1)', content, flags=re.MULTILINE)
    content = re.sub(r'^\s*-\s*\(([a-z])\)', r'(\1)', content, flags=re.MULTILINE)
    content = re.sub(r'^\s*-\s*\(([ivx]+)\)', r'(\1)', content, flags=re.MULTILINE)
    # 인라인 **(1)** -> (1)
    content = re.sub(r'\*{2}\((\d+)\)\*{2}', r'(\1)', content)

    # "- (See Note..." 대시 제거
    content = re.sub(r'^- \(See Note', r'(See Note', content, flags=re.MULTILINE)
    content = re.sub(r'^- \. \(See Note', r'(See Note', content, flags=re.MULTILINE)

    # Notes 마커 복원
    content = re.sub(r'__NOTES_ITEM__\((\d+)\)', r'- (\1)', content)

    return content


def convert_where_block_format(content: str) -> str:
    """수식의 where 블록을 Part 8 형식으로 변환"""
    # 1. "where:" → "where,"
    content = re.sub(r'^where\s*:\s*$', 'where,', content, flags=re.MULTILINE)

    def convert_variable_definitions(m):
        where_marker = m.group(1)
        definitions_block = m.group(2)

        lines = definitions_block.split('\n')
        converted_lines = []

        for line in lines:
            stripped = line.strip()

            if stripped.startswith('- '):
                converted_lines.append(line)
                continue

            if not stripped:
                converted_lines.append(line)
                continue

            var_match = re.match(r'^([A-Za-zγ]{1,3})\s+(?:is|=)\s+(.+)$', stripped)
            if var_match:
                var_name = var_match.group(1)
                description = var_match.group(2)
                converted_lines.append(f'- {var_name} = {description}')
            else:
                converted_lines.append(line)

        return where_marker + '\n' + '\n'.join(converted_lines)

    where_pattern = r'(where,)\n((?:(?!\n\n\n|\(\d+\)|\([a-z]\)|\[ARTICLE:|\#{4} Table).)*)'
    content = re.sub(where_pattern, convert_variable_definitions, content, flags=re.DOTALL)

    return content


def remove_bold_italic(content: str) -> str:
    """Bold/Italic 마크다운 제거"""
    content = re.sub(r'\*{2}([^*]+)\*{2}', r'\1', content)
    content = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'\1', content)
    return content


def extract_part6(full_content: str) -> str:
    """전체 Marker 출력에서 Part 6만 추출"""
    # Part 6 시작
    start_match = re.search(r'^# Part 6\s*$', full_content, re.MULTILINE)
    if not start_match:
        start_match = re.search(r'^# Section 6\.1\.', full_content, re.MULTILINE)
    if not start_match:
        raise ValueError("Part 6 not found in Marker output")

    # Part 7 시작 전까지
    end_match = re.search(r'^# Part 7\s*$', full_content[start_match.end():], re.MULTILINE)
    if end_match:
        return full_content[start_match.start():start_match.end() + end_match.start()]
    else:
        return full_content[start_match.start():]


def parse_marker_file():
    """Marker 파일 파싱"""

    with open(MARKER_PATH, 'r', encoding='utf-8') as f:
        full_content = f.read()

    # Part 6만 추출
    content = extract_part6(full_content)

    # 목차 부분 제거 (첫 번째 "# Section 6.1." 시작 전까지)
    section_start = re.search(r'^# (?:<span[^>]*>)?Section 6\.1\.', content, re.MULTILINE)
    if section_start:
        content = content[section_start.start():]

    # 기본 정리
    content = clean_text(content)

    sections = []
    current_section = None
    current_subsection = None

    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Section 헤딩 감지: # Section 6.1. General
        section_match = re.match(r'^#{1,4}\s*(?:<span[^>]*>)?Section\s*(6\.\d+)\.\s*(.*)$', line)

        # Subsection 헤딩 감지: # 6.1.1. Application
        # Article (6.x.x.x)이 매칭되지 않도록 (?!\d) 사용
        subsection_match = re.match(r'^#{1,4}\s*(?:<span[^>]*>)?(6\.\d+\.\d+[A-Z]?)\.(?!\d)\s*(.*)$', line)

        if section_match:
            section_id = section_match.group(1)
            section_title = section_match.group(2).strip()
            # span 태그 제거
            section_title = re.sub(r'<[^>]+>', '', section_title)

            # 이전 데이터 저장
            if current_section:
                if current_subsection:
                    current_section['subsections'].append(current_subsection)
                sections.append(current_section)

            current_section = {
                'id': section_id,
                'title': SECTION_TITLES.get(section_id, section_title),
                'subsections': []
            }
            current_subsection = None
            i += 1
            continue

        if subsection_match:
            subsection_id = subsection_match.group(1)
            subsection_title = subsection_match.group(2).strip()

            # Bold/마커/span 태그 제거
            subsection_title = re.sub(r'\*{1,2}', '', subsection_title)
            subsection_title = re.sub(r'\s*[er]\d+$', '', subsection_title)
            subsection_title = re.sub(r'<[^>]+>', '', subsection_title)

            # 이전 Subsection 저장
            if current_subsection and current_section:
                current_section['subsections'].append(current_subsection)

            # Section이 없으면 생성
            if not current_section:
                section_id = re.match(r'(6\.\d+)', subsection_id).group(1)
                current_section = {
                    'id': section_id,
                    'title': SECTION_TITLES.get(section_id, ''),
                    'subsections': []
                }

            current_subsection = {
                'id': subsection_id,
                'title': SUBSECTION_TITLES.get(subsection_id, subsection_title),
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
            content = add_dash_to_notes_items(content)
            content = convert_where_block_format(content)
            content = remove_bold_italic(content)
            content = clean_text(content)

            subsection['content'] = content

    return {
        'id': '6',
        'title': 'Heating, Ventilating and Air-Conditioning',
        'sections': sections
    }


def main():
    print("=== Marker -> Part 6 JSON 변환 ===\n")

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
            total_tables += len(re.findall(r'#### Table 6\.', content))

    print(f"Sections: {len(data['sections'])}")
    print(f"Subsections: {total_subsections}")
    print(f"Articles: {total_articles}")
    print(f"Tables: {total_tables}")

    # 저장
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n저장됨: {OUTPUT_PATH}")

    # 샘플 출력
    print("\n=== 샘플 (6.1.1 처음 1000자) ===")
    for section in data['sections']:
        for subsection in section['subsections']:
            if subsection['id'] == '6.1.1':
                print(subsection['content'][:1000])
                break


if __name__ == "__main__":
    main()
