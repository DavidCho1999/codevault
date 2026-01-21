#!/usr/bin/env python3
"""
Table Gap Analysis Script
- part9.json에서 참조된 테이블 ID 추출
- part9_tables.json에 있는지 확인
- 누락 목록 출력
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent / "codevault" / "public" / "data"

def extract_table_references(part9_json_path):
    """part9.json에서 참조된 모든 테이블 ID 추출"""
    with open(part9_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    table_refs = set()
    pattern = r'Table\s+(9\.\d+(?:\.\d+)*(?:\.-[A-Z])?)'

    def search_content(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                search_content(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search_content(item, f"{path}[{i}]")
        elif isinstance(obj, str):
            matches = re.findall(pattern, obj)
            for m in matches:
                table_refs.add(m)

    search_content(data)
    return sorted(table_refs, key=lambda x: [int(n) if n.isdigit() else n for n in re.split(r'[.\-]', x)])

def get_existing_tables(tables_json_path):
    """part9_tables.json에 있는 테이블 ID 추출"""
    with open(tables_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    existing = set()
    for key in data.keys():
        # "Table 9.3.1.7" -> "9.3.1.7"
        match = re.match(r'Table\s+([\d.]+(?:-[A-Z])?)', key)
        if match:
            existing.add(match.group(1))
    return existing

def get_v9_fixed_tables(v9_fixed_path):
    """part9_tables_v9_fixed.json에 있는 테이블 ID 추출"""
    with open(v9_fixed_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tables = {}
    for item in data:
        table_id = item.get('table_id')
        if table_id:
            tables[table_id] = item
    return tables

def main():
    part9_path = BASE_DIR / "part9.json"
    tables_path = BASE_DIR / "part9_tables.json"
    v9_fixed_path = BASE_DIR / "part9_tables_v9_fixed.json"

    print("=" * 60)
    print("TABLE GAP ANALYSIS")
    print("=" * 60)

    # 1. 참조된 테이블 추출
    referenced = extract_table_references(part9_path)
    print(f"\n[1] part9.json에서 참조된 테이블: {len(referenced)}개")

    # 2. 현재 테이블 파일에 있는 것들
    existing = get_existing_tables(tables_path)
    print(f"[2] part9_tables.json에 있는 테이블: {len(existing)}개")

    # 3. v9_fixed에 있는 것들
    v9_fixed = get_v9_fixed_tables(v9_fixed_path)
    print(f"[3] part9_tables_v9_fixed.json에 있는 테이블: {len(v9_fixed)}개")

    # 4. 갭 분석
    missing = set(referenced) - existing
    print(f"\n[4] 누락된 테이블: {len(missing)}개")

    if missing:
        print("\n" + "-" * 40)
        print("MISSING TABLES:")
        print("-" * 40)

        can_add = []
        cannot_add = []

        for table_id in sorted(missing, key=lambda x: [int(n) if n.isdigit() else n for n in re.split(r'[.\-]', x)]):
            if table_id in v9_fixed:
                can_add.append(table_id)
                status = "[OK] v9_fixed available"
            else:
                cannot_add.append(table_id)
                status = "[X] not in v9_fixed"
            print(f"  Table {table_id}: {status}")

        print("\n" + "-" * 40)
        print(f"SUMMARY:")
        print(f"  - Auto-add possible: {len(can_add)}")
        print(f"  - Manual work needed: {len(cannot_add)}")
        print("-" * 40)

        # 자동 추가 가능한 목록 저장
        if can_add:
            output_path = BASE_DIR / "missing_tables_to_add.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(can_add, f, indent=2)
            print(f"\nSaved to: {output_path}")
    else:
        print("\n[OK] All referenced tables exist!")

    return missing

if __name__ == "__main__":
    main()
