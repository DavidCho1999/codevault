"""검증 테이블 페이지 위치 찾기"""
import fitz
import sys
sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'

# 검증할 테이블 목록
TARGET_TABLES = [
    'Table 9.3.2.1',
    'Table 9.20.3.2',
    'Table 9.23.3.1',
    'Table 9.23.3.5',
    'Table 9.20.5.2.-A',
    'Table 9.20.5.2.-B',
]

def find_table_pages(doc, table_id):
    """테이블이 있는 페이지 찾기"""
    pages = []
    for page_num in range(700, 1050):
        page = doc[page_num]
        text = page.get_text()
        if table_id in text:
            # "Forming Part of" 확인 (테이블 정의)
            if 'Forming Part of' in text:
                idx = text.find(table_id)
                context = text[max(0, idx-50):min(len(text), idx+200)]
                pages.append((page_num + 1, 'definition', context[:150]))
    return pages

def main():
    doc = fitz.open(PDF_PATH)
    print(f"PDF: {len(doc)} pages\n")

    for table_id in TARGET_TABLES:
        print(f"\n{'='*60}")
        print(f"{table_id}")
        print('='*60)

        pages = find_table_pages(doc, table_id)
        if pages:
            for page_num, ptype, context in pages:
                print(f"  Page {page_num} ({ptype})")
                print(f"  Context: {context[:100]}...")

                # 해당 페이지의 테이블 구조 확인
                page = doc[page_num - 1]
                tabs = page.find_tables()
                if tabs.tables:
                    print(f"  Tables found: {len(tabs.tables)}")
                    for i, tab in enumerate(tabs.tables):
                        print(f"    [{i}] {tab.row_count}x{tab.col_count}")
                        data = tab.extract()
                        if data and len(data) > 0:
                            header = data[0]
                            print(f"        Header: {header[:3]}...")
        else:
            print("  Not found in p.700-1050")

    doc.close()

if __name__ == "__main__":
    main()
