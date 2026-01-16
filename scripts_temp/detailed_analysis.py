"""
낮은 정확도 테이블 상세 분석
Table 9.3.2.1, 9.20.3.2.-B, 9.20.5.2.-A 분석
"""
import sys
import pdfplumber
import fitz
sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'

def analyze_table_9_3_2_1():
    """Table 9.3.2.1 상세 분석"""
    print("="*70)
    print("Table 9.3.2.1 - Minimum Lumber Grades for Specific End Uses")
    print("Page 719 (0-indexed: 718)")
    print("="*70)

    # pdfplumber
    print("\n[pdfplumber 결과]")
    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[718]
        tables = page.extract_tables()
        for i, table in enumerate(tables):
            print(f"\nTable {i}: {len(table)} rows x {len(table[0]) if table else 0} cols")
            for row_idx, row in enumerate(table[:15]):  # 전체 출력
                print(f"  Row {row_idx}: {row}")

    # PyMuPDF
    print("\n[PyMuPDF 결과]")
    doc = fitz.open(PDF_PATH)
    page = doc[718]
    tabs = page.find_tables()
    for i, tab in enumerate(tabs.tables):
        data = tab.extract()
        print(f"\nTable {i}: {tab.row_count} rows x {tab.col_count} cols")
        for row_idx, row in enumerate(data[:15]):
            print(f"  Row {row_idx}: {row}")
    doc.close()


def analyze_table_9_20_3_2_B():
    """Table 9.20.3.2.-B 상세 분석 (Mortar Proportions)"""
    print("\n" + "="*70)
    print("Table 9.20.3.2.-B - Mortar Proportions by Volume")
    print("Page 839 (0-indexed: 838)")
    print("="*70)

    # pdfplumber
    print("\n[pdfplumber 결과]")
    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[838]
        tables = page.extract_tables()
        for i, table in enumerate(tables):
            print(f"\nTable {i}: {len(table)} rows x {len(table[0]) if table else 0} cols")
            for row_idx, row in enumerate(table):
                print(f"  Row {row_idx}: {row}")


def analyze_table_9_20_5_2_A():
    """Table 9.20.5.2.-A 상세 분석 (Steel Lintels)"""
    print("\n" + "="*70)
    print("Table 9.20.5.2.-A - Loose Steel Lintels")
    print("Page 841 (0-indexed: 840)")
    print("="*70)

    # pdfplumber
    print("\n[pdfplumber 결과]")
    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[840]
        tables = page.extract_tables()
        for i, table in enumerate(tables):
            if not table:
                continue
            print(f"\nTable {i}: {len(table)} rows x {len(table[0]) if table else 0} cols")
            # 처음 5행, 마지막 3행
            for row_idx in range(min(5, len(table))):
                print(f"  Row {row_idx}: {table[row_idx]}")
            if len(table) > 8:
                print("  ...")
                for row_idx in range(len(table)-3, len(table)):
                    print(f"  Row {row_idx}: {table[row_idx]}")


def check_merged_cells():
    """병합 셀 확인"""
    print("\n" + "="*70)
    print("병합 셀 분석")
    print("="*70)

    doc = fitz.open(PDF_PATH)

    test_pages = [718, 838, 840]  # 9.3.2.1, 9.20.3.2, 9.20.5.2.-A

    for page_num in test_pages:
        page = doc[page_num]
        tabs = page.find_tables()

        print(f"\nPage {page_num + 1}:")
        for i, tab in enumerate(tabs.tables):
            print(f"  Table {i}: bbox={tab.bbox}")
            # 셀 정보 확인
            cells = tab.cells
            if cells:
                print(f"    Total cells: {len(cells)}")
                # 병합 셀 확인 (크기가 큰 셀)
                for cell in cells[:5]:
                    print(f"    Cell: {cell}")

    doc.close()


if __name__ == "__main__":
    analyze_table_9_3_2_1()
    analyze_table_9_20_3_2_B()
    analyze_table_9_20_5_2_A()
    check_merged_cells()
