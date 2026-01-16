"""
Part 9 테이블 최종 추출 스크립트
- 수동으로 확인된 정확한 페이지 사용
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

# 수동으로 확인된 테이블 페이지 (1-indexed)
VERIFIED_TABLES = {
    # 기존 추출 성공한 테이블들 (정확한 페이지로 업데이트)
    'Table 9.3.2.1': 719,
    'Table 9.6.1.3.-A': 731,
    'Table 9.6.1.3.-B': 732,
    'Table 9.6.1.3.-C': 732,
    'Table 9.6.1.3.-D': 733,
    'Table 9.6.1.3.-E': 733,
    'Table 9.6.1.3.-F': 734,
    'Table 9.6.1.3.-G': 734,
    'Table 9.8.1.1': 742,
    'Table 9.10.3.1.-A': 755,
    'Table 9.10.3.1.-B': 756,
    'Table 9.10.9.6': 771,
    'Table 9.10.9.10.-A': 773,
    'Table 9.10.9.10.-B': 774,
    'Table 9.10.9.14': 780,
    'Table 9.10.13.2': 784,
    'Table 9.10.14.4.-A': 789,
    'Table 9.10.14.4.-B': 790,
    'Table 9.10.14.5': 794,
    'Table 9.12.2.2': 802,
    'Table 9.13.2.1': 807,
    'Table 9.13.2.2': 808,
    'Table 9.14.3.1': 812,
    'Table 9.15.4.2': 823,
    'Table 9.15.4.3.-A': 824,
    'Table 9.15.4.3.-B': 824,
    'Table 9.15.4.5.-A': 826,
    'Table 9.15.4.5.-B': 826,
    'Table 9.15.4.5.-C': 826,
    'Table 9.20.3.2': 839,
    'Table 9.20.6.2': 844,
    'Table 9.20.10.1.-A': 848,
    'Table 9.20.10.1.-B': 849,
    'Table 9.20.10.1.-C': 849,
    'Table 9.20.13.1.-A': 850,
    'Table 9.20.13.1.-B': 850,
    'Table 9.20.15.1': 851,
    'Table 9.20.17.4': 987,
    'Table 9.21.2.5': 857,
    'Table 9.23.3.1': 867,
    'Table 9.23.3.5.-A': 868,
    'Table 9.23.3.5.-B': 869,
    'Table 9.23.4.2.-A': 871,
    'Table 9.23.4.2.-B': 872,
    'Table 9.23.4.2.-C': 873,
    'Table 9.23.4.2.-D': 874,
    'Table 9.23.4.2.-E': 875,
    'Table 9.23.4.3': 876,
    'Table 9.23.6.2': 879,
    'Table 9.23.9.2': 882,
    'Table 9.23.10.1': 884,
    'Table 9.23.10.4.-A': 1023,
    'Table 9.23.10.4.-B': 1024,
    'Table 9.23.10.7': 1026,
    'Table 9.23.12.3': 1030,
    'Table 9.23.12.4': 887,
    'Table 9.23.13.2': 889,
    'Table 9.23.13.11': 892,
    'Table 9.23.14.5': 893,
    'Table 9.23.17.1.-A': 895,
    'Table 9.23.17.1.-B': 895,
    'Table 9.23.17.2.-A': 897,
    'Table 9.23.17.2.-B': 898,
    'Table 9.25.2.2': 902,
    'Table 9.26.2.1': 908,
    'Table 9.26.3.1': 910,
    'Table 9.26.10.2': 915,
    'Table 9.30.1.2': 934,
    'Table 9.32.3.3': 957,
    'Table 9.32.3.5': 960,
    'Table 9.32.3.6': 961,
    'Table 9.32.3.10': 964,
    'Table 9.32.3.13.-A': 965,
    'Table 9.32.3.13.-B': 965,
    'Table 9.33.5.1': 974,
    'Table 9.34.2.2': 977,
    'Table 9.36.2.6.-A': 1003,
    'Table 9.36.2.6.-B': 1005,
    'Table 9.36.2.8': 1006,
    'Table 9.36.3.10': 1015,
}

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
                # 중복 공백 제거
                text = re.sub(r'\s+', ' ', text)
                cleaned_row.append(text)
        cleaned_data.append(cleaned_row)

    # 헤더 행 수 결정 (첫 번째 데이터 행까지)
    header_end = 1
    for i, row in enumerate(cleaned_data):
        # 숫자가 많으면 데이터 행
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
    for i, row in enumerate(cleaned_data[:max(1, header_end)]):
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


def main():
    doc = fitz.open(PDF_PATH)
    print(f"PDF opened: {len(doc)} pages")
    print(f"Tables to extract: {len(VERIFIED_TABLES)}")

    tables_data = {}
    errors = []

    for table_id, page_num in sorted(VERIFIED_TABLES.items()):
        print(f"\nProcessing {table_id} (page {page_num})...")

        page = doc[page_num - 1]
        tabs = page.find_tables()

        if not tabs.tables:
            errors.append(f"{table_id}: No table found on page {page_num}")
            continue

        # 여러 테이블이 있는 페이지에서 올바른 테이블 선택
        table_suffix = table_id.split('.')[-1]
        selected_tab = None

        # A, B, C 등의 서픽스 처리
        if '-' in table_suffix:
            suffix_letter = table_suffix.split('-')[-1]
            idx = ord(suffix_letter) - ord('A')
            if idx < len(tabs.tables):
                selected_tab = tabs.tables[idx]
            else:
                selected_tab = tabs.tables[0]
        else:
            selected_tab = tabs.tables[0]

        if selected_tab:
            data = selected_tab.extract()
            if data and len(data) > 1:
                html = extract_table_html(selected_tab, table_id)
                if html:
                    tables_data[table_id] = {
                        'page': page_num,
                        'rows': selected_tab.row_count,
                        'cols': selected_tab.col_count,
                        'html': html
                    }
                    print(f"  ✓ Extracted: {selected_tab.row_count}x{selected_tab.col_count}")
                else:
                    errors.append(f"{table_id}: HTML conversion failed")
            else:
                errors.append(f"{table_id}: No valid data")
        else:
            errors.append(f"{table_id}: Could not select table")

    # Save results
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_path = os.path.join(OUTPUT_DIR, 'part9_tables_final.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tables_data, f, ensure_ascii=False, indent=2)

    print(f"\n\n=== Summary ===")
    print(f"Successfully extracted: {len(tables_data)} tables")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nErrors:")
        for e in errors[:20]:
            print(f"  - {e}")

    print(f"\nSaved to: {output_path}")

    doc.close()


if __name__ == "__main__":
    main()
