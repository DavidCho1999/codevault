"""
개선된 테이블 추출 - 병합 셀, 헤더 처리 개선
"""
import sys
import pdfplumber
import fitz
import pandas as pd
from copy import deepcopy
sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'

def filldown_none_cells(table_data):
    """None 셀을 위의 값으로 채우기 (병합 셀 처리)"""
    if not table_data:
        return table_data

    result = deepcopy(table_data)
    cols = len(result[0]) if result else 0

    for col in range(cols):
        last_value = None
        for row in range(len(result)):
            if result[row][col] is None or result[row][col] == '':
                result[row][col] = last_value
            else:
                last_value = result[row][col]

    return result


def clean_cell_text(text):
    """셀 텍스트 정규화"""
    if text is None:
        return None
    text = str(text).strip()
    text = ' '.join(text.split())  # 다중 공백 제거
    return text if text else None


def clean_table(table_data):
    """테이블 데이터 정리"""
    if not table_data:
        return table_data

    result = []
    for row in table_data:
        cleaned_row = [clean_cell_text(cell) for cell in row]
        # 모든 셀이 None이면 제외
        if any(cell is not None for cell in cleaned_row):
            result.append(cleaned_row)

    return result


def extract_with_pdfplumber_improved(pdf_path, page_num, table_settings=None):
    """pdfplumber 개선 버전"""
    default_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "snap_x_tolerance": 3,
        "snap_y_tolerance": 3,
        "join_tolerance": 3,
        "edge_min_length": 3,
        "min_words_vertical": 3,
        "min_words_horizontal": 1,
    }

    if table_settings:
        default_settings.update(table_settings)

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]

        # 기본 추출
        tables = page.extract_tables(table_settings=default_settings)

        results = []
        for table in tables:
            cleaned = clean_table(table)
            filled = filldown_none_cells(cleaned)
            results.append(filled)

        return results


def extract_with_pymupdf_improved(pdf_path, page_num):
    """PyMuPDF 개선 버전"""
    doc = fitz.open(pdf_path)
    page = doc[page_num]

    tabs = page.find_tables()
    results = []

    for tab in tabs.tables:
        data = tab.extract()
        cleaned = clean_table(data)
        filled = filldown_none_cells(cleaned)
        results.append(filled)

    doc.close()
    return results


def calculate_detailed_accuracy(extracted, expected):
    """상세 정확도 계산"""
    if not extracted:
        return {'total': 0, 'filled': 0, 'correct': 0, 'accuracy': 0}

    total_cells = sum(len(row) for row in extracted)
    filled_cells = sum(1 for row in extracted for cell in row if cell is not None)

    # 예상 키워드 매칭
    all_text = ' '.join(str(cell) for row in extracted for cell in row if cell).lower()
    keywords = expected.get('sample_content', [])
    matches = sum(1 for kw in keywords if kw.lower() in all_text)

    return {
        'rows': len(extracted),
        'cols': len(extracted[0]) if extracted else 0,
        'total_cells': total_cells,
        'filled_cells': filled_cells,
        'keyword_matches': matches,
        'keyword_total': len(keywords),
        'fill_rate': filled_cells / total_cells if total_cells > 0 else 0,
        'keyword_accuracy': matches / len(keywords) if keywords else 1.0
    }


# 테스트 케이스
VERIFICATION_TABLES = {
    'Table 9.3.2.1': {
        'page': 718,  # 0-indexed
        'expected_rows': 14,
        'expected_cols': 5,
        'sample_content': ['Use', 'Boards', 'Stud', 'Framing', 'Plank', 'No. 2', 'Common'],
    },
    'Table 9.20.3.2.-B': {
        'page': 838,
        'expected_rows': 6,
        'expected_cols': 6,
        'sample_content': ['Mortar Type', 'Portland Cement', 'Lime', 'Sand', 'Masonry'],
        'table_index': 1,  # 두 번째 테이블
    },
    'Table 9.20.5.2.-A': {
        'page': 840,
        'expected_rows': 19,
        'expected_cols': 11,
        'sample_content': ['Clear Span', 'Exterior', 'Interior', 'Angle', 'Floor', 'Load'],
    },
}


def test_improved_methods():
    """개선된 방법 테스트"""
    print("="*70)
    print("개선된 테이블 추출 테스트")
    print("="*70)

    for table_id, info in VERIFICATION_TABLES.items():
        print(f"\n{'='*60}")
        print(f"{table_id}")
        print(f"Expected: {info['expected_rows']} rows x {info['expected_cols']} cols")
        print(f"{'='*60}")

        page_num = info['page']
        table_index = info.get('table_index', 0)

        # pdfplumber 개선
        print("\n[pdfplumber + filldown]")
        tables = extract_with_pdfplumber_improved(PDF_PATH, page_num)
        if table_index < len(tables):
            table = tables[table_index]
            stats = calculate_detailed_accuracy(table, info)
            print(f"  Rows: {stats['rows']}, Cols: {stats['cols']}")
            print(f"  Fill rate: {stats['fill_rate']*100:.1f}%")
            print(f"  Keywords: {stats['keyword_matches']}/{stats['keyword_total']} ({stats['keyword_accuracy']*100:.1f}%)")

            # 처음 5행 출력
            for i, row in enumerate(table[:5]):
                print(f"  Row {i}: {row}")

        # PyMuPDF 개선
        print("\n[PyMuPDF + filldown]")
        tables = extract_with_pymupdf_improved(PDF_PATH, page_num)
        if table_index < len(tables):
            table = tables[table_index]
            stats = calculate_detailed_accuracy(table, info)
            print(f"  Rows: {stats['rows']}, Cols: {stats['cols']}")
            print(f"  Fill rate: {stats['fill_rate']*100:.1f}%")
            print(f"  Keywords: {stats['keyword_matches']}/{stats['keyword_total']} ({stats['keyword_accuracy']*100:.1f}%)")


def test_pdfplumber_settings():
    """pdfplumber 설정 튜닝 테스트"""
    print("\n" + "="*70)
    print("pdfplumber 설정 튜닝 테스트")
    print("="*70)

    # Table 9.20.5.2.-A (가장 복잡한 테이블)
    page_num = 840

    settings_list = [
        {"name": "default", "settings": {}},
        {"name": "text_based", "settings": {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
        }},
        {"name": "explicit", "settings": {
            "vertical_strategy": "explicit",
            "horizontal_strategy": "explicit",
            "explicit_vertical_lines": [],
            "explicit_horizontal_lines": [],
        }},
        {"name": "tight_snap", "settings": {
            "snap_tolerance": 5,
            "join_tolerance": 5,
        }},
    ]

    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[page_num]

        for setting in settings_list:
            print(f"\n[{setting['name']}]")
            try:
                tables = page.extract_tables(table_settings=setting['settings'] if setting['settings'] else None)
                for i, table in enumerate(tables):
                    if table:
                        print(f"  Table {i}: {len(table)} rows x {len(table[0]) if table else 0} cols")
            except Exception as e:
                print(f"  Error: {e}")


if __name__ == "__main__":
    test_improved_methods()
    test_pdfplumber_settings()
