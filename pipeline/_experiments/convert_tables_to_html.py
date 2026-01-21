# -*- coding: utf-8 -*-
"""
마크다운 테이블을 인라인 HTML로 변환하는 범용 스크립트

사용법:
    python scripts_temp/convert_tables_to_html.py <part_number>

예시:
    python scripts_temp/convert_tables_to_html.py 8
"""

import sqlite3
import re
import sys
from pathlib import Path


def convert_markdown_table_to_html(lines: list, start_idx: int) -> tuple:
    """마크다운 테이블을 HTML로 변환

    Returns: (html_string, end_idx)
    """
    table_lines = []
    i = start_idx

    # 테이블 줄 수집
    while i < len(lines) and lines[i].strip().startswith('|'):
        table_lines.append(lines[i].strip())
        i += 1

    if len(table_lines) < 2:
        return None, start_idx

    # 헤더 행 파싱
    header_line = table_lines[0]
    headers = [cell.strip() for cell in header_line.split('|')[1:-1]]

    # 구분선 확인 (|---|---|)
    if len(table_lines) > 1 and re.match(r'^\|[\s\-:|]+\|$', table_lines[1]):
        data_start = 2
    else:
        data_start = 1

    # HTML 생성
    html = ['<table class="obc-table">']

    # 헤더
    html.append('<thead><tr>')
    for h in headers:
        html.append(f'<th>{h}</th>')
    html.append('</tr></thead>')

    # 바디
    html.append('<tbody>')
    for row_line in table_lines[data_start:]:
        cells = [cell.strip() for cell in row_line.split('|')[1:-1]]
        html.append('<tr>')
        for cell in cells:
            html.append(f'<td>{cell}</td>')
        html.append('</tr>')
    html.append('</tbody>')

    html.append('</table>')

    return ''.join(html), i - 1


def convert_content_tables(content: str) -> str:
    """content 내의 모든 마크다운 테이블을 HTML로 변환"""
    if not content or '|' not in content:
        return content

    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 마크다운 테이블 시작 감지
        if line.strip().startswith('|') and '|' in line[1:]:
            html_table, end_idx = convert_markdown_table_to_html(lines, i)
            if html_table:
                result.append('')  # 빈 줄로 분리
                result.append(html_table)
                result.append('')
                i = end_idx + 1
                continue

        result.append(line)
        i += 1

    return '\n'.join(result)


def convert_part_tables(part_num: str, db_path: str = 'obc.db'):
    """특정 Part의 모든 테이블을 HTML로 변환"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 마크다운 테이블이 있는 노드 찾기
    cursor.execute(f'''
        SELECT id, content FROM nodes
        WHERE id LIKE '{part_num}.%'
        AND content LIKE '%|%|%'
        AND content NOT LIKE '%<table%'
    ''')
    rows = cursor.fetchall()

    print(f"Part {part_num}: {len(rows)} nodes with potential markdown tables")

    converted_count = 0
    for node_id, content in rows:
        if not content:
            continue

        # 실제로 마크다운 테이블이 있는지 확인
        if not re.search(r'^\|.+\|$', content, re.MULTILINE):
            continue

        new_content = convert_content_tables(content)

        if new_content != content:
            cursor.execute('UPDATE nodes SET content = ? WHERE id = ?', (new_content, node_id))
            converted_count += 1

            # 변환된 테이블 개수 카운트
            table_count = new_content.count('<table class="obc-table">')
            print(f"  [OK] {node_id}: {table_count} tables converted")

    conn.commit()
    conn.close()

    print(f"\nTotal: {converted_count} nodes updated")
    return converted_count


def verify_conversion(part_num: str, db_path: str = 'obc.db'):
    """변환 결과 검증"""
    print(f"\n=== Part {part_num} 테이블 변환 검증 ===")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # HTML 테이블 있는 노드
    cursor.execute(f'''
        SELECT COUNT(*) FROM nodes
        WHERE id LIKE '{part_num}.%'
        AND content LIKE '%<table class="obc-table">%'
    ''')
    html_count = cursor.fetchone()[0]

    # 아직 마크다운 테이블이 남은 노드
    cursor.execute(f'''
        SELECT id FROM nodes
        WHERE id LIKE '{part_num}.%'
        AND content LIKE '%|%|%'
        AND content NOT LIKE '%<table%'
        AND content REGEXP '^\|.+\|$'
    ''')
    # SQLite doesn't support REGEXP by default, use Python
    cursor.execute(f'''
        SELECT id, content FROM nodes
        WHERE id LIKE '{part_num}.%'
        AND content LIKE '%|%|%'
        AND content NOT LIKE '%<table%'
    ''')
    remaining = []
    for row in cursor.fetchall():
        if re.search(r'^\|.+\|$', row[1] or '', re.MULTILINE):
            remaining.append(row[0])

    conn.close()

    print(f"  HTML 테이블 있는 노드: {html_count}")
    print(f"  마크다운 테이블 남은 노드: {len(remaining)}")

    if remaining:
        print(f"  미변환 노드: {remaining[:5]}...")

    return len(remaining) == 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python convert_tables_to_html.py <part_number>")
        print("Example: python convert_tables_to_html.py 8")
        sys.exit(1)

    part_num = sys.argv[1]
    db_path = Path(__file__).parent.parent / 'obc.db'

    print(f"Converting Part {part_num} tables to HTML...")
    print(f"DB: {db_path}")
    print()

    convert_part_tables(part_num, str(db_path))
    verify_conversion(part_num, str(db_path))
