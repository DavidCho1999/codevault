"""
Part 9 테이블 추출 스크립트 v4
- 자동 스캔으로 테이블 페이지 정확히 찾기
- HTML 변환
"""

import fitz
import json
import re
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'
OUTPUT_DIR = './output'


def find_all_tables(doc):
    """Part 9 범위에서 모든 테이블과 정확한 페이지 찾기"""
    found_tables = {}

    # Part 9 페이지 범위 (약 700-1050)
    for page_num in range(700, 1050):
        page = doc[page_num]
        tabs = page.find_tables()

        if not tabs.tables:
            continue

        text = page.get_text()

        # 테이블 타이틀 패턴 찾기
        # "Table 9.x.x.x" or "Table 9.x.x.x.-A"
        patterns = [
            (r'Table (9\.\d+\.\d+\.\d+)\.-([A-G])', True),   # With suffix
            (r'Table (9\.\d+\.\d+\.\d+)\.?\s', False),       # Without suffix
        ]

        for pattern, has_suffix in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if has_suffix:
                    base_id, suffix = match
                    table_id = f'Table {base_id}.-{suffix}'
                else:
                    base_id = match
                    table_id = f'Table {base_id}'

                if table_id not in found_tables:
                    found_tables[table_id] = {
                        'page': page_num + 1,
                        'tables': tabs.tables
                    }

    return found_tables


def extract_table_html(tab, table_id):
    """테이블 데이터를 HTML로 변환"""
    data = tab.extract()

    if not data or len(data) < 2:
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

    # 헤더 행 수 결정
    header_end = 1
    for i, row in enumerate(cleaned_data):
        if i == 0:
            continue
        num_count = sum(1 for c in row if c and re.match(r'^[\d.,\s\-–]+$', c))
        if num_count > len(row) / 3:
            header_end = i
            break
        if i >= 3:
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
    html_parts.append('<tbody>')
    for row in cleaned_data[max(1, header_end):]:
        html_parts.append('<tr>')
        for j, cell in enumerate(row):
            tag = 'th' if j == 0 else 'td'
            display = cell if cell and cell != '-' else '—'
            html_parts.append(f'<{tag}>{display}</{tag}>')
        html_parts.append('</tr>')
    html_parts.append('</tbody>')

    html_parts.append('</table>')

    return '\n'.join(html_parts)


def get_table_title_from_page(doc, page_num, table_id):
    """페이지에서 테이블 타이틀 추출"""
    page = doc[page_num - 1]
    text = page.get_text()

    # 테이블 타이틀 찾기
    base_id = table_id.replace('Table ', '')
    pattern = rf'Table {re.escape(base_id)}\.?\s*\n?([^\n]+)?'
    match = re.search(pattern, text)

    if match:
        title_line = match.group(0).strip()
        # "Forming Part of" 이전까지만
        if 'Forming Part' in title_line:
            title_line = title_line.split('Forming Part')[0].strip()
        return title_line

    return table_id


def main():
    doc = fitz.open(PDF_PATH)
    print(f"PDF opened: {len(doc)} pages")

    # 1. 모든 테이블 자동 탐색
    print("\n1. Scanning for all tables...")
    all_tables = find_all_tables(doc)
    print(f"   Found {len(all_tables)} table locations")

    # 2. 테이블 추출
    print("\n2. Extracting tables...")
    tables_data = {}
    errors = []

    for table_id, info in sorted(all_tables.items()):
        page_num = info['page']
        tabs = info['tables']

        # 서픽스가 있으면 해당 인덱스 테이블 선택
        if '.-' in table_id:
            suffix = table_id.split('.-')[-1]
            idx = ord(suffix) - ord('A')
            if idx < len(tabs):
                selected_tab = tabs[idx]
            else:
                selected_tab = tabs[0]
        else:
            selected_tab = tabs[0]

        data = selected_tab.extract()
        if data and len(data) > 1:
            html = extract_table_html(selected_tab, table_id)
            if html:
                title = get_table_title_from_page(doc, page_num, table_id)
                tables_data[table_id] = {
                    'title': title,
                    'page': page_num,
                    'rows': selected_tab.row_count,
                    'cols': selected_tab.col_count,
                    'html': html
                }
                print(f"  ✓ {table_id}: {selected_tab.row_count}x{selected_tab.col_count}")
            else:
                errors.append(f"{table_id}: HTML conversion failed")
        else:
            errors.append(f"{table_id}: No valid data")

    # 3. 저장
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_path = os.path.join(OUTPUT_DIR, 'part9_tables_v4.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tables_data, f, ensure_ascii=False, indent=2)

    # 4. Summary
    print(f"\n\n=== Summary ===")
    print(f"Successfully extracted: {len(tables_data)} tables")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nErrors:")
        for e in errors[:10]:
            print(f"  - {e}")

    print(f"\nSaved to: {output_path}")

    doc.close()


if __name__ == "__main__":
    main()
