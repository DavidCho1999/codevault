"""
Part 9 테이블 추출 스크립트 v6
- 핵심 테이블 수동 매핑 + 자동 탐색 하이브리드
- 테이블 내용 검증
"""

import fitz
import json
import re
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'
OUTPUT_DIR = './output'

# 수동으로 확인된 핵심 테이블 (page는 1-indexed)
MANUAL_TABLES = {
    'Table 9.3.2.1': {'page': 719, 'idx': 0, 'title': 'Minimum Lumber Grades for Specific End Uses'},
    'Table 9.20.3.2': {'page': 839, 'idx': 0, 'title': 'Mortar Proportions by Volume'},
}


def validate_table_content(data, table_id):
    """테이블 내용이 유효한지 검증 - 완화된 버전"""
    if not data or len(data) < 2:
        return False
    # 기본적으로 모든 테이블 허용 (수동 매핑으로 핵심 테이블 처리)
    return True


def extract_table_html(tab, table_id):
    """테이블 데이터를 HTML로 변환"""
    data = tab.extract()

    if not data or len(data) < 2:
        return None

    if not validate_table_content(data, table_id):
        return None

    # Clean data
    cleaned_data = []
    for row in data:
        cleaned_row = []
        for cell in row:
            if cell is None:
                cleaned_row.append('')
            else:
                text = str(cell).strip().replace('\n', ' ')
                text = re.sub(r'\s+', ' ', text)
                cleaned_row.append(text)
        cleaned_data.append(cleaned_row)

    # 빈 행 제거
    cleaned_data = [row for row in cleaned_data if any(cell.strip() for cell in row)]

    if len(cleaned_data) < 2:
        return None

    # 헤더 행 수 결정
    header_end = 1
    for i, row in enumerate(cleaned_data):
        if i == 0:
            continue
        # 첫 열이 실제 데이터 시작인지 확인
        first_cell = row[0].strip() if row[0] else ''
        # "Stud", "Roof", "Wall" 등으로 시작하면 데이터 행
        if first_cell and any(first_cell.startswith(w) for w in ['Stud', 'Plank', 'Post', 'Roof', 'Sub', 'Wall']):
            header_end = i
            break
        # 숫자로 시작하면 데이터 행
        if first_cell and re.match(r'^\d', first_cell):
            header_end = i
            break
        if i >= 4:
            header_end = i
            break

    # Build HTML
    html_parts = [f'<table class="obc-table" data-table-id="{table_id}">']

    # Header
    html_parts.append('<thead>')
    for row in cleaned_data[:max(1, header_end)]:
        html_parts.append('<tr>')
        for cell in row:
            html_parts.append(f'<th>{cell}</th>')
        html_parts.append('</tr>')
    html_parts.append('</thead>')

    # Body
    if header_end < len(cleaned_data):
        html_parts.append('<tbody>')
        for ri, row in enumerate(cleaned_data[header_end:]):
            row_class = 'bg-white' if ri % 2 == 0 else 'bg-gray-50'
            html_parts.append(f'<tr class="{row_class}">')
            for j, cell in enumerate(row):
                tag = 'th' if j == 0 else 'td'
                display = cell if cell and cell != '-' else '—'
                html_parts.append(f'<{tag}>{display}</{tag}>')
            html_parts.append('</tr>')
        html_parts.append('</tbody>')

    html_parts.append('</table>')

    return '\n'.join(html_parts)


def find_all_tables(doc):
    """Part 9 범위에서 모든 테이블 찾기"""
    found_tables = {}

    # Part 9 페이지 범위
    for page_num in range(700, 1050):
        page = doc[page_num]
        text = page.get_text()

        tabs = page.find_tables()
        if not tabs.tables:
            continue

        # 테이블 타이틀 패턴 찾기
        title_pattern = r'Table\s+(9\.\d+\.\d+\.\d+)\.?\s*\n?\s*([A-Z][^()\n]{5,80})?'
        matches = re.finditer(title_pattern, text)

        for match in matches:
            table_num = match.group(1)
            table_desc = match.group(2) if match.group(2) else ''

            # 실제 테이블 페이지 확인
            context_start = max(0, match.start() - 50)
            context_end = min(len(text), match.end() + 200)
            context = text[context_start:context_end]

            is_table_page = (
                'Forming Part of' in context or
                'Notes to Table' in text
            )

            if not is_table_page:
                continue

            base_id = f'Table {table_num}'

            # 수동 매핑이 있으면 스킵 (나중에 처리)
            if base_id in MANUAL_TABLES:
                continue

            # 서픽스 처리
            suffix_matches = re.findall(rf'Table {re.escape(table_num)}\.-([A-G])', text)

            if suffix_matches:
                for idx, suffix in enumerate(sorted(set(suffix_matches))):
                    table_id = f'Table {table_num}.-{suffix}'
                    if table_id not in found_tables:
                        found_tables[table_id] = {
                            'page': page_num + 1,
                            'tables': tabs.tables,
                            'suffix_idx': idx,
                            'title': f'Table {table_num}.-{suffix}. {table_desc}'.strip()
                        }
            else:
                if base_id not in found_tables:
                    found_tables[base_id] = {
                        'page': page_num + 1,
                        'tables': tabs.tables,
                        'suffix_idx': 0,
                        'title': f'{base_id}. {table_desc}'.strip()
                    }

    return found_tables


def main():
    doc = fitz.open(PDF_PATH)
    print(f"PDF opened: {len(doc)} pages")

    tables_data = {}
    errors = []

    # 1. 수동 매핑된 테이블 먼저 처리
    print("\n1. Processing manually mapped tables...")
    for table_id, info in MANUAL_TABLES.items():
        page_num = info['page']
        idx = info['idx']
        title = info['title']

        page = doc[page_num - 1]
        tabs = page.find_tables()

        if tabs.tables and idx < len(tabs.tables):
            tab = tabs.tables[idx]
            html = extract_table_html(tab, table_id)
            if html:
                tables_data[table_id] = {
                    'title': f'{table_id}. {title}',
                    'page': page_num,
                    'rows': tab.row_count,
                    'cols': tab.col_count,
                    'html': html
                }
                print(f"  ✓ {table_id}: {tab.row_count}x{tab.col_count} (p.{page_num})")
            else:
                errors.append(f"{table_id}: HTML conversion failed")
        else:
            errors.append(f"{table_id}: Table not found on page {page_num}")

    # 2. 자동 탐색
    print("\n2. Auto-scanning for other tables...")
    all_tables = find_all_tables(doc)
    print(f"   Found {len(all_tables)} additional table locations")

    # 3. 자동 탐색된 테이블 추출
    print("\n3. Extracting auto-detected tables...")
    for table_id, info in sorted(all_tables.items()):
        page_num = info['page']
        tabs = info['tables']
        suffix_idx = info.get('suffix_idx', 0)
        title = info.get('title', table_id)

        if suffix_idx < len(tabs):
            selected_tab = tabs[suffix_idx]
        else:
            selected_tab = tabs[0]

        data = selected_tab.extract()
        if data and len(data) > 1:
            html = extract_table_html(selected_tab, table_id)
            if html:
                tables_data[table_id] = {
                    'title': title,
                    'page': page_num,
                    'rows': selected_tab.row_count,
                    'cols': selected_tab.col_count,
                    'html': html
                }
                print(f"  ✓ {table_id}: {selected_tab.row_count}x{selected_tab.col_count} (p.{page_num})")
            else:
                errors.append(f"{table_id}: HTML conversion failed")
        else:
            errors.append(f"{table_id}: No valid data")

    # 4. 저장
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_path = os.path.join(OUTPUT_DIR, 'part9_tables_final.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tables_data, f, ensure_ascii=False, indent=2)

    # 5. Summary
    print(f"\n\n=== Summary ===")
    print(f"Successfully extracted: {len(tables_data)} tables")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nErrors:")
        for e in errors[:10]:
            print(f"  - {e}")

    print(f"\nSaved to: {output_path}")

    # 6. 검증
    print("\n=== Verification ===")
    for key_table in ['Table 9.3.2.1', 'Table 9.20.3.2']:
        if key_table in tables_data:
            t = tables_data[key_table]
            print(f"{key_table}: Page {t['page']}, {t['rows']}x{t['cols']}")
        else:
            print(f"{key_table}: NOT FOUND")

    doc.close()


if __name__ == "__main__":
    main()
