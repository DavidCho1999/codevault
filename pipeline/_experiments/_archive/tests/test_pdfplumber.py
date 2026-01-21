"""
pdfplumber 테스트 스크립트
- 가장 손상 심한 테이블들 테스트
"""

import pdfplumber
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'

# 문제가 있었던 테이블들
TEST_TABLES = {
    'Table 9.15.3.4': 820,   # 완전 손상
    'Table 9.6.1.3-A': 731,  # 7번 중복
    'Table 9.23.4.2-A': 871, # 단어 분리
    'Table 9.3.1.7': 717,    # 노트 누락
}

def test_table_extraction(pdf_path, table_name, page_num):
    """단일 테이블 추출 테스트"""
    print(f"\n{'='*60}")
    print(f"Testing: {table_name} (Page {page_num})")
    print('='*60)

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num - 1]  # 0-indexed

        # 방법 1: 자동 감지
        tables = page.find_tables()
        print(f"\n[자동 감지] Found {len(tables)} table(s)")

        for i, table in enumerate(tables):
            data = table.extract()
            print(f"\n--- Table {i+1} ({len(data)} rows) ---")

            # 첫 5행 출력
            for j, row in enumerate(data[:5]):
                # 각 셀 길이 제한
                formatted_row = [str(cell)[:30] + '...' if cell and len(str(cell)) > 30 else str(cell) for cell in row]
                print(f"  Row {j}: {formatted_row}")

            if len(data) > 5:
                print(f"  ... ({len(data) - 5} more rows)")

        # 방법 2: 설정 조정
        print(f"\n[설정 조정] Testing with custom settings...")

        table_settings = {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 3,
            "min_words_vertical": 1,
            "min_words_horizontal": 1,
        }

        tables_custom = page.find_tables(table_settings)
        print(f"Found {len(tables_custom)} table(s) with custom settings")

        if tables_custom:
            data = tables_custom[0].extract()
            print(f"First table: {len(data)} rows, {len(data[0]) if data else 0} columns")

            # 헤더 출력
            if data:
                print(f"\nHeaders: {data[0]}")

def compare_with_pymupdf(pdf_path, table_name, page_num):
    """PyMuPDF와 비교"""
    import fitz

    print(f"\n[비교] PyMuPDF vs pdfplumber for {table_name}")

    # PyMuPDF
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    pymupdf_tables = page.find_tables()
    print(f"  PyMuPDF: {len(pymupdf_tables.tables)} table(s)")

    if pymupdf_tables.tables:
        first_table = pymupdf_tables[0].extract()
        print(f"    - Rows: {len(first_table)}, Cols: {len(first_table[0]) if first_table else 0}")

    doc.close()

    # pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num - 1]
        plumber_tables = page.find_tables()
        print(f"  pdfplumber: {len(plumber_tables)} table(s)")

        if plumber_tables:
            first_table = plumber_tables[0].extract()
            print(f"    - Rows: {len(first_table)}, Cols: {len(first_table[0]) if first_table else 0}")

def main():
    print("=" * 60)
    print("pdfplumber 테이블 추출 테스트")
    print("=" * 60)

    for table_name, page_num in TEST_TABLES.items():
        try:
            test_table_extraction(PDF_PATH, table_name, page_num)
            compare_with_pymupdf(PDF_PATH, table_name, page_num)
        except Exception as e:
            print(f"Error testing {table_name}: {e}")

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)

if __name__ == '__main__':
    main()
