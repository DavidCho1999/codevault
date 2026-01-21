#!/usr/bin/env python3
"""
Smart Table Converter
- colspan 자동 감지 (null 패턴)
- rowspan 자동 감지 (반복 값)
- 다중 헤더 행 처리
"""

import json
from pathlib import Path
from html import escape
from typing import List, Optional, Tuple

BASE_DIR = Path(__file__).parent.parent / "codevault" / "public" / "data"


def detect_header_rows(data: List[List]) -> int:
    """
    헤더 행 수 감지
    - 데이터 행은 보통 숫자가 많음
    - 헤더 행은 텍스트가 많음
    """
    if len(data) <= 1:
        return 1

    def is_data_row(row):
        """숫자가 50% 이상이면 데이터 행"""
        numeric_count = 0
        total = 0
        for cell in row:
            if cell is not None and str(cell).strip():
                total += 1
                # 숫자 또는 숫자+단위 패턴
                cell_str = str(cell).strip()
                if cell_str.replace('.', '').replace(',', '').replace(' ', '').isdigit():
                    numeric_count += 1
                elif cell_str in ['1', '2', '—', '-', 'N/A']:
                    numeric_count += 1
        return total > 0 and (numeric_count / total) > 0.4

    header_count = 0
    for i, row in enumerate(data):
        if is_data_row(row):
            return max(1, i)
        header_count += 1
        if header_count >= 5:  # 최대 5개 헤더 행
            break

    return max(1, min(header_count, len(data) - 1))


def calculate_colspans(row: List) -> List[Tuple[str, int]]:
    """
    null 패턴으로 colspan 계산
    ["A", null, null, "B", null] -> [("A", 3), ("B", 2)]
    """
    result = []
    i = 0
    while i < len(row):
        cell = row[i]
        colspan = 1

        # 현재 셀 이후 연속된 null 개수 세기
        j = i + 1
        while j < len(row) and row[j] is None:
            colspan += 1
            j += 1

        cell_text = escape(str(cell)) if cell else ''
        result.append((cell_text, colspan))
        i = j

    return result


def calculate_rowspans(data: List[List], col_idx: int, start_row: int, end_row: int) -> List[int]:
    """
    특정 열에서 rowspan 계산
    반환: 각 행의 rowspan 값 (0이면 이전 셀의 rowspan에 포함됨)
    """
    rowspans = []

    i = start_row
    while i <= end_row:
        cell = data[i][col_idx] if col_idx < len(data[i]) else None
        cell_str = str(cell).strip() if cell else ''

        # 연속된 동일 값 찾기
        span = 1
        j = i + 1
        while j <= end_row:
            next_cell = data[j][col_idx] if col_idx < len(data[j]) else None
            next_str = str(next_cell).strip() if next_cell else ''

            if cell_str and cell_str == next_str:
                span += 1
                j += 1
            else:
                break

        rowspans.append(span)
        for _ in range(span - 1):
            rowspans.append(0)  # 0 = 이 셀은 렌더링하지 않음

        i += span

    return rowspans


def smart_convert_to_html(table_data: dict) -> str:
    """스마트 HTML 변환 (colspan/rowspan 자동 감지)"""
    table_id = table_data.get('table_id', '')
    data = table_data.get('data', [])

    if not data:
        return f'<p class="text-red-500">No data for Table {table_id}</p>'

    # 헤더 행 수 감지
    header_rows = detect_header_rows(data)

    # rowspan 계산 (첫 번째 열만 - 보통 row header)
    first_col_rowspans = calculate_rowspans(data, 0, header_rows, len(data) - 1)

    # 헤더 영역에서 첫 번째 열 rowspan 계산
    header_col0_rowspans = calculate_rowspans(data, 0, 0, header_rows - 1) if header_rows > 1 else [1]

    html_parts = []
    html_parts.append(f'<table class="obc-table" data-table-id="Table {table_id}">')

    # THEAD - rowspan/colspan 모두 처리
    html_parts.append('<thead>')
    header_row_idx = 0
    for row_idx in range(header_rows):
        row = data[row_idx]
        html_parts.append('<tr>')

        # 첫 번째 열 처리 (rowspan)
        first_col_rowspan = header_col0_rowspans[header_row_idx] if header_row_idx < len(header_col0_rowspans) else 1
        if first_col_rowspan > 0:
            cell_text = escape(str(row[0])) if row[0] else ''
            # 특수 문자 정리
            cell_text = cell_text.replace('\uf0b3', '>=').replace('\uf0b2', '<=')
            attrs = f' rowspan="{first_col_rowspan}"' if first_col_rowspan > 1 else ''
            html_parts.append(f'<th{attrs}>{cell_text}</th>')

        # 나머지 열 처리 (colspan)
        cells_with_colspan = calculate_colspans(row[1:])
        for cell_text, colspan in cells_with_colspan:
            cell_text = cell_text.replace('\uf0b3', '>=').replace('\uf0b2', '<=')
            attrs = f' colspan="{colspan}"' if colspan > 1 else ''
            html_parts.append(f'<th{attrs}>{cell_text}</th>')

        html_parts.append('</tr>')
        header_row_idx += 1
    html_parts.append('</thead>')

    # TBODY
    if len(data) > header_rows:
        html_parts.append('<tbody>')
        data_row_idx = 0

        for row_idx in range(header_rows, len(data)):
            row = data[row_idx]
            bg_class = 'bg-gray-50' if (row_idx - header_rows) % 2 == 1 else 'bg-white'
            html_parts.append(f'<tr class="{bg_class}">')

            for col_idx, cell in enumerate(row):
                cell_text = escape(str(cell)) if cell else ''
                cell_text = cell_text.replace('\uf0b3', '>=').replace('\uf0b2', '<=')

                if col_idx == 0:
                    # 첫 번째 열 - rowspan 적용
                    rowspan = first_col_rowspans[data_row_idx] if data_row_idx < len(first_col_rowspans) else 1
                    if rowspan == 0:
                        continue  # 이전 셀의 rowspan에 포함됨
                    attrs = f' rowspan="{rowspan}"' if rowspan > 1 else ''
                    html_parts.append(f'<th{attrs}>{cell_text}</th>')
                else:
                    html_parts.append(f'<td>{cell_text}</td>')

            html_parts.append('</tr>')
            data_row_idx += 1

        html_parts.append('</tbody>')

    html_parts.append('</table>')

    return '\n'.join(html_parts)


def convert_and_update_table(table_id: str):
    """특정 테이블을 스마트 변환하여 업데이트"""
    tables_path = BASE_DIR / "part9_tables.json"
    v9_fixed_path = BASE_DIR / "part9_tables_v9_fixed.json"

    # 로드
    with open(tables_path, 'r', encoding='utf-8') as f:
        tables = json.load(f)

    with open(v9_fixed_path, 'r', encoding='utf-8') as f:
        v9_fixed = json.load(f)

    # 테이블 찾기
    v9_map = {t['table_id']: t for t in v9_fixed}

    if table_id not in v9_map:
        print(f"[X] Table {table_id} not found in v9_fixed")
        return False

    table_data = v9_map[table_id]

    # 스마트 변환
    html = smart_convert_to_html(table_data)

    # 업데이트
    key = f"Table {table_id}"
    tables[key] = {
        "title": key,
        "page": table_data.get('page', 0),
        "rows": table_data.get('rows', len(table_data.get('data', []))),
        "cols": table_data.get('cols', 0),
        "html": html
    }

    # 저장
    with open(tables_path, 'w', encoding='utf-8') as f:
        json.dump(tables, f, ensure_ascii=False, indent=2)

    print(f"[OK] Table {table_id} updated with smart conversion")
    return True


def preview_table(table_id: str):
    """테이블 변환 결과 미리보기"""
    v9_fixed_path = BASE_DIR / "part9_tables_v9_fixed.json"

    with open(v9_fixed_path, 'r', encoding='utf-8') as f:
        v9_fixed = json.load(f)

    v9_map = {t['table_id']: t for t in v9_fixed}

    if table_id not in v9_map:
        print(f"[X] Table {table_id} not found")
        return

    table_data = v9_map[table_id]

    print("=" * 60)
    print(f"TABLE {table_id} PREVIEW")
    print("=" * 60)

    print("\n[RAW DATA]")
    for i, row in enumerate(table_data.get('data', [])):
        # Clean special chars for display
        clean_row = [str(c).replace('\uf0b3', '>=').replace('\uf0b2', '<=') if c else None for c in row]
        print(f"Row {i}: {clean_row}")

    header_rows = detect_header_rows(table_data.get('data', []))
    print(f"\n[DETECTED HEADER ROWS]: {header_rows}")

    print("\n[GENERATED HTML]")
    html = smart_convert_to_html(table_data)
    # Safe print for Windows
    safe_html = html.replace('\uf0b3', '>=').replace('\uf0b2', '<=')
    print(safe_html)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python table_smart_convert.py preview 9.8.7.1")
        print("  python table_smart_convert.py update 9.8.7.1")
        print("  python table_smart_convert.py update_all")
        sys.exit(1)

    command = sys.argv[1]

    if command == "preview" and len(sys.argv) > 2:
        preview_table(sys.argv[2])

    elif command == "update" and len(sys.argv) > 2:
        convert_and_update_table(sys.argv[2])

    elif command == "update_all":
        # 최근 추가된 테이블들 재변환
        tables_to_update = ["9.8.7.1", "9.23.3.5", "9.27.5.4"]
        for tid in tables_to_update:
            convert_and_update_table(tid)

    else:
        print("Unknown command")
