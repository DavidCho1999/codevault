"""
PDF 테이블 구조 심층 분석
- 실제 테이블 유형 분류
- 병합 셀, 다중 헤더 등 복잡도 파악
- 실패 원인 분석
"""

import pdfplumber
import fitz
import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'

# 분석할 주요 테이블 (다양한 복잡도)
SAMPLE_TABLES = {
    'simple': {
        'Table 9.3.1.7': 718,      # 간단한 테이블 (Concrete Mixes)
        'Table 9.4.3.1': 724,      # Deflections
    },
    'complex_header': {
        'Table 9.3.2.1': 719,      # 다중 헤더 (Lumber Grades)
        'Table 9.6.1.3-A': 731,    # 3행 헤더
    },
    'multi_page': {
        'Table 9.23.4.2-A': 871,   # 여러 페이지 스팬
    },
    'merged_cells': {
        'Table 9.9.1.1-A': 746,    # 병합 셀 많음
    }
}


def analyze_table_with_pdfplumber(pdf_path, page_num, table_name):
    """pdfplumber로 테이블 상세 분석"""
    print(f"\n{'='*60}")
    print(f"📊 {table_name} (페이지 {page_num})")
    print(f"{'='*60}")

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num - 1]

        # 1. 기본 추출
        tables = page.extract_tables()

        if not tables:
            print("❌ pdfplumber: 테이블 감지 실패")
            return None

        for i, table in enumerate(tables):
            print(f"\n테이블 {i+1}:")
            print(f"  행 수: {len(table)}")
            print(f"  열 수: {len(table[0]) if table else 0}")

            # 처음 5행 출력
            print(f"\n  데이터 (처음 5행):")
            for j, row in enumerate(table[:5]):
                # None/빈 값 표시
                display_row = []
                for cell in row:
                    if cell is None:
                        display_row.append("[NULL]")
                    elif cell.strip() == "":
                        display_row.append("[EMPTY]")
                    else:
                        display_row.append(cell[:20] + "..." if len(cell) > 20 else cell)
                print(f"    행{j}: {display_row}")

            # 2. 병합 셀 분석
            null_count = sum(1 for row in table for cell in row if cell is None)
            empty_count = sum(1 for row in table for cell in row if cell is not None and cell.strip() == "")
            total_cells = len(table) * (len(table[0]) if table else 0)

            print(f"\n  셀 분석:")
            print(f"    총 셀: {total_cells}")
            print(f"    NULL 셀: {null_count} ({null_count/total_cells*100:.1f}%)")
            print(f"    빈 셀: {empty_count} ({empty_count/total_cells*100:.1f}%)")

            # 3. 헤더 복잡도 추정
            header_rows = 0
            for row in table[:4]:
                text_cells = [c for c in row if c and c.strip()]
                if any(len(c) > 30 for c in text_cells):  # 긴 텍스트 = 헤더 가능성
                    header_rows += 1
            print(f"    추정 헤더 행: {header_rows}")

        return tables


def analyze_table_bbox(pdf_path, page_num):
    """테이블 경계 상자 분석 (PyMuPDF)"""
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]

    # 테이블 감지 (PyMuPDF 내장)
    tabs = page.find_tables()

    print(f"\n  PyMuPDF 테이블 감지:")
    print(f"    발견된 테이블: {len(tabs.tables)}개")

    for i, tab in enumerate(tabs.tables):
        print(f"    테이블 {i+1} bbox: {tab.bbox}")
        print(f"    테이블 {i+1} 행/열: {tab.row_count}x{tab.col_count}")

    doc.close()


def analyze_with_different_settings(pdf_path, page_num):
    """다양한 pdfplumber 설정으로 테이블 추출 비교"""
    print(f"\n  다양한 설정 테스트:")

    settings_list = [
        {"name": "기본", "settings": {}},
        {"name": "lines_only", "settings": {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines"
        }},
        {"name": "text_only", "settings": {
            "vertical_strategy": "text",
            "horizontal_strategy": "text"
        }},
        {"name": "explicit", "settings": {
            "vertical_strategy": "explicit",
            "horizontal_strategy": "explicit",
            "snap_tolerance": 5,
            "join_tolerance": 5
        }},
    ]

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num - 1]

        for config in settings_list:
            try:
                if config["settings"]:
                    tables = page.extract_tables(config["settings"])
                else:
                    tables = page.extract_tables()

                if tables:
                    table = tables[0]
                    null_pct = sum(1 for row in table for c in row if c is None) / (len(table) * len(table[0])) * 100
                    print(f"    {config['name']}: {len(table)}행 x {len(table[0])}열, NULL {null_pct:.1f}%")
                else:
                    print(f"    {config['name']}: 감지 실패")
            except Exception as e:
                print(f"    {config['name']}: 오류 - {str(e)[:50]}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.normpath(os.path.join(script_dir, PDF_PATH))

    print("="*70)
    print("🔬 PDF 테이블 구조 심층 분석")
    print("="*70)

    all_results = {}

    for category, tables in SAMPLE_TABLES.items():
        print(f"\n\n{'#'*70}")
        print(f"카테고리: {category.upper()}")
        print(f"{'#'*70}")

        for table_name, page_num in tables.items():
            result = analyze_table_with_pdfplumber(pdf_path, page_num, table_name)
            analyze_table_bbox(pdf_path, page_num)
            analyze_with_different_settings(pdf_path, page_num)

            all_results[table_name] = {
                'category': category,
                'page': page_num,
                'extracted': result is not None
            }

    # 요약
    print("\n\n" + "="*70)
    print("📋 분석 요약")
    print("="*70)

    for category in SAMPLE_TABLES.keys():
        tables_in_cat = [name for name, info in all_results.items() if info['category'] == category]
        success = sum(1 for name in tables_in_cat if all_results[name]['extracted'])
        print(f"\n{category}: {success}/{len(tables_in_cat)} 성공")

    print("\n결론: 위 분석 결과를 바탕으로 적절한 추출 전략을 선택하세요.")


if __name__ == "__main__":
    main()
