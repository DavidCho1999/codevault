#!/usr/bin/env python3
"""
Marker 301880_full.md -> Part 7 JSON 변환

Part 7: Plumbing
- Section: 7.1 ~ 7.7
- Subsection: 7.X.X 또는 7.X.XA/B (Alternative)
- Article: 7.X.X.X
"""

import json
import re
from pathlib import Path

MARKER_PATH = Path(__file__).parent.parent / "data" / "marker" / "301880_full.md"
OUTPUT_PATH = Path(__file__).parent.parent / "codevault" / "public" / "data" / "part7.json"

# Section 제목 매핑
SECTION_TITLES = {
    "7.1": "General",
    "7.2": "Materials and Equipment",
    "7.3": "Piping",
    "7.4": "Drainage Systems",
    "7.5": "Venting Systems",
    "7.6": "Potable Water Systems",
    "7.7": "Non-Potable Water Systems"
}

# Subsection 제목 매핑 (목차에서 추출)
SUBSECTION_TITLES = {
    "7.1.0": "Scope",
    "7.1.1": "Application",
    "7.1.1A": "Definitions",
    "7.1.1B": "Plumbing Facilities",
    "7.1.2": "Service Connections",
    "7.1.3": "Location of Fixtures",
    "7.1.3A": "Accommodating Movement",
    "7.1.4": "Seismic Design",
    "7.2.1": "General",
    "7.2.2": "Fixtures",
    "7.2.3": "Traps and Interceptors",
    "7.2.4": "Pipe Fittings",
    "7.2.5": "Non-Metallic Pipe and Fittings",
    "7.2.6": "Ferrous Pipe and Fittings",
    "7.2.7": "Non-Ferrous Pipe and Fittings",
    "7.2.8": "Corrosion Resistant Materials",
    "7.2.9": "Jointing Materials",
    "7.2.10": "Miscellaneous Materials",
    "7.2.11": "Water Service Pipes and Fire Service Mains",
    "7.3.1": "Application",
    "7.3.2": "Construction and Use of Joints",
    "7.3.3": "Joints and Connections",
    "7.3.4": "Support of Piping",
    "7.3.5": "Protection of Piping",
    "7.3.6": "Testing of Drainage and Venting Systems",
    "7.3.7": "Testing of Potable Water Systems",
    "7.4.1": "Application",
    "7.4.2": "Connections to Drainage Systems",
    "7.4.3": "Location of Fixtures",
    "7.4.4": "Treatment of Sewage and Wastes",
    "7.4.5": "Traps",
    "7.4.6": "Arrangement of Drainage Piping",
    "7.4.7": "Cleanouts",
    "7.4.8": "Minimum Slope and Length of Drainage Pipes",
    "7.4.9": "Size of Drainage Pipes",
    "7.4.10": "Hydraulic Loads",
    "7.5.1": "Vent Pipes for Traps",
    "7.5.2": "Wet Venting",
    "7.5.3": "Circuit Venting",
    "7.5.4": "Vent Pipes for Stacks",
    "7.5.5": "Miscellaneous Vent Pipes",
    "7.5.6": "Arrangement of Vent Pipes",
    "7.5.7": "Minimum Size of Vent Pipes",
    "7.5.8": "Sizing of Vent Pipes",
    "7.5.9": "Air Admittance Valves",
    "7.6.1": "Arrangement of Piping",
    "7.6.2": "Protection from Contamination",
    "7.6.3": "Size and Capacity of Pipes",
    "7.6.4": "Water Efficiency",
    "7.7.1": "Non-Potable Water Systems",
    "7.7.2": "Non-Potable Rainwater Harvesting Systems",
    "7.7.3": "Non-Potable Water Systems for Re-Use Purposes",
    "7.7.4": "Water Quality"
}


def convert_superscript(text: str) -> str:
    """<sup> 태그를 유니코드 위첨자로 변환"""
    # 숫자 위첨자 매핑
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
    # <sup> 태그를 유니코드 위첨자로 변환
    text = convert_superscript(text)
    # r1, r2 revision marker 제거 (2024 Building Code 개정 표시)
    # 패턴: **r1**, **r2**, r1, r2 (문장 끝이나 단독)
    text = re.sub(r'\s*\*{0,2}r[12]\*{0,2}(?=\s|$|\.|\))', '', text)
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
    # 목표: 모든 테이블 헤딩을 #### Table X.X.X.X. Title 형태로 통일
    # 입력 형태들:
    #   - ### **Table 7.x.x.x. Title** Forming Part of...
    #   - **Table 7.x.x.x. Title** Forming Part of...
    #   - Table 7.x.x.x.\n\nTitle\nForming Part of...

    # Pattern 1: ### **Table X.X.X.X. Title** Forming Part of...
    # Bold로 감싸진 테이블 제목 (마크다운 헤딩 포함 가능)
    pattern1 = r'^#{0,4}\s*\*{2}(Table 7\.\d+\.\d+\.\d+\.?(?:-[A-Z])?[^*]*)\*{2}\s*(.*)$'

    def replace1(m):
        table_part = m.group(1).strip()
        rest = m.group(2).strip()
        # Bold 내부의 불필요한 공백 정리
        table_part = re.sub(r'\s+', ' ', table_part)
        if rest:
            return f'#### {table_part} {rest}'
        return f'#### {table_part}'

    content = re.sub(pattern1, replace1, content, flags=re.MULTILINE)

    # Pattern 2: ### Table X.X.X.X. Title (Bold 없는 마크다운 헤딩)
    pattern2 = r'^#{1,4}\s*(Table 7\.\d+\.\d+\.\d+\.?(?:-[A-Z])?)\s*(.*)$'

    def replace2(m):
        table_id = m.group(1).strip()
        rest = m.group(2).strip()
        if rest:
            return f'#### {table_id} {rest}'
        return f'#### {table_id}'

    content = re.sub(pattern2, replace2, content, flags=re.MULTILINE)

    # Pattern 3: 줄바꿈으로 분리된 테이블 헤딩 (Table X.X.X.X.\n\nTitle\nForming Part of...)
    pattern3 = r'^(Table 7\.\d+\.\d+\.\d+\.?(?:-[A-Z])?)\s*\n\n(.+?)\n(Forming Part of.+)$'
    content = re.sub(pattern3, r'#### \1 \2 \3', content, flags=re.MULTILINE)

    return content


def convert_notes_headings(content: str) -> str:
    """Notes to Table 헤딩 변환

    Marker 형식:
        #### Notes to Table 7.2.5.15.:
        Notes to Table 7.2.5.15.:

    목표 형식:
        <h5 class="table-notes-title">Notes to Table 7.2.5.15.:</h5>
    """
    # Pattern 1: ### Notes to Table... 또는 #### Notes to Table...
    pattern1 = r'^#{1,5}\s*\*{0,2}(Notes to Table[^:*\n]+):?\*{0,2}\s*$'
    content = re.sub(pattern1, r'\n<h5 class="table-notes-title">\1:</h5>', content, flags=re.MULTILINE)

    # Pattern 2: 마크다운 헤딩 없이 "Notes to Table X.X.X.X.:" 로 시작
    pattern2 = r'^(Notes to Table\s+\d+\.\d+\.\d+\.\d*\.?(?:-[A-Z])?):?\s*$'
    content = re.sub(pattern2, r'<h5 class="table-notes-title">\1:</h5>', content, flags=re.MULTILINE)

    return content


def add_dash_to_notes_items(content: str) -> str:
    """Notes 섹션 내의 (1), (2) 항목에 대시 추가

    CLAUDE.md 규칙: "Notes 항목 = `- (1)` 형식 (대시 필수!)"

    Marker 출력 (Part 7):
        <h5 class="table-notes-title">Notes to Table 7.2.5.15.:</h5>
        (1) P = permitted...

    목표 형식:
        <h5 class="table-notes-title">Notes to Table 7.2.5.15.:</h5>
        - (1) P = permitted...
    """
    # Notes 헤더 이후 ~ 다음 컨텐츠 시작 전까지의 (숫자) 항목에 대시 추가
    def process_notes_section(m):
        notes_header = m.group(1)
        notes_content = m.group(2)
        # (1), (2), ... 패턴에 대시 추가 (이미 대시가 없는 경우만)
        # ^ 시작에서 공백이 있을 수 있으니 ^\s* 로 변경
        notes_content = re.sub(r'^(\s*)(?!- )\((\d+)\)', r'\1- (\2)', notes_content, flags=re.MULTILINE)
        return notes_header + notes_content

    # Notes 섹션 패턴 확장:
    # - [ARTICLE: 다음 Article 마커
    # - #### Table 다음 테이블 헤딩
    # - \n\n\( Article의 clause 시작 (본문 (1), (2)...)
    # - \Z 문자열 끝
    pattern = r'(<h5 class="table-notes-title">Notes to Table[^<]+</h5>\s*\n)(.*?)(?=\[ARTICLE:|#### Table|$)'
    content = re.sub(pattern, process_notes_section, content, flags=re.DOTALL)

    return content


def convert_article_markers(content: str) -> str:
    """Article 헤딩을 [ARTICLE:ID:Title] 마커로 변환"""
    # ### 7.1.1.1. Scope -> [ARTICLE:7.1.1.1:Scope]
    # 7.X.X.X 또는 7.X.XA.X (Alternative subsection의 article)
    # 7.X.X.XA, 7.X.X.XB, 7.X.X.XC (Article suffix - e.g., 7.2.10.7A)
    pattern = r'^#{1,4}\s*(7\.\d+\.\d+[A-Z]?\.\d+[A-Z]?)\.\s*(.+)$'

    def replace(m):
        article_id = m.group(1)
        title = m.group(2).strip()
        # Bold 제거
        title = re.sub(r'\*{1,2}', '', title)
        # (See Note...) 제거
        title = re.sub(r'\s*\(See Note[^)]+\)', '', title)
        # **e2** 같은 마커 제거
        title = re.sub(r'\s*\*{0,2}[er]\d+\*{0,2}$', '', title)
        return f'\n[ARTICLE:{article_id}:{title.strip()}]'

    return re.sub(pattern, replace, content, flags=re.MULTILINE)


def process_clauses(content: str) -> str:
    """Clause 형식 정리

    Marker 출력 형식:
    - **(1)** Main clause...
      - **(2)** Indented clause (2 spaces + dash)
      - (a) sub-clause

    목표 형식:
    (1) Main clause...
    (2) Indented clause
    (a) sub-clause

    주의: Notes to Table 섹션 내의 - (1)은 대시 유지!
    CLAUDE.md: "Notes 항목 = `- (1)` 형식 (대시 필수!)"
    """
    # Notes 섹션을 임시 마커로 보호
    notes_pattern = r'(<h5 class="table-notes-title">Notes to Table[^<]+</h5>.*?)(?=\[ARTICLE:|#### Table|\Z)'

    def protect_notes(m):
        notes_section = m.group(1)
        # Notes 내의 대시+숫자 형식을 임시 마커로 변환
        notes_section = re.sub(r'^- \((\d+)\)', r'__NOTES_ITEM__(\1)', notes_section, flags=re.MULTILINE)
        return notes_section

    content = re.sub(notes_pattern, protect_notes, content, flags=re.DOTALL)

    # 일반 clause에서 대시 제거
    # 주의: 소수점 clause를 먼저 처리해야 함! (1.1)을 (1)보다 먼저 매칭해야 함
    # ^\s*- (0.1), (1.1), (2.1) 등 소수점 clause (OBC 2024에서 사용)
    content = re.sub(r'^\s*-\s*\*{0,2}\((\d+\.\d+)\)\*{0,2}', r'(\1)', content, flags=re.MULTILINE)
    # ^\s*- (1), (2)... 정수 clause
    content = re.sub(r'^\s*-\s*\*{0,2}\((\d+)\)\*{0,2}', r'(\1)', content, flags=re.MULTILINE)
    # ^\s*- (a), (b), ... 처리
    content = re.sub(r'^\s*-\s*\(([a-z])\)', r'(\1)', content, flags=re.MULTILINE)
    # ^\s*- (i), (ii), ... 처리
    content = re.sub(r'^\s*-\s*\(([ivx]+)\)', r'(\1)', content, flags=re.MULTILINE)
    # 인라인 **(1)** -> (1)
    content = re.sub(r'\*{2}\((\d+)\)\*{2}', r'(\1)', content)

    # "- (See Note..." 대시 제거 (clause가 아님)
    content = re.sub(r'^- \(See Note', r'(See Note', content, flags=re.MULTILINE)

    # "- . (See Note..." 잘못된 파싱 수정 (Marker 오류)
    content = re.sub(r'^- \. \(See Note', r'(See Note', content, flags=re.MULTILINE)

    # Notes 마커 복원 (대시 포함)
    content = re.sub(r'__NOTES_ITEM__\((\d+)\)', r'- (\1)', content)

    return content


def convert_where_block_format(content: str) -> str:
    """수식의 where 블록을 Part 8 형식으로 변환

    Part 7 (Marker 출력):
        $Q = ...$
        where:
        Q is the flow rate...
        N is the number of fixtures...

    Part 8 (목표 형식 - add-part.md 참조):
        $A = QT/850$

        where,

        - A = the area of contact in square metres...
        - Q = the total daily design flow in litres, and
    """
    # 1. "where:" → "where,"
    content = re.sub(r'^where\s*:\s*$', 'where,', content, flags=re.MULTILINE)

    # 2. "where," 블록 이후의 변수 정의를 찾아서 변환
    # 패턴: 줄 시작에서 단일 문자/짧은 변수명 + "is" or "=" + 설명
    # 예: "Q is the flow rate..." → "- Q = the flow rate..."
    # 예: "Ss is the specified..." → "- Ss = the specified..."

    def convert_variable_definitions(m):
        """where, 블록 내의 변수 정의 변환"""
        where_marker = m.group(1)  # "where,"
        definitions_block = m.group(2)

        # 각 줄을 처리
        lines = definitions_block.split('\n')
        converted_lines = []

        for line in lines:
            stripped = line.strip()

            # 이미 "- " 로 시작하면 스킵
            if stripped.startswith('- '):
                converted_lines.append(line)
                continue

            # 빈 줄은 유지
            if not stripped:
                converted_lines.append(line)
                continue

            # 변수 정의 패턴: "X is the..." 또는 "X = the..."
            # 변수명: 1-3 글자의 알파벳/그리스문자 (Q, Ss, PD, γ 등)
            var_match = re.match(r'^([A-Za-zγ]{1,3})\s+(?:is|=)\s+(.+)$', stripped)
            if var_match:
                var_name = var_match.group(1)
                description = var_match.group(2)
                converted_lines.append(f'- {var_name} = {description}')
            else:
                # 매칭 안 되면 원본 유지
                converted_lines.append(line)

        return where_marker + '\n' + '\n'.join(converted_lines)

    # where, 이후 다음 빈 줄 2개 또는 clause/Article까지의 블록 처리
    # 종료 조건: 빈 줄 2개 연속, (1), (a), [ARTICLE:, #### Table
    where_pattern = r'(where,)\n((?:(?!\n\n\n|\(\d+\)|\([a-z]\)|\[ARTICLE:|\#{4} Table).)*)'
    content = re.sub(where_pattern, convert_variable_definitions, content, flags=re.DOTALL)

    return content


def remove_bold_italic(content: str) -> str:
    """Bold/Italic 마크다운 제거"""
    # **bold** -> bold
    content = re.sub(r'\*{2}([^*]+)\*{2}', r'\1', content)
    # *italic* -> italic (단, *(1)* 같은 clause는 유지)
    content = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'\1', content)
    return content


def extract_part7(full_content: str) -> str:
    """전체 Marker 출력에서 Part 7만 추출"""
    # Part 7 시작: "# Part 7" 또는 "# Section 7.1"
    start_match = re.search(r'^# Part 7\s*$', full_content, re.MULTILINE)
    if not start_match:
        start_match = re.search(r'^# Section 7\.1\.', full_content, re.MULTILINE)
    if not start_match:
        raise ValueError("Part 7 not found in Marker output")

    # Part 8 시작 전까지
    end_match = re.search(r'^# Part 8\s*$', full_content[start_match.end():], re.MULTILINE)
    if end_match:
        return full_content[start_match.start():start_match.end() + end_match.start()]
    else:
        return full_content[start_match.start():]


def parse_marker_file():
    """Marker 파일 파싱"""

    with open(MARKER_PATH, 'r', encoding='utf-8') as f:
        full_content = f.read()

    # Part 7만 추출
    content = extract_part7(full_content)

    # 목차 부분 제거 (첫 번째 "# Section 7.1." 시작 전까지)
    section_start = re.search(r'^# Section 7\.1\.', content, re.MULTILINE)
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

        # Section 헤딩 감지: # Section 7.1. General
        section_match = re.match(r'^#{1,4}\s*Section\s*(7\.\d+)\.\s*(.*)$', line)

        # Subsection 헤딩 감지: # 7.1.1. Application 또는 # 7.1.1A. Definitions
        # Article (7.x.x.x)이 매칭되지 않도록 (?!\d) 사용
        subsection_match = re.match(r'^#{1,4}\s*(7\.\d+\.\d+[A-Z]?)\.(?!\d)\s*(.*)$', line)

        if section_match:
            section_id = section_match.group(1)
            section_title = section_match.group(2).strip()

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

            # Bold/마커 제거
            subsection_title = re.sub(r'\*{1,2}', '', subsection_title)
            subsection_title = re.sub(r'\s*[er]\d+$', '', subsection_title)

            # 이전 Subsection 저장
            if current_subsection and current_section:
                current_section['subsections'].append(current_subsection)

            # Section이 없으면 생성
            if not current_section:
                section_id = '.'.join(subsection_id.split('.')[:2])
                # Alternative subsection인 경우 (7.1.1A -> 7.1)
                section_id = re.match(r'(7\.\d+)', subsection_id).group(1)
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
            content = add_dash_to_notes_items(content)  # Notes 항목에 대시 추가
            content = convert_where_block_format(content)  # 수식 where 블록 변환
            content = remove_bold_italic(content)
            content = clean_text(content)

            subsection['content'] = content

    return {
        'id': '7',
        'title': 'Plumbing',
        'sections': sections
    }


def main():
    print("=== Marker -> Part 7 JSON 변환 ===\n")

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
            total_tables += len(re.findall(r'#### Table 7\.', content))

    print(f"Sections: {len(data['sections'])}")
    print(f"Subsections: {total_subsections}")
    print(f"Articles: {total_articles}")
    print(f"Tables: {total_tables}")

    # 저장
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n저장됨: {OUTPUT_PATH}")

    # 샘플 출력
    print("\n=== 샘플 (7.1.1 처음 1000자) ===")
    for section in data['sections']:
        for subsection in section['subsections']:
            if subsection['id'] == '7.1.1':
                print(subsection['content'][:1000])
                break


if __name__ == "__main__":
    main()
