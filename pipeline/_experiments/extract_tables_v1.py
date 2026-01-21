"""
Part 9 테이블 추출 스크립트
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

def find_table_pages(doc):
    """Part 9 테이블이 있는 페이지 찾기"""
    table_pages = {}
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        # Find Table 9.x.x.x patterns
        matches = re.findall(r'Table (9\.\d+\.\d+\.\d+)\.', text)
        for table_id in matches:
            full_id = f'Table {table_id}'
            if full_id not in table_pages:
                table_pages[full_id] = page_num
    
    return table_pages

def extract_table_html(tab, table_id):
    """테이블 데이터를 HTML로 변환"""
    data = tab.extract()
    
    if not data:
        return None
    
    # Clean data - replace None with empty string
    cleaned_data = []
    for row in data:
        cleaned_row = []
        for cell in row:
            if cell is None:
                cleaned_row.append('')
            else:
                # Clean up whitespace
                cleaned_row.append(str(cell).strip().replace('\n', ' '))
        cleaned_data.append(cleaned_row)
    
    # Determine header rows (usually first few rows with merged cells)
    header_end = 0
    for i, row in enumerate(cleaned_data):
        empty_count = sum(1 for c in row if c == '' or c == '-')
        if empty_count > len(row) / 2:
            header_end = i + 1
        else:
            break
    
    # If no clear header, assume first row is header
    if header_end == 0:
        header_end = 1
    
    # Build HTML
    html_parts = [f'<table class="obc-table">']
    
    # Header
    html_parts.append('<thead>')
    for i, row in enumerate(cleaned_data[:header_end]):
        html_parts.append('<tr>')
        for cell in row:
            if cell and cell != '-':
                html_parts.append(f'<th>{cell}</th>')
            else:
                html_parts.append('<th></th>')
        html_parts.append('</tr>')
    html_parts.append('</thead>')
    
    # Body
    html_parts.append('<tbody>')
    for row in cleaned_data[header_end:]:
        html_parts.append('<tr>')
        for j, cell in enumerate(row):
            if j == 0:
                html_parts.append(f'<th>{cell}</th>')  # Row header
            else:
                html_parts.append(f'<td>{cell if cell and cell != "-" else "—"}</td>')
        html_parts.append('</tr>')
    html_parts.append('</tbody>')
    
    html_parts.append('</table>')
    
    return '\n'.join(html_parts)

def main():
    doc = fitz.open(PDF_PATH)
    print(f"PDF opened: {len(doc)} pages")
    
    # Find all table pages
    table_pages = find_table_pages(doc)
    print(f"Found {len(table_pages)} table references")
    
    # Extract tables
    tables_data = {}
    errors = []
    
    for table_id, page_num in sorted(table_pages.items()):
        print(f"\nProcessing {table_id} (page {page_num + 1})...")
        
        page = doc[page_num]
        tabs = page.find_tables()
        
        if not tabs.tables:
            errors.append(f"{table_id}: No table found on page {page_num + 1}")
            continue
        
        # Find the table that matches (usually first one on page)
        for tab in tabs.tables:
            data = tab.extract()
            if data and len(data) > 1:
                html = extract_table_html(tab, table_id)
                if html:
                    tables_data[table_id] = {
                        'page': page_num + 1,
                        'rows': tab.row_count,
                        'cols': tab.col_count,
                        'html': html
                    }
                    print(f"  ✓ Extracted: {tab.row_count}x{tab.col_count}")
                    break
        else:
            errors.append(f"{table_id}: Could not extract valid table")
    
    # Save results
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    output_path = os.path.join(OUTPUT_DIR, 'part9_tables.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tables_data, f, ensure_ascii=False, indent=2)
    
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
