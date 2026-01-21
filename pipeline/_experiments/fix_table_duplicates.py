"""
테이블 중복 문제 해결
- 연속 페이지의 같은 테이블 병합
- 고유 ID 부여 (table_id + page 또는 suffix)
"""

import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

INPUT_FILE = '../codevault/public/data/part9_tables_v9.json'
OUTPUT_FILE = '../codevault/public/data/part9_tables_v9_fixed.json'


def get_paths():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.normpath(os.path.join(script_dir, INPUT_FILE))
    output_path = os.path.normpath(os.path.join(script_dir, OUTPUT_FILE))
    return input_path, output_path


def merge_multipage_tables(tables):
    """연속 페이지의 같은 테이블 병합"""
    if not tables:
        return []

    # Sort by page
    sorted_tables = sorted(tables, key=lambda t: (t['page'], t['index']))

    merged = []
    current = None

    for table in sorted_tables:
        table_id = table.get('table_id')

        # No ID or new table
        if not table_id:
            if current:
                merged.append(current)
            current = dict(table)
            # Generate unique id for tables without ID
            current['unique_id'] = f"table_p{table['page']}_{table['index']}"
            continue

        # Check if this is a continuation of the previous table
        if (current and
            current.get('table_id') == table_id and
            table['page'] - current['end_page'] <= 1):

            # Merge: append data rows (skip header which might be repeated)
            new_data = table.get('raw_data', [])

            # Skip rows that look like headers (first few rows might be header repeat)
            data_start = 0
            if new_data and current.get('raw_data'):
                # Check if first row matches header
                current_header = current['raw_data'][0] if current['raw_data'] else []
                if new_data[0] == current_header:
                    data_start = 1  # Skip repeated header

            current['raw_data'].extend(new_data[data_start:])
            current['data'].extend(table.get('data', []))
            current['rows'] = len(current['raw_data'])
            current['end_page'] = table['page']
            current['pages'] = list(range(current['start_page'], current['end_page'] + 1))

        else:
            # Save current and start new
            if current:
                merged.append(current)

            current = dict(table)
            current['start_page'] = table['page']
            current['end_page'] = table['page']
            current['pages'] = [table['page']]
            current['unique_id'] = f"{table_id}_p{table['page']}"

    # Don't forget the last one
    if current:
        merged.append(current)

    return merged


def deduplicate_by_unique_id(tables):
    """고유 ID 기준으로 중복 제거"""
    seen = set()
    result = []

    for table in tables:
        uid = table.get('unique_id', f"p{table['page']}_{table['index']}")
        if uid not in seen:
            seen.add(uid)
            result.append(table)

    return result


def fix_tables():
    input_path, output_path = get_paths()

    print("=== 테이블 중복 수정 ===")

    # Load
    with open(input_path, 'r', encoding='utf-8') as f:
        tables = json.load(f)

    print(f"원본 테이블 수: {len(tables)}")

    # Count duplicates before
    from collections import Counter
    id_counts = Counter(t.get('table_id') for t in tables if t.get('table_id'))
    dup_before = sum(1 for c in id_counts.values() if c > 1)
    print(f"중복 ID 수 (before): {dup_before}")

    # Merge multi-page tables
    merged = merge_multipage_tables(tables)
    print(f"병합 후 테이블 수: {len(merged)}")

    # Deduplicate
    final = deduplicate_by_unique_id(merged)
    print(f"최종 테이블 수: {len(final)}")

    # Count duplicates after
    id_counts_after = Counter(t.get('table_id') for t in final if t.get('table_id'))
    dup_after = sum(1 for c in id_counts_after.values() if c > 1)
    print(f"중복 ID 수 (after): {dup_after}")

    # Save
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print(f"\n저장됨: {output_path}")

    # Summary of multi-page tables
    multi_page = [t for t in final if len(t.get('pages', [])) > 1]
    if multi_page:
        print(f"\n다중 페이지 테이블: {len(multi_page)}개")
        for t in multi_page[:5]:
            print(f"  - {t.get('table_id')}: p.{t['pages'][0]}-{t['pages'][-1]} ({len(t['pages'])}페이지, {t['rows']}행)")

    return final


if __name__ == "__main__":
    fix_tables()
