"""
Part 9 테이블 추출 스크립트 v2
- 테이블 실제 위치 찾기 개선
- PyMuPDF find_tables() 사용
- HTML 테이블로 변환
"""

import fitz
import json
import re
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'
OUTPUT_DIR = './output'

def find_table_actual_pages(doc):
    """테이블이 실제로 있는 페이지 찾기"""
    table_pages = {}
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        # Find Table 9.x.x.x patterns
        matches = re.findall(r'Table (9\.\d+\.\d+\.\d+)\.', text)
        
        for table_id in matches:
            full_id = f'Table {table_id}'
            
            # Check if actual table exists on this page
            tabs = page.find_tables()
            if tabs.tables and full_id not in table_pages:
                table_pages[full_id] = page_num
    
    return table_pages

def clean_cell(cell):
    """셀 데이터 정리"""
    if cell is None:
        return ''
    text = str(cell).strip()
    # Replace multiple whitespace with single space
    text = ' '.join(text.split())
    return text

def extract_table_html(tab, table_id):
    """테이블 데이터를 HTML로 변환"""
    data = tab.extract()
    
    if not data or len(data) < 2:
        return None
    
    # Clean data
    cleaned_data = []
    for row in data:
        cleaned_row = [clean_cell(cell) for cell in row]
        cleaned_data.append(cleaned_row)
    
    # Remove completely empty rows
    cleaned_data = [row for row in cleaned_data if any(cell for cell in row)]
    
    if not cleaned_data:
        return None
    
    # Detect header rows
    # Headers usually have merged cells (empty cells) or special formatting
    header_end = 1
    for i, row in enumerate(cleaned_data[:5]):
        empty_count = sum(1 for c in row if not c)
        if empty_count > 0 and i < 4:
            header_end = i + 1
    
    # Build HTML with proper structure
    html_parts = ['<table class="obc-table">']
    
    # Caption (table title) - extracted from first rows if present
    
    # Header
    html_parts.append('<thead>')
    for row in cleaned_data[:header_end]:
        html_parts.append('<tr>')
        for cell in row:
            content = cell if cell else ''
            html_parts.append(f'<th>{content}</th>')
        html_parts.append('</tr>')
    html_parts.append('</thead>')
    
    # Body
    html_parts.append('<tbody>')
    for row in cleaned_data[header_end:]:
        html_parts.append('<tr>')
        for j, cell in enumerate(row):
            content = cell if cell else '—'
            if j == 0:
                html_parts.append(f'<th>{content}</th>')
            else:
                html_parts.append(f'<td>{content}</td>')
        html_parts.append('</tr>')
    html_parts.append('</tbody>')
    
    html_parts.append('</table>')
    
    return '\n'.join(html_parts)

def main():
    doc = fitz.open(PDF_PATH)
    print(f"PDF opened: {len(doc)} pages")
    
    # Find all table pages
    print("Finding table pages...")
    table_pages = find_table_actual_pages(doc)
    print(f"Found {len(table_pages)} tables with actual table content")
    
    # Extract tables
    tables_data = {}
    errors = []
    
    for table_id in sorted(table_pages.keys(), key=lambda x: [int(n) for n in x.replace('Table ', '').split('.')]):
        page_num = table_pages[table_id]
        print(f"Processing {table_id} (page {page_num + 1})...", end=' ')
        
        page = doc[page_num]
        tabs = page.find_tables()
        
        if not tabs.tables:
            errors.append(f"{table_id}: No table found")
            print("✗ No table")
            continue
        
        # Get the best matching table
        best_tab = None
        for tab in tabs.tables:
            data = tab.extract()
            if data and len(data) > 1:
                # Check if table contains the table ID
                flat_text = ' '.join([str(c) for row in data for c in row if c])
                if table_id.replace('Table ', '') in flat_text or best_tab is None:
                    best_tab = tab
                    break
        
        if best_tab is None:
            best_tab = tabs.tables[0]
        
        html = extract_table_html(best_tab, table_id)
        if html:
            tables_data[table_id] = {
                'page': page_num + 1,
                'rows': best_tab.row_count,
                'cols': best_tab.col_count,
                'html': html
            }
            print(f"✓ {best_tab.row_count}x{best_tab.col_count}")
        else:
            errors.append(f"{table_id}: Could not generate HTML")
            print("✗ HTML error")
    
    # Save results
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    output_path = os.path.join(OUTPUT_DIR, 'part9_tables.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tables_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== Summary ===")
    print(f"Successfully extracted: {len(tables_data)} tables")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  - {e}")
    
    print(f"\nSaved to: {output_path}")
    
    doc.close()

if __name__ == "__main__":
    main()
