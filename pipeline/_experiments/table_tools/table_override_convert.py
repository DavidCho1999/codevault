#!/usr/bin/env python3
"""
Table Override Converter
- manual_table_overrides.json의 정확한 데이터 사용
- rowspan/colspan 명시적 지정
- part9_tables.json 업데이트
"""

import json
from pathlib import Path
from html import escape
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent / "codevault" / "public" / "data"


def convert_override_to_html(table_id: str, override_data: dict) -> str:
    """수동 오버라이드 데이터를 HTML로 변환 (명시적 rowspan/colspan 사용)"""
    data = override_data.get('data', [])
    header_rows = override_data.get('header_rows', 1)
    spans = override_data.get('spans', {})

    if not data:
        return f'<p class="text-red-500">No data for Table {table_id}</p>'

    # rowspan/colspan 매핑 생성
    rowspan_map = {}  # {(row, col): span}
    colspan_map = {}  # {(row, col): span}

    for rs in spans.get('rowspans', []):
        rowspan_map[(rs['row'], rs['col'])] = rs['span']

    for cs in spans.get('colspans', []):
        colspan_map[(cs['row'], cs['col'])] = cs['span']

    # 어떤 셀이 rowspan에 의해 숨겨지는지 계산
    hidden_cells = set()
    for (row, col), span in rowspan_map.items():
        for r in range(row + 1, row + span):
            hidden_cells.add((r, col))

    # 어떤 셀이 colspan에 의해 숨겨지는지 계산
    for (row, col), span in colspan_map.items():
        for c in range(col + 1, col + span):
            hidden_cells.add((row, c))

    html_parts = []
    html_parts.append(f'<table class="obc-table" data-table-id="Table {table_id}">')

    # Caption (테이블 제목) - PDF 원본처럼 표시
    caption_html = override_data.get('caption_html', '')
    if caption_html:
        html_parts.append(f'<caption class="text-center mb-2">{caption_html}</caption>')

    # THEAD
    html_parts.append('<thead>')
    for row_idx in range(header_rows):
        row = data[row_idx]
        html_parts.append('<tr>')

        for col_idx, cell in enumerate(row):
            # 숨겨진 셀이면 건너뜀
            if (row_idx, col_idx) in hidden_cells:
                continue

            # null이고 숨겨진 셀이 아니면 건너뜀 (이미 병합됨)
            if cell is None:
                continue

            cell_text = escape(str(cell)) if cell else ''
            # 복원: 특정 HTML 태그 (<i>, </i>)는 이스케이프하지 않음
            cell_text = cell_text.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')

            # 속성 생성
            attrs = []
            if (row_idx, col_idx) in rowspan_map:
                attrs.append(f'rowspan="{rowspan_map[(row_idx, col_idx)]}"')
            if (row_idx, col_idx) in colspan_map:
                attrs.append(f'colspan="{colspan_map[(row_idx, col_idx)]}"')

            attr_str = ' ' + ' '.join(attrs) if attrs else ''
            html_parts.append(f'<th{attr_str}>{cell_text}</th>')

        html_parts.append('</tr>')
    html_parts.append('</thead>')

    # TBODY
    if len(data) > header_rows:
        html_parts.append('<tbody>')
        for row_idx in range(header_rows, len(data)):
            row = data[row_idx]
            bg_class = 'bg-gray-50' if (row_idx - header_rows) % 2 == 1 else 'bg-white'
            html_parts.append(f'<tr class="{bg_class}">')

            for col_idx, cell in enumerate(row):
                if (row_idx, col_idx) in hidden_cells:
                    continue
                if cell is None:
                    continue

                cell_text = escape(str(cell)) if cell else ''
                # 복원: 특정 HTML 태그 (<i>, </i>)는 이스케이프하지 않음
                cell_text = cell_text.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')

                # 속성 생성 (rowspan/colspan 포함)
                attrs = ['style="text-align: center;"']
                if (row_idx, col_idx) in rowspan_map:
                    attrs.append(f'rowspan="{rowspan_map[(row_idx, col_idx)]}"')
                if (row_idx, col_idx) in colspan_map:
                    attrs.append(f'colspan="{colspan_map[(row_idx, col_idx)]}"')
                attr_str = ' '.join(attrs)

                # 첫 번째 열은 th (row header)
                if col_idx == 0:
                    html_parts.append(f'<th {attr_str}>{cell_text}</th>')
                else:
                    html_parts.append(f'<td {attr_str}>{cell_text}</td>')

            html_parts.append('</tr>')
        html_parts.append('</tbody>')

    html_parts.append('</table>')

    # Notes 추가 (있는 경우)
    notes_html = override_data.get('notes_html', '')
    if notes_html:
        html_parts.append(notes_html)

    return '\n'.join(html_parts)


def apply_html_override(table_id: str, override_data: dict, existing_html: str) -> str:
    """html_override=true인 경우: 기존 HTML에 caption, notes, 텍스트 수정 적용"""
    html = existing_html

    # 1. 텍스트 수정 적용 (header_fix, italic_fix, data_fix)
    for fix_key in ['header_fix', 'italic_fix', 'data_fix']:
        fixes = override_data.get(fix_key, {})
        for old_text, new_text in fixes.items():
            html = html.replace(old_text, new_text)

    # 2. Caption 추가 (테이블 시작 직후)
    caption_html = override_data.get('caption_html', '')
    if caption_html:
        import re
        # 먼저 기존 caption을 모두 제거
        html = re.sub(r'<caption[^>]*>.*?</caption>', '', html, flags=re.DOTALL)

        # <table ...> 태그 찾아서 그 뒤에 새 caption 삽입
        table_tag_match = re.search(r'(<table[^>]*>)', html)
        if table_tag_match:
            table_tag = table_tag_match.group(1)
            caption = f'<caption class="text-center mb-2">{caption_html}</caption>'
            html = html.replace(table_tag, f'{table_tag}\n{caption}', 1)

    # 3. Notes 추가 (테이블 끝에)
    notes_html = override_data.get('notes_html', '')
    if notes_html:
        import re
        # 먼저 기존 notes를 모두 제거
        html = re.sub(r'<div class="table-notes[^>]*>.*?</div>', '', html, flags=re.DOTALL)

        # 새 notes 추가
        html = html + '\n' + notes_html

    return html


def update_table_from_override(table_id: str):
    """manual_table_overrides.json에서 테이블을 가져와 part9_tables.json 업데이트"""
    overrides_path = BASE_DIR / "manual_table_overrides.json"
    tables_path = BASE_DIR / "part9_tables.json"

    # 오버라이드 로드
    if not overrides_path.exists():
        print(f"[X] Override file not found: {overrides_path}")
        return False

    with open(overrides_path, 'r', encoding='utf-8') as f:
        overrides = json.load(f)

    if table_id not in overrides:
        print(f"[X] Table {table_id} not in overrides")
        return False

    # 현재 테이블 로드
    with open(tables_path, 'r', encoding='utf-8') as f:
        tables = json.load(f)

    override_data = overrides[table_id]
    key = f"Table {table_id}"

    # html_override=true인 경우: 기존 HTML 수정
    if override_data.get('html_override', False):
        if key not in tables:
            print(f"[X] Table {table_id} not found in part9_tables.json (required for html_override)")
            return False

        existing_html = tables[key].get('html', '')
        html = apply_html_override(table_id, override_data, existing_html)

        # 기존 정보 유지하면서 html만 업데이트
        tables[key]['html'] = html
        tables[key]['source'] = 'manual_override'
    else:
        # 완전한 데이터 재정의
        html = convert_override_to_html(table_id, override_data)
        tables[key] = {
            "title": override_data.get('title', key),
            "page": override_data.get('page', 0),
            "rows": override_data.get('rows', len(override_data.get('data', []))),
            "cols": override_data.get('cols', 0),
            "html": html,
            "source": "manual_override"
        }

    # 저장
    with open(tables_path, 'w', encoding='utf-8') as f:
        json.dump(tables, f, ensure_ascii=False, indent=2)

    print(f"[OK] Table {table_id} updated from manual override")
    return True


def preview_override(table_id: str):
    """오버라이드 테이블 미리보기"""
    overrides_path = BASE_DIR / "manual_table_overrides.json"

    with open(overrides_path, 'r', encoding='utf-8') as f:
        overrides = json.load(f)

    if table_id not in overrides:
        print(f"[X] Table {table_id} not found in overrides")
        return

    override_data = overrides[table_id]

    print("=" * 60)
    print(f"TABLE {table_id} OVERRIDE PREVIEW")
    print("=" * 60)

    print("\n[DATA]")
    for i, row in enumerate(override_data.get('data', [])):
        print(f"Row {i}: {row}")

    print("\n[SPANS]")
    print(f"Rowspans: {override_data.get('spans', {}).get('rowspans', [])}")
    print(f"Colspans: {override_data.get('spans', {}).get('colspans', [])}")

    print("\n[GENERATED HTML]")
    html = convert_override_to_html(table_id, override_data)
    print(html)


def list_overrides():
    """사용 가능한 오버라이드 목록"""
    overrides_path = BASE_DIR / "manual_table_overrides.json"

    if not overrides_path.exists():
        print("[X] No override file found")
        return

    with open(overrides_path, 'r', encoding='utf-8') as f:
        overrides = json.load(f)

    print("=" * 60)
    print("AVAILABLE MANUAL OVERRIDES")
    print("=" * 60)

    for table_id, data in overrides.items():
        title = data.get('title', 'No title')
        print(f"  - {table_id}: {title}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python table_override_convert.py list")
        print("  python table_override_convert.py preview 9.8.7.1")
        print("  python table_override_convert.py update 9.8.7.1")
        print("  python table_override_convert.py update_all")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_overrides()

    elif command == "preview" and len(sys.argv) > 2:
        preview_override(sys.argv[2])

    elif command == "update" and len(sys.argv) > 2:
        update_table_from_override(sys.argv[2])

    elif command == "update_all":
        overrides_path = BASE_DIR / "manual_table_overrides.json"
        if overrides_path.exists():
            with open(overrides_path, 'r', encoding='utf-8') as f:
                overrides = json.load(f)
            for table_id in overrides:
                update_table_from_override(table_id)

    else:
        print("Unknown command")
