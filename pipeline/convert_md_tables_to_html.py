#!/usr/bin/env python3
"""
Markdown 파이프 테이블 → HTML <table class="obc-table"> 변환

Part 11 형식으로 통일:
- <table class="obc-table">
- <h4 class="table-title">Table X.X.X.X.-X Title</h4>
- <h5 class="table-notes-title">Notes to Table X:</h5>
"""

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "codevault" / "public" / "data"


def parse_markdown_table(md_table: str) -> dict:
    """
    Markdown 파이프 테이블을 파싱

    Input:
    | Header1 | Header2 |
    |---------|---------|
    | Cell1   | Cell2   |

    Output:
    {'headers': ['Header1', 'Header2'], 'rows': [['Cell1', 'Cell2']]}
    """
    lines = [l.strip() for l in md_table.strip().split('\n') if l.strip()]

    if len(lines) < 2:
        return None

    # 헤더 행 파싱
    header_line = lines[0]
    if not header_line.startswith('|'):
        return None

    headers = [cell.strip() for cell in header_line.split('|')[1:-1]]

    # 구분선 확인 (|---|---|)
    if len(lines) < 2 or not re.match(r'\|[\s\-:]+\|', lines[1]):
        # 구분선 없으면 첫 줄도 데이터로 처리
        separator_idx = -1
    else:
        separator_idx = 1

    # 데이터 행 파싱
    rows = []
    start_idx = separator_idx + 1 if separator_idx >= 0 else 1
    for line in lines[start_idx:]:
        if line.startswith('|'):
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            rows.append(cells)

    return {'headers': headers, 'rows': rows}


def markdown_table_to_html(md_table: str) -> str:
    """Markdown 테이블 → HTML 테이블 변환"""

    parsed = parse_markdown_table(md_table)
    if not parsed:
        return md_table  # 파싱 실패시 원본 반환

    html_parts = ['<table class="obc-table">']

    # thead
    if parsed['headers']:
        html_parts.append('<thead><tr>')
        for header in parsed['headers']:
            # <br> 태그 유지
            html_parts.append(f'<th>{header}</th>')
        html_parts.append('</tr></thead>')

    # tbody
    if parsed['rows']:
        html_parts.append('<tbody>')
        for row in parsed['rows']:
            html_parts.append('<tr>')
            for cell in row:
                html_parts.append(f'<td>{cell}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody>')

    html_parts.append('</table>')

    return ''.join(html_parts)


def find_markdown_tables(content: str) -> list:
    """
    Content에서 Markdown 테이블 블록 찾기

    Returns: [(start, end, table_text), ...]
    """
    tables = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 파이프로 시작하는 줄 찾기
        if line.startswith('|') and '|' in line[1:]:
            start = i
            table_lines = [lines[i]]
            i += 1

            # 연속된 테이블 줄 수집
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith('|') or re.match(r'^\|?[\s\-:]+\|', next_line):
                    table_lines.append(lines[i])
                    i += 1
                else:
                    break

            if len(table_lines) >= 2:  # 최소 2줄 이상이어야 테이블
                tables.append({
                    'start': start,
                    'end': i,
                    'text': '\n'.join(table_lines),
                    'lines': table_lines
                })
        else:
            i += 1

    return tables


def convert_table_heading(content: str) -> str:
    """
    테이블 헤딩을 Part 11 형식으로 변환

    Before: #### Table 8.2.1.3.-A
    After: <h4 class="table-title">Table 8.2.1.3.-A</h4>
    """
    # #### Table X.X.X.X 패턴
    pattern = r'^#{1,4}\s*(Table \d+\.\d+\.\d+\.\d+\.(?:-[A-Z])?(?:\s*\(Cont\'d\))?)\s*(.*)$'

    def replace_heading(match):
        table_id = match.group(1)
        rest = match.group(2).strip()
        if rest:
            return f'<h4 class="table-title">{table_id} {rest}</h4>'
        return f'<h4 class="table-title">{table_id}</h4>'

    return re.sub(pattern, replace_heading, content, flags=re.MULTILINE)


def convert_notes_heading(content: str) -> str:
    """
    Notes to Table 헤딩 변환

    Before: #### Notes to Table 8.2.1.3.-A:
    After: <h5 class="table-notes-title">Notes to Table 8.2.1.3.-A:</h5>
    """
    pattern = r'^#{1,5}\s*\*{0,2}(Notes to Table[^:*\n]+):?\*{0,2}\s*$'

    def replace_notes(match):
        notes_text = match.group(1).strip()
        return f'<h5 class="table-notes-title">{notes_text}:</h5>'

    return re.sub(pattern, replace_notes, content, flags=re.MULTILINE)


def convert_content(content: str, part_num: int) -> tuple:
    """
    Content 내의 모든 Markdown 테이블을 HTML로 변환

    Returns: (converted_content, stats)
    """
    stats = {'tables_converted': 0, 'headings_converted': 0, 'notes_converted': 0}

    # 1. 테이블 헤딩 변환
    original = content
    content = convert_table_heading(content)
    stats['headings_converted'] = len(re.findall(r'<h4 class="table-title">', content))

    # 2. Notes 헤딩 변환
    content = convert_notes_heading(content)
    stats['notes_converted'] = len(re.findall(r'<h5 class="table-notes-title">', content))

    # 3. Markdown 테이블 → HTML 테이블
    tables = find_markdown_tables(content)

    # 역순으로 처리 (인덱스 유지)
    lines = content.split('\n')
    for table in reversed(tables):
        html_table = markdown_table_to_html(table['text'])

        # 테이블 줄 교체
        lines = lines[:table['start']] + [html_table] + lines[table['end']:]
        stats['tables_converted'] += 1

    return '\n'.join(lines), stats


def convert_part_tables(part_num: int, dry_run: bool = False):
    """Part JSON의 모든 테이블 변환"""

    input_path = DATA_DIR / f"part{part_num}.json"
    output_path = DATA_DIR / f"part{part_num}_html_tables.json"

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"=== Part {part_num} 테이블 HTML 변환 ===\n")

    total_stats = {'tables_converted': 0, 'headings_converted': 0, 'notes_converted': 0}

    for section in data.get('sections', []):
        for subsection in section.get('subsections', []):
            content = subsection.get('content', '')

            if content:
                converted, stats = convert_content(content, part_num)

                if stats['tables_converted'] > 0:
                    print(f"[{subsection['id']}] {stats['tables_converted']} tables, "
                          f"{stats['headings_converted']} headings, {stats['notes_converted']} notes")

                    for key in total_stats:
                        total_stats[key] += stats[key]

                subsection['content'] = converted

    print(f"\n=== 총계 ===")
    print(f"Tables: {total_stats['tables_converted']}")
    print(f"Headings: {total_stats['headings_converted']}")
    print(f"Notes: {total_stats['notes_converted']}")

    if dry_run:
        print("\n[DRY RUN] 파일 저장 안 함")
        return data

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n저장됨: {output_path}")
    return data


def preview_conversion(part_num: int, subsection_id: str = None):
    """변환 미리보기"""

    input_path = DATA_DIR / f"part{part_num}.json"

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for section in data.get('sections', []):
        for subsection in section.get('subsections', []):
            if subsection_id and subsection['id'] != subsection_id:
                continue

            content = subsection.get('content', '')
            if '|' in content and '---' in content:
                print(f"\n=== {subsection['id']} 변환 미리보기 ===\n")

                converted, _ = convert_content(content, part_num)

                print("--- BEFORE (첫 500자) ---")
                print(content[:500])
                print("\n--- AFTER (첫 500자) ---")
                print(converted[:500])

                if subsection_id:
                    return


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python convert_md_tables_to_html.py <part_num> [--dry-run]")
        print("  python convert_md_tables_to_html.py <part_num> --preview [subsection_id]")
        sys.exit(1)

    part_num = int(sys.argv[1])

    if "--preview" in sys.argv:
        subsection_id = sys.argv[sys.argv.index("--preview") + 1] if len(sys.argv) > sys.argv.index("--preview") + 1 else None
        preview_conversion(part_num, subsection_id)
    else:
        dry_run = "--dry-run" in sys.argv
        convert_part_tables(part_num, dry_run)
