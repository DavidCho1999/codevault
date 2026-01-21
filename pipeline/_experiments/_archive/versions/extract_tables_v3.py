"""
Part 9 테이블 추출 스크립트 v3
- 테이블 제목 바로 아래에 있는 테이블만 추출
- 참조가 아닌 실제 테이블 위치 찾기
"""

import fitz
import json
import re
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'
OUTPUT_DIR = './output'

def find_tables_with_content(doc):
    """
    테이블 제목과 실제 테이블 내용이 같은 페이지에 있는 경우만 찾기
    """
    table_data = {}
    
    # Part 9 페이지 범위 (대략 700-1000)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        # 테이블 제목 패턴 찾기: "Table 9.x.x.x." 다음에 제목이 오는 경우
        # 예: "Table 9.3.2.1.\nMinimum Lumber Grades"
        pattern = r'Table (9\.\d+\.\d+\.\d+)\.\s*\n([A-Z][^\n]+)'
        matches = re.findall(pattern, text)
        
        if not matches:
            # 대체 패턴: 같은 줄에 있는 경우
            pattern2 = r'Table (9\.\d+\.\d+\.\d+)\.\s+([A-Z][A-Za-z].*?)(?:\n|Forming)'
            matches = re.findall(pattern2, text)
        
        for table_num, title in matches:
            table_id = f"Table {table_num}"
            
            # 이 페이지에 실제 테이블이 있는지 확인
            tabs = page.find_tables()
            if tabs.tables:
                # 이미 찾은 테이블이 아닌 경우만 추가
                if table_id not in table_data:
                    table_data[table_id] = {
                        'page': page_num,
                        'title': title.strip(),
                        'tables_on_page': len(tabs.tables)
                    }
    
    return table_data

def clean_cell(cell):
    """셀 데이터 정리"""
    if cell is None:
        return ''
    text = str(cell).strip()
    text = ' '.join(text.split())
    return text

def extract_table_html(tab, table_id, title):
    """테이블을 HTML로 변환"""
    data = tab.extract()
    
    if not data or len(data) < 2:
        return None
    
    # Clean data
    cleaned_data = []
    for row in data:
        cleaned_row = [clean_cell(cell) for cell in row]
        cleaned_data.append(cleaned_row)
    
    # Remove empty rows
    cleaned_data = [row for row in cleaned_data if any(cell for cell in row)]
    
    if not cleaned_data:
        return None
    
    # Detect header rows (rows with empty cells are usually headers)
    header_end = 1
    for i, row in enumerate(cleaned_data[:6]):
        empty_count = sum(1 for c in row if not c)
        if empty_count > 0 and i < 5:
            header_end = i + 1
    
    # Build HTML
    html_parts = ['<table class="obc-table">']
    
    # Header
    html_parts.append('<thead>')
    for row in cleaned_data[:header_end]:
        html_parts.append('<tr>')
        for cell in row:
            html_parts.append(f'<th>{cell}</th>')
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
    print(f"PDF: {len(doc)} pages")
    
    # Find tables
    print("Finding tables...")
    table_info = find_tables_with_content(doc)
    print(f"Found {len(table_info)} tables")
    
    # Extract
    tables_data = {}
    errors = []
    
    for table_id in sorted(table_info.keys(), key=lambda x: [int(n) for n in x.replace('Table ', '').split('.')]):
        info = table_info[table_id]
        page_num = info['page']
        title = info['title']
        
        print(f"{table_id}: {title[:40]}... (p{page_num + 1})", end=' ')
        
        page = doc[page_num]
        tabs = page.find_tables()
        
        if not tabs.tables:
            errors.append(f"{table_id}: No table")
            print("✗")
            continue
        
        # Find best matching table
        best_tab = tabs.tables[0]
        
        html = extract_table_html(best_tab, table_id, title)
        if html:
            tables_data[table_id] = {
                'title': title,
                'page': page_num + 1,
                'rows': best_tab.row_count,
                'cols': best_tab.col_count,
                'html': html
            }
            print(f"✓ {best_tab.row_count}x{best_tab.col_count}")
        else:
            errors.append(f"{table_id}: HTML error")
            print("✗")
    
    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'part9_tables.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tables_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== Summary ===")
    print(f"Extracted: {len(tables_data)}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors:")
        for e in errors[:10]:
            print(f"  - {e}")
    
    print(f"\nSaved: {output_path}")
    
    doc.close()

if __name__ == "__main__":
    main()
