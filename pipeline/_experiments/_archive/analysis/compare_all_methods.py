"""
PDF 테이블 추출: 모든 방법 비교 테스트
- Method A: pdfplumber (개선판)
- Method B: Camelot (lattice + stream)
- Method C: PyMuPDF 네이티브
- Method D: tabula-py

각 방법으로 동일한 테이블을 추출하고 품질 비교
"""

import sys
import os
import json
import time
from copy import deepcopy

sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'

# 테스트할 테이블 (다양한 복잡도)
TEST_TABLES = [
    {'name': 'Table 9.3.1.7', 'page': 718, 'expected_rows': 7, 'expected_cols': 7},
    {'name': 'Table 9.4.3.1', 'page': 724, 'expected_rows': 9, 'expected_cols': 3},
    {'name': 'Table 9.3.2.1', 'page': 719, 'expected_rows': 14, 'expected_cols': 5},
    {'name': 'Table 9.9.1.1-A', 'page': 746, 'expected_rows': 10, 'expected_cols': 5},  # 감지 실패했던 것
]


def get_pdf_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(script_dir, PDF_PATH))


# ============================================================
# Method A: pdfplumber 개선판
# ============================================================
def method_a_pdfplumber(pdf_path, page_num):
    """pdfplumber + filldown + 다중 설정 시도"""
    import pdfplumber

    results = {'method': 'pdfplumber', 'tables': [], 'error': None}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_num - 1]

            # 여러 설정 시도
            settings_list = [
                {},  # 기본
                {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
                {"vertical_strategy": "lines", "horizontal_strategy": "text"},
                {"snap_tolerance": 5, "join_tolerance": 5},
            ]

            best_table = None
            best_score = -1

            for settings in settings_list:
                try:
                    tables = page.extract_tables(settings) if settings else page.extract_tables()
                    if tables:
                        for table in tables:
                            if table and len(table) > 1:
                                # 품질 점수: NULL이 적을수록 좋음
                                null_count = sum(1 for row in table for c in row if c is None)
                                total = len(table) * len(table[0])
                                score = 1 - (null_count / total) if total > 0 else 0

                                if score > best_score:
                                    best_score = score
                                    best_table = table
                except:
                    continue

            if best_table:
                # filldown 적용
                filled = filldown_cells(best_table)
                results['tables'].append({
                    'rows': len(filled),
                    'cols': len(filled[0]) if filled else 0,
                    'null_pct': calculate_null_pct(filled),
                    'data': filled[:5],  # 처음 5행만
                    'quality_score': best_score
                })
    except Exception as e:
        results['error'] = str(e)

    return results


# ============================================================
# Method B: Camelot
# ============================================================
def method_b_camelot(pdf_path, page_num):
    """Camelot lattice + stream"""
    results = {'method': 'camelot', 'tables': [], 'error': None}

    try:
        import camelot

        # Lattice (선 기반) 시도
        try:
            tables = camelot.read_pdf(pdf_path, pages=str(page_num), flavor='lattice')
            if tables:
                for table in tables:
                    df = table.df
                    data = df.values.tolist()
                    results['tables'].append({
                        'flavor': 'lattice',
                        'rows': len(data),
                        'cols': len(data[0]) if data else 0,
                        'null_pct': calculate_null_pct(data),
                        'accuracy': table.accuracy if hasattr(table, 'accuracy') else 0,
                        'data': data[:5]
                    })
        except Exception as e:
            results['lattice_error'] = str(e)[:100]

        # Stream (텍스트 기반) 시도
        try:
            tables = camelot.read_pdf(pdf_path, pages=str(page_num), flavor='stream')
            if tables:
                for table in tables:
                    df = table.df
                    data = df.values.tolist()
                    results['tables'].append({
                        'flavor': 'stream',
                        'rows': len(data),
                        'cols': len(data[0]) if data else 0,
                        'null_pct': calculate_null_pct(data),
                        'accuracy': table.accuracy if hasattr(table, 'accuracy') else 0,
                        'data': data[:5]
                    })
        except Exception as e:
            results['stream_error'] = str(e)[:100]

    except ImportError:
        results['error'] = 'Camelot not installed'
    except Exception as e:
        results['error'] = str(e)[:100]

    return results


# ============================================================
# Method C: PyMuPDF 네이티브
# ============================================================
def method_c_pymupdf(pdf_path, page_num):
    """PyMuPDF 내장 테이블 추출"""
    import fitz

    results = {'method': 'pymupdf', 'tables': [], 'error': None}

    try:
        doc = fitz.open(pdf_path)
        page = doc[page_num - 1]

        # PyMuPDF 테이블 추출
        tabs = page.find_tables()

        for tab in tabs.tables:
            data = tab.extract()
            if data:
                results['tables'].append({
                    'rows': len(data),
                    'cols': len(data[0]) if data else 0,
                    'null_pct': calculate_null_pct(data),
                    'bbox': tab.bbox,
                    'data': data[:5]
                })

        doc.close()
    except Exception as e:
        results['error'] = str(e)

    return results


# ============================================================
# Method D: tabula-py
# ============================================================
def method_d_tabula(pdf_path, page_num):
    """tabula-py (Java 기반)"""
    results = {'method': 'tabula', 'tables': [], 'error': None}

    try:
        import tabula

        # lattice 모드
        try:
            tables = tabula.read_pdf(pdf_path, pages=page_num, lattice=True)
            for df in tables:
                data = df.values.tolist()
                results['tables'].append({
                    'mode': 'lattice',
                    'rows': len(data),
                    'cols': len(data[0]) if data else 0,
                    'null_pct': calculate_null_pct(data),
                    'data': data[:5]
                })
        except:
            pass

        # stream 모드
        try:
            tables = tabula.read_pdf(pdf_path, pages=page_num, stream=True)
            for df in tables:
                data = df.values.tolist()
                results['tables'].append({
                    'mode': 'stream',
                    'rows': len(data),
                    'cols': len(data[0]) if data else 0,
                    'null_pct': calculate_null_pct(data),
                    'data': data[:5]
                })
        except:
            pass

    except ImportError:
        results['error'] = 'tabula-py not installed'
    except Exception as e:
        results['error'] = str(e)[:100]

    return results


# ============================================================
# 유틸리티 함수
# ============================================================
def filldown_cells(table):
    """병합 셀 처리: None을 위의 값으로 채움"""
    if not table:
        return table

    result = deepcopy(table)
    cols = len(result[0]) if result else 0

    for col in range(cols):
        last_value = None
        for row in range(len(result)):
            cell = result[row][col]
            if cell is None or (isinstance(cell, str) and cell.strip() == ''):
                result[row][col] = last_value
            else:
                last_value = cell

    return result


def calculate_null_pct(table):
    """NULL/빈 셀 비율 계산"""
    if not table:
        return 100.0

    total = sum(len(row) for row in table)
    if total == 0:
        return 100.0

    null_count = 0
    for row in table:
        for cell in row:
            if cell is None or (isinstance(cell, str) and cell.strip() == ''):
                null_count += 1
            # pandas NaN 체크
            try:
                import pandas as pd
                if pd.isna(cell):
                    null_count += 1
            except:
                pass

    return round(null_count / total * 100, 1)


def score_result(result, expected_rows, expected_cols):
    """결과 품질 점수 계산 (0-100)"""
    if result.get('error') or not result.get('tables'):
        return 0

    best_score = 0
    for table in result['tables']:
        score = 0

        # 행/열 일치도 (40점)
        row_diff = abs(table['rows'] - expected_rows)
        col_diff = abs(table['cols'] - expected_cols)

        row_score = max(0, 20 - row_diff * 5)
        col_score = max(0, 20 - col_diff * 5)
        score += row_score + col_score

        # NULL 비율 (60점)
        null_pct = table.get('null_pct', 100)
        null_score = max(0, 60 - null_pct)
        score += null_score

        best_score = max(best_score, score)

    return best_score


# ============================================================
# 메인 비교 함수
# ============================================================
def run_comparison():
    pdf_path = get_pdf_path()

    print("=" * 80)
    print("🔬 PDF 테이블 추출 방법 비교 테스트")
    print("=" * 80)
    print(f"PDF: {pdf_path}\n")

    all_results = {}
    method_scores = {'pdfplumber': 0, 'camelot': 0, 'pymupdf': 0, 'tabula': 0}

    for test in TEST_TABLES:
        table_name = test['name']
        page_num = test['page']
        expected_rows = test['expected_rows']
        expected_cols = test['expected_cols']

        print(f"\n{'#' * 80}")
        print(f"📊 {table_name} (페이지 {page_num})")
        print(f"   예상: {expected_rows}행 x {expected_cols}열")
        print(f"{'#' * 80}")

        results = {}

        # Method A: pdfplumber
        print("\n▶ Method A: pdfplumber...", end=" ")
        start = time.time()
        results['pdfplumber'] = method_a_pdfplumber(pdf_path, page_num)
        elapsed_a = time.time() - start
        score_a = score_result(results['pdfplumber'], expected_rows, expected_cols)
        method_scores['pdfplumber'] += score_a
        print(f"완료 ({elapsed_a:.2f}s) - 점수: {score_a}")

        # Method B: Camelot
        print("▶ Method B: Camelot...", end=" ")
        start = time.time()
        results['camelot'] = method_b_camelot(pdf_path, page_num)
        elapsed_b = time.time() - start
        score_b = score_result(results['camelot'], expected_rows, expected_cols)
        method_scores['camelot'] += score_b
        print(f"완료 ({elapsed_b:.2f}s) - 점수: {score_b}")

        # Method C: PyMuPDF
        print("▶ Method C: PyMuPDF...", end=" ")
        start = time.time()
        results['pymupdf'] = method_c_pymupdf(pdf_path, page_num)
        elapsed_c = time.time() - start
        score_c = score_result(results['pymupdf'], expected_rows, expected_cols)
        method_scores['pymupdf'] += score_c
        print(f"완료 ({elapsed_c:.2f}s) - 점수: {score_c}")

        # Method D: tabula-py
        print("▶ Method D: tabula-py...", end=" ")
        start = time.time()
        results['tabula'] = method_d_tabula(pdf_path, page_num)
        elapsed_d = time.time() - start
        score_d = score_result(results['tabula'], expected_rows, expected_cols)
        method_scores['tabula'] += score_d
        print(f"완료 ({elapsed_d:.2f}s) - 점수: {score_d}")

        # 상세 결과
        print(f"\n  결과 요약:")
        for method, result in results.items():
            if result.get('error'):
                print(f"    {method}: ❌ {result['error'][:50]}")
            elif result.get('tables'):
                t = result['tables'][0]
                print(f"    {method}: {t['rows']}x{t['cols']}, NULL {t.get('null_pct', '?')}%")
            else:
                print(f"    {method}: 테이블 없음")

        all_results[table_name] = results

    # 최종 점수
    print("\n\n" + "=" * 80)
    print("📋 최종 점수 (전체 테이블 합산)")
    print("=" * 80)

    max_possible = len(TEST_TABLES) * 100

    sorted_methods = sorted(method_scores.items(), key=lambda x: x[1], reverse=True)

    for i, (method, score) in enumerate(sorted_methods):
        bar = "█" * int(score / max_possible * 40)
        pct = score / max_possible * 100
        rank = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "  "
        print(f"{rank} {method:12} {bar:40} {score}/{max_possible} ({pct:.1f}%)")

    winner = sorted_methods[0][0]
    print(f"\n✅ 권장 방법: {winner.upper()}")

    # 결과 저장
    output_path = os.path.join(os.path.dirname(__file__), 'comparison_results.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'method_scores': method_scores,
            'winner': winner,
            'details': {k: {m: {'error': r.get('error'), 'tables_count': len(r.get('tables', []))}
                           for m, r in v.items()}
                       for k, v in all_results.items()}
        }, f, indent=2, ensure_ascii=False)

    print(f"\n결과 저장: {output_path}")

    return winner, method_scores


if __name__ == "__main__":
    run_comparison()
