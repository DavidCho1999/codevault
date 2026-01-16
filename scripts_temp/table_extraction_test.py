"""
테이블 추출 방법론 비교 테스트
목표: Part 9 테이블 추출 정확도 98%+ 달성

테스트 방법:
1. pdfplumber
2. Camelot (stream/lattice)
3. PyMuPDF (fitz)
4. 좌표 기반 재구성
5. 앙상블
"""

import sys
import json
import os
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'
OUTPUT_DIR = './extraction_test_results'

# 검증 테이블 정보 (정확한 페이지와 예상 구조)
VERIFICATION_TABLES = {
    'Table 9.3.2.1': {
        'page': 719,  # 0-indexed: 718
        'expected_rows': 14,
        'expected_cols': 5,
        'title': 'Minimum Lumber Grades for Specific End Uses',
        'sample_content': ['Use', 'Boards', 'Stud', 'Joist', 'Rafter', 'Plank', 'No. 1'],
    },
    'Table 9.20.3.2.-A': {
        'page': 839,  # 0-indexed: 838
        'expected_rows': 7,
        'expected_cols': 3,
        'title': 'Mortar Types for Masonry',
        'sample_content': ['Location', 'Building Element', 'Mortar Type', 'Loadbearing'],
    },
    'Table 9.20.3.2.-B': {
        'page': 839,
        'expected_rows': 6,
        'expected_cols': 6,
        'title': 'Mortar Proportions by Volume',
        'sample_content': ['Mortar Type', 'Portland Cement', 'Lime', 'Sand'],
    },
    'Table 9.23.3.1': {
        'page': 866,
        'expected_rows': 6,
        'expected_cols': 2,
        'title': 'Common Wire Nails',
        'sample_content': ['Minimum Length', 'Diameter', 'mm', '51', '57', '63'],
    },
    'Table 9.23.3.5.-A': {
        'page': 868,
        'expected_rows': 9,
        'expected_cols': 6,
        'title': 'Fasteners for Sheathing and Subflooring',
        'sample_content': ['Element', 'Fastener', 'Spacing', 'nail', 'screw'],
    },
    'Table 9.20.5.2.-A': {
        'page': 841,
        'expected_rows': 19,
        'expected_cols': 11,
        'title': 'Loose Steel Lintels for Masonry',
        'sample_content': ['Clear Span', 'Exterior', 'Interior', 'Angle', 'mm'],
    },
    'Table 9.20.5.2.-B': {
        'page': 842,
        'expected_rows': 13,
        'expected_cols': 6,
        'title': 'Maximum Allowable Spans for Steel Lintels',
        'sample_content': ['Angle Size', 'Span', 'mm'],
    },
}


def calculate_accuracy(extracted_data, expected_info):
    """추출 정확도 계산"""
    if not extracted_data:
        return {'found': False, 'row_accuracy': 0, 'col_accuracy': 0, 'content_score': 0, 'overall': 0}

    # 행/열 정확도
    actual_rows = len(extracted_data)
    actual_cols = max(len(row) for row in extracted_data) if extracted_data else 0

    expected_rows = expected_info['expected_rows']
    expected_cols = expected_info['expected_cols']

    row_accuracy = min(actual_rows, expected_rows) / max(actual_rows, expected_rows) if max(actual_rows, expected_rows) > 0 else 0
    col_accuracy = min(actual_cols, expected_cols) / max(actual_cols, expected_cols) if max(actual_cols, expected_cols) > 0 else 0

    # 내용 점수 (샘플 키워드 매칭)
    all_text = ' '.join(str(cell) for row in extracted_data for cell in row if cell).lower()
    sample_content = expected_info.get('sample_content', [])
    content_matches = sum(1 for keyword in sample_content if keyword.lower() in all_text)
    content_score = content_matches / len(sample_content) if sample_content else 1.0

    # 종합 점수
    overall = (row_accuracy * 0.3 + col_accuracy * 0.3 + content_score * 0.4)

    return {
        'found': True,
        'actual_rows': actual_rows,
        'actual_cols': actual_cols,
        'row_accuracy': round(row_accuracy, 3),
        'col_accuracy': round(col_accuracy, 3),
        'content_score': round(content_score, 3),
        'overall': round(overall, 3)
    }


# ============================================
# Method 1: pdfplumber
# ============================================
def test_pdfplumber():
    """pdfplumber로 테이블 추출 테스트"""
    import pdfplumber

    print("\n" + "="*60)
    print("Method 1: pdfplumber")
    print("="*60)

    results = {}

    with pdfplumber.open(PDF_PATH) as pdf:
        for table_id, info in VERIFICATION_TABLES.items():
            page_num = info['page'] - 1  # 0-indexed
            page = pdf.pages[page_num]

            # 테이블 추출 시도
            tables = page.extract_tables()

            best_table = None
            best_score = 0

            for tab in tables:
                if not tab:
                    continue
                score = calculate_accuracy(tab, info)
                if score['overall'] > best_score:
                    best_score = score['overall']
                    best_table = tab

            accuracy = calculate_accuracy(best_table, info)
            results[table_id] = {
                'accuracy': accuracy,
                'data': best_table[:3] if best_table else None  # 샘플 데이터
            }

            status = '✓' if accuracy['overall'] >= 0.8 else '△' if accuracy['overall'] >= 0.5 else '✗'
            print(f"  {status} {table_id}: {accuracy['overall']*100:.1f}% "
                  f"(rows: {accuracy.get('actual_rows', 0)}/{info['expected_rows']}, "
                  f"cols: {accuracy.get('actual_cols', 0)}/{info['expected_cols']})")

    avg_accuracy = sum(r['accuracy']['overall'] for r in results.values()) / len(results) if results else 0
    print(f"\n  Average accuracy: {avg_accuracy*100:.1f}%")

    return {'method': 'pdfplumber', 'results': results, 'average': avg_accuracy}


# ============================================
# Method 2: Camelot (lattice mode)
# ============================================
def test_camelot_lattice():
    """Camelot lattice 모드 테스트"""
    try:
        import camelot
    except ImportError:
        print("\n  Camelot not available")
        return {'method': 'camelot_lattice', 'results': {}, 'average': 0, 'error': 'import failed'}

    print("\n" + "="*60)
    print("Method 2: Camelot (lattice mode)")
    print("="*60)

    results = {}

    for table_id, info in VERIFICATION_TABLES.items():
        page_num = info['page']

        try:
            tables = camelot.read_pdf(PDF_PATH, pages=str(page_num), flavor='lattice')

            best_table = None
            best_score = 0

            for tab in tables:
                data = tab.df.values.tolist()
                score = calculate_accuracy(data, info)
                if score['overall'] > best_score:
                    best_score = score['overall']
                    best_table = data

            accuracy = calculate_accuracy(best_table, info)
            results[table_id] = {
                'accuracy': accuracy,
                'data': best_table[:3] if best_table else None
            }

            status = '✓' if accuracy['overall'] >= 0.8 else '△' if accuracy['overall'] >= 0.5 else '✗'
            print(f"  {status} {table_id}: {accuracy['overall']*100:.1f}%")

        except Exception as e:
            results[table_id] = {
                'accuracy': {'found': False, 'overall': 0},
                'error': str(e)[:50]
            }
            print(f"  ✗ {table_id}: Error - {str(e)[:30]}")

    avg_accuracy = sum(r['accuracy']['overall'] for r in results.values()) / len(results) if results else 0
    print(f"\n  Average accuracy: {avg_accuracy*100:.1f}%")

    return {'method': 'camelot_lattice', 'results': results, 'average': avg_accuracy}


# ============================================
# Method 3: Camelot (stream mode)
# ============================================
def test_camelot_stream():
    """Camelot stream 모드 테스트"""
    try:
        import camelot
    except ImportError:
        print("\n  Camelot not available")
        return {'method': 'camelot_stream', 'results': {}, 'average': 0}

    print("\n" + "="*60)
    print("Method 3: Camelot (stream mode)")
    print("="*60)

    results = {}

    for table_id, info in VERIFICATION_TABLES.items():
        page_num = info['page']

        try:
            tables = camelot.read_pdf(PDF_PATH, pages=str(page_num), flavor='stream')

            best_table = None
            best_score = 0

            for tab in tables:
                data = tab.df.values.tolist()
                score = calculate_accuracy(data, info)
                if score['overall'] > best_score:
                    best_score = score['overall']
                    best_table = data

            accuracy = calculate_accuracy(best_table, info)
            results[table_id] = {
                'accuracy': accuracy,
                'data': best_table[:3] if best_table else None
            }

            status = '✓' if accuracy['overall'] >= 0.8 else '△' if accuracy['overall'] >= 0.5 else '✗'
            print(f"  {status} {table_id}: {accuracy['overall']*100:.1f}%")

        except Exception as e:
            results[table_id] = {
                'accuracy': {'found': False, 'overall': 0},
                'error': str(e)[:50]
            }
            print(f"  ✗ {table_id}: Error - {str(e)[:30]}")

    avg_accuracy = sum(r['accuracy']['overall'] for r in results.values()) / len(results) if results else 0
    print(f"\n  Average accuracy: {avg_accuracy*100:.1f}%")

    return {'method': 'camelot_stream', 'results': results, 'average': avg_accuracy}


# ============================================
# Method 4: PyMuPDF (fitz)
# ============================================
def test_pymupdf():
    """PyMuPDF로 테이블 추출 테스트"""
    import fitz

    print("\n" + "="*60)
    print("Method 4: PyMuPDF (fitz)")
    print("="*60)

    results = {}
    doc = fitz.open(PDF_PATH)

    for table_id, info in VERIFICATION_TABLES.items():
        page_num = info['page'] - 1  # 0-indexed
        page = doc[page_num]

        tabs = page.find_tables()

        best_table = None
        best_score = 0

        for tab in tabs.tables:
            data = tab.extract()
            score = calculate_accuracy(data, info)
            if score['overall'] > best_score:
                best_score = score['overall']
                best_table = data

        accuracy = calculate_accuracy(best_table, info)
        results[table_id] = {
            'accuracy': accuracy,
            'data': best_table[:3] if best_table else None
        }

        status = '✓' if accuracy['overall'] >= 0.8 else '△' if accuracy['overall'] >= 0.5 else '✗'
        print(f"  {status} {table_id}: {accuracy['overall']*100:.1f}% "
              f"(rows: {accuracy.get('actual_rows', 0)}/{info['expected_rows']}, "
              f"cols: {accuracy.get('actual_cols', 0)}/{info['expected_cols']})")

    doc.close()

    avg_accuracy = sum(r['accuracy']['overall'] for r in results.values()) / len(results) if results else 0
    print(f"\n  Average accuracy: {avg_accuracy*100:.1f}%")

    return {'method': 'pymupdf', 'results': results, 'average': avg_accuracy}


# ============================================
# Method 5: 좌표 기반 재구성 (PyMuPDF blocks)
# ============================================
def test_coordinate_based():
    """좌표 기반 테이블 재구성"""
    import fitz

    print("\n" + "="*60)
    print("Method 5: Coordinate-based reconstruction")
    print("="*60)

    results = {}
    doc = fitz.open(PDF_PATH)

    for table_id, info in VERIFICATION_TABLES.items():
        page_num = info['page'] - 1
        page = doc[page_num]

        # 테이블 영역 찾기 (fitz의 find_tables로)
        tabs = page.find_tables()
        if not tabs.tables:
            results[table_id] = {'accuracy': {'found': False, 'overall': 0}}
            print(f"  ✗ {table_id}: No tables found")
            continue

        # 가장 적합한 테이블 선택
        best_tab = None
        best_score = 0

        for tab in tabs.tables:
            # 테이블 영역의 텍스트 블록 추출
            bbox = tab.bbox
            blocks = page.get_text("dict", clip=bbox)['blocks']

            # 텍스트 블록을 그리드로 재구성
            text_items = []
            for block in blocks:
                if 'lines' in block:
                    for line in block['lines']:
                        for span in line['spans']:
                            x0 = span['bbox'][0]
                            y0 = span['bbox'][1]
                            text = span['text'].strip()
                            if text:
                                text_items.append((y0, x0, text))

            # y좌표로 행 그룹화
            if not text_items:
                continue

            text_items.sort(key=lambda x: (x[0], x[1]))

            rows = []
            current_row = []
            current_y = text_items[0][0]

            for y, x, text in text_items:
                if abs(y - current_y) > 5:  # 새 행
                    if current_row:
                        current_row.sort(key=lambda x: x[0])
                        rows.append([t for _, t in current_row])
                    current_row = [(x, text)]
                    current_y = y
                else:
                    current_row.append((x, text))

            if current_row:
                current_row.sort(key=lambda x: x[0])
                rows.append([t for _, t in current_row])

            score = calculate_accuracy(rows, info)
            if score['overall'] > best_score:
                best_score = score['overall']
                best_tab = rows

        accuracy = calculate_accuracy(best_tab, info)
        results[table_id] = {
            'accuracy': accuracy,
            'data': best_tab[:3] if best_tab else None
        }

        status = '✓' if accuracy['overall'] >= 0.8 else '△' if accuracy['overall'] >= 0.5 else '✗'
        print(f"  {status} {table_id}: {accuracy['overall']*100:.1f}%")

    doc.close()

    avg_accuracy = sum(r['accuracy']['overall'] for r in results.values()) / len(results) if results else 0
    print(f"\n  Average accuracy: {avg_accuracy*100:.1f}%")

    return {'method': 'coordinate_based', 'results': results, 'average': avg_accuracy}


# ============================================
# Method 6: 앙상블 (최고 결과 선택)
# ============================================
def test_ensemble(all_results):
    """앙상블: 각 테이블별로 최고 결과 선택"""
    print("\n" + "="*60)
    print("Method 6: Ensemble (best of all methods)")
    print("="*60)

    ensemble_results = {}

    for table_id in VERIFICATION_TABLES.keys():
        best_method = None
        best_accuracy = {'overall': 0}

        for method_result in all_results:
            if table_id in method_result['results']:
                acc = method_result['results'][table_id]['accuracy']
                if acc['overall'] > best_accuracy['overall']:
                    best_accuracy = acc
                    best_method = method_result['method']

        ensemble_results[table_id] = {
            'accuracy': best_accuracy,
            'best_method': best_method
        }

        status = '✓' if best_accuracy['overall'] >= 0.8 else '△' if best_accuracy['overall'] >= 0.5 else '✗'
        print(f"  {status} {table_id}: {best_accuracy['overall']*100:.1f}% (best: {best_method})")

    avg_accuracy = sum(r['accuracy']['overall'] for r in ensemble_results.values()) / len(ensemble_results)
    print(f"\n  Average accuracy: {avg_accuracy*100:.1f}%")

    return {'method': 'ensemble', 'results': ensemble_results, 'average': avg_accuracy}


def main():
    """메인 테스트 실행"""
    print("="*60)
    print("Table Extraction Method Comparison Test")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_results = []

    # 각 방법 테스트
    try:
        all_results.append(test_pdfplumber())
    except Exception as e:
        print(f"  pdfplumber error: {e}")

    try:
        all_results.append(test_camelot_lattice())
    except Exception as e:
        print(f"  camelot_lattice error: {e}")

    try:
        all_results.append(test_camelot_stream())
    except Exception as e:
        print(f"  camelot_stream error: {e}")

    try:
        all_results.append(test_pymupdf())
    except Exception as e:
        print(f"  pymupdf error: {e}")

    try:
        all_results.append(test_coordinate_based())
    except Exception as e:
        print(f"  coordinate_based error: {e}")

    # 앙상블
    if all_results:
        ensemble = test_ensemble(all_results)
        all_results.append(ensemble)

    # 결과 요약
    print("\n" + "="*60)
    print("SUMMARY - Method Comparison")
    print("="*60)
    print(f"{'Method':<25} {'Avg Accuracy':>15}")
    print("-"*40)

    for result in sorted(all_results, key=lambda x: x['average'], reverse=True):
        print(f"{result['method']:<25} {result['average']*100:>14.1f}%")

    # 결과 저장
    output_path = os.path.join(OUTPUT_DIR, f'comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')

    # 데이터 필드 제거 (크기 줄이기)
    save_results = []
    for r in all_results:
        save_r = {'method': r['method'], 'average': r['average'], 'results': {}}
        for table_id, data in r['results'].items():
            save_r['results'][table_id] = {
                'accuracy': data.get('accuracy', {}),
                'best_method': data.get('best_method', None)
            }
        save_results.append(save_r)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(save_results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_path}")
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
