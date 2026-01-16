"""
Part 9 테이블 추출 스크립트 v5
- 테이블 타이틀 + 실제 테이블 내용이 있는 페이지만 선택
- 더 정확한 헤더/바디 분리
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
    """Part 9 범위에서 모든 테이블 찾기 - 타이틀 + 테이블이 함께 있는 페이지"""
    found_tables = {}

    # Part 9 페이지 범위
    for page_num in range(700, 1050):
        page = doc[page_num]
        text = page.get_text()

        # 이 페이지에 테이블이 있는지 확인
        tabs = page.find_tables()
        if not tabs.tables:
            continue

        # 테이블 타이틀 패턴 찾기: "Table 9.x.x.x."
        # "Forming Part of" 또는 "Minimum" 등이 근처에 있어야 실제 테이블
        title_pattern = r'Table\s+(9\.\d+\.\d+\.\d+)\.?\s*\n?\s*([A-Z][^()\n]{5,80})?'
        matches = re.finditer(title_pattern, text)

        for match in matches:
            table_num = match.group(1)
            table_desc = match.group(2) if match.group(2) else ''

            # "Forming Part of" 확인 - 실제 테이블 페이지 표시
            context_start = max(0, match.start() - 50)
            context_end = min(len(text), match.end() + 200)
            context = text[context_start:context_end]

            is_table_page = (
                'Forming Part of' in context or
                table_desc.strip().startswith('Minimum') or
                table_desc.strip().startswith('Maximum') or
                table_desc.strip().startswith('Required') or
                table_desc.strip().startswith('Size') or
                table_desc.strip().startswith('Type') or
                'Notes to Table' in text
            )

            if not is_table_page:
                continue

            base_id = f'Table {table_num}'

            # 이미 더 좋은 페이지가 있으면 스킵
            if base_id in found_tables:
                # 기존 것과 비교 - 테이블 크기가 더 크면 교체
                existing_size = found_tables[base_id]['tables'][0].row_count
                new_size = tabs.tables[0].row_count
                if new_size <= existing_size:
                    continue

            # 서픽스가 있는 테이블 처리 (-A, -B 등)
            suffix_matches = re.findall(rf'Table {re.escape(table_num)}\.-([A-G])', text)

            if suffix_matches:
                # 서픽스가 있는 테이블들
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
                # 서픽스 없는 테이블
                if base_id not in found_tables:
                    found_tables[base_id] = {
                        'page': page_num + 1,
                        'tables': tabs.tables,
                        'suffix_idx': 0,
                        'title': f'{base_id}. {table_desc}'.strip()
                    }

    return found_tables


def extract_table_html(tab, table_id):
    """테이블 데이터를 HTML로 변환 - 개선된 헤더 감지"""
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

    # 빈 행 제거
    cleaned_data = [row for row in cleaned_data if any(cell.strip() for cell in row)]

    if len(cleaned_data) < 2:
        return None

    # 헤더 행 수 결정 - 첫 번째 숫자 데이터 행 찾기
    header_end = 1
    for i, row in enumerate(cleaned_data):
        if i == 0:
            continue

        # 숫자 데이터가 많으면 데이터 행
        num_pattern = r'^[\d.,\-–—\s]+$|^\d+(\.\d+)?$|^No\.\s*\d'
        num_count = sum(1 for c in row if c and re.match(num_pattern, c.strip()))

        # 빈 셀이 적고 숫자가 있으면 데이터 행 시작
        non_empty = sum(1 for c in row if c.strip())
        if non_empty > 2 and num_count >= 1:
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
        suffix_idx = info.get('suffix_idx', 0)
        title = info.get('title', table_id)

        # 서픽스에 따라 테이블 선택
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

    # 3. 저장
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_path = os.path.join(OUTPUT_DIR, 'part9_tables_v5.json')
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

    # 5. 검증: Table 9.3.2.1 확인
    print("\n=== Verification: Table 9.3.2.1 ===")
    if 'Table 9.3.2.1' in tables_data:
        t = tables_data['Table 9.3.2.1']
        print(f"Page: {t['page']}")
        print(f"Size: {t['rows']}x{t['cols']}")
        print(f"Title: {t['title'][:80]}")
    else:
        print("Not found!")

    doc.close()


if __name__ == "__main__":
    main()
