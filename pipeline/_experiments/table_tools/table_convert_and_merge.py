#!/usr/bin/env python3
"""
Table Convert and Merge Script
- v9_fixed JSON → HTML 테이블 변환
- part9_tables.json에 병합
"""

import json
import re
from pathlib import Path
from html import escape

BASE_DIR = Path(__file__).parent.parent / "codevault" / "public" / "data"

def convert_to_html(table_data: dict) -> str:
    """v9_fixed 형식의 테이블 데이터를 HTML로 변환"""
    table_id = table_data.get('table_id', '')
    data = table_data.get('data', [])
    title = table_data.get('title', f'Table {table_id}')

    if not data:
        return f'<p class="text-red-500">No data for Table {table_id}</p>'

    html_parts = []
    html_parts.append(f'<table class="obc-table" data-table-id="Table {table_id}">')

    # 첫 번째 행을 헤더로 사용
    if data:
        html_parts.append('<thead>')
        html_parts.append('<tr>')
        for cell in data[0]:
            cell_text = escape(str(cell)) if cell else ''
            html_parts.append(f'<th>{cell_text}</th>')
        html_parts.append('</tr>')
        html_parts.append('</thead>')

    # 나머지 행을 본문으로
    if len(data) > 1:
        html_parts.append('<tbody>')
        for i, row in enumerate(data[1:]):
            bg_class = 'bg-gray-50' if i % 2 == 1 else 'bg-white'
            html_parts.append(f'<tr class="{bg_class}">')
            for j, cell in enumerate(row):
                cell_text = escape(str(cell)) if cell else ''
                # 첫 번째 열은 th로
                if j == 0:
                    html_parts.append(f'<th>{cell_text}</th>')
                else:
                    html_parts.append(f'<td>{cell_text}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody>')

    html_parts.append('</table>')

    return '\n'.join(html_parts)

def merge_tables(target_tables: dict, v9_fixed_tables: list, table_ids_to_add: list) -> dict:
    """지정된 테이블들을 target에 추가"""
    v9_map = {t['table_id']: t for t in v9_fixed_tables}

    added = []
    for table_id in table_ids_to_add:
        if table_id in v9_map:
            table_data = v9_map[table_id]
            html = convert_to_html(table_data)
            key = f"Table {table_id}"

            target_tables[key] = {
                "title": key,
                "page": table_data.get('page', 0),
                "rows": table_data.get('rows', len(table_data.get('data', []))),
                "cols": table_data.get('cols', len(table_data.get('data', [[]])[0]) if table_data.get('data') else 0),
                "html": html
            }
            added.append(table_id)
            print(f"  [OK] Added: Table {table_id}")
        else:
            print(f"  [X] Not found in v9_fixed: {table_id}")

    return target_tables, added

def main(table_ids=None):
    """
    table_ids: 추가할 테이블 ID 목록 (None이면 missing_tables_to_add.json 사용)
    """
    tables_path = BASE_DIR / "part9_tables.json"
    v9_fixed_path = BASE_DIR / "part9_tables_v9_fixed.json"
    missing_path = BASE_DIR / "missing_tables_to_add.json"

    print("=" * 60)
    print("TABLE CONVERT AND MERGE")
    print("=" * 60)

    # 1. 현재 테이블 파일 로드
    with open(tables_path, 'r', encoding='utf-8') as f:
        current_tables = json.load(f)
    print(f"\n[1] 현재 테이블 수: {len(current_tables)}개")

    # 2. v9_fixed 로드
    with open(v9_fixed_path, 'r', encoding='utf-8') as f:
        v9_fixed = json.load(f)
    print(f"[2] v9_fixed 테이블 수: {len(v9_fixed)}개")

    # 3. 추가할 테이블 목록
    if table_ids is None:
        if missing_path.exists():
            with open(missing_path, 'r', encoding='utf-8') as f:
                table_ids = json.load(f)
        else:
            print("\n❌ missing_tables_to_add.json이 없습니다.")
            print("   먼저 table_gap_analysis.py를 실행하세요.")
            return

    print(f"[3] 추가 대상 테이블: {len(table_ids)}개")

    # 4. 변환 및 병합
    print("\n" + "-" * 40)
    print("CONVERTING AND MERGING:")
    print("-" * 40)

    updated_tables, added = merge_tables(current_tables, v9_fixed, table_ids)

    # 5. 저장
    if added:
        # 백업
        backup_path = tables_path.with_suffix('.json.bak')
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(current_tables, f, ensure_ascii=False, indent=2)
        print(f"\n[4] 백업 생성: {backup_path}")

        # 새 파일 저장
        with open(tables_path, 'w', encoding='utf-8') as f:
            json.dump(updated_tables, f, ensure_ascii=False, indent=2)
        print(f"[5] 저장 완료: {tables_path}")

        print("\n" + "-" * 40)
        print(f"RESULT: {len(added)}개 테이블 추가됨")
        print("-" * 40)
    else:
        print("\n추가된 테이블이 없습니다.")

    return added

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # 특정 테이블 ID만 추가
        table_ids = sys.argv[1:]
        main(table_ids)
    else:
        # missing_tables_to_add.json 사용
        main()
