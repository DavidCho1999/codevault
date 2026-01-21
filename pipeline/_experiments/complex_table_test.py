"""
복잡한 테이블 상세 테스트 - 9.3.2.1, 9.20.5.2.-A
"""
import sys
import pdfplumber
import fitz
from copy import deepcopy
sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'

def filldown_none_cells(table_data):
    """None 셀을 위의 값으로 채우기"""
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

def normalize(text):
    if text is None:
        return ''
    return ' '.join(str(text).strip().split()).lower()

def test_table_9_3_2_1():
    """Table 9.3.2.1 상세 테스트"""
    print("="*70)
    print("Table 9.3.2.1 - Minimum Lumber Grades for Specific End Uses")
    print("="*70)

    # Ground Truth (PDF p.719에서 수동 확인)
    # 헤더가 복잡 (4행), 데이터 10행
    GROUND_TRUTH_DATA_ROWS = [
        ['Stud wall framing (loadbearing members)', '—', '—', '—', 'Stud, Standard, No. 2'],
        ['Stud wall framing (non-loadbearing members)', '—', '—', '—', 'Stud, Utility, No. 3'],
        ['Plank frame construction (loadbearing members)', 'No. 3 Common', '—', 'No. 3 Common', 'No. 2'],
        ['Plank frame construction (non-loadbearing members)', 'No. 5 Common', '—', 'No. 5 Common', 'Economy, No. 3'],
        ['Post and beams less than 114 mm in thickness', '—', '—', '—', 'Standard, No.2'],
        ['Post and beams not less than 114 mm in thickness', '—', '—', '—', 'Standard'],
        ['Roof sheathing', 'No. 3 Common', 'Standard', 'No. 4 Common', '—'],
        ['Subflooring', 'No. 3 Common', 'Standard', 'No. 3 Common', '—'],
        ['Wall sheathing when required as a nailing base', 'No. 4 Common', 'Utility', 'No. 4 Common', '—'],
        ['Wall sheathing not required as a nailing base', 'No. 5 Common', 'Economy', 'No. 5 Common', '—'],
    ]

    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[718]
        tables = page.extract_tables()

        if tables:
            table = filldown_none_cells(tables[0])

            # 데이터 행 추출 (헤더 4행 건너뛰기)
            data_rows = table[4:] if len(table) > 4 else table

            print(f"\n추출된 데이터 행: {len(data_rows)}")
            print(f"예상 데이터 행: {len(GROUND_TRUTH_DATA_ROWS)}")

            # 셀 단위 비교
            matched = 0
            total = 0

            for row_idx, (ext_row, gt_row) in enumerate(zip(data_rows, GROUND_TRUTH_DATA_ROWS)):
                for col_idx in range(min(len(ext_row), len(gt_row))):
                    total += 1
                    ext_val = normalize(ext_row[col_idx])
                    gt_val = normalize(gt_row[col_idx])

                    if ext_val == gt_val:
                        matched += 1
                    elif ext_val in gt_val or gt_val in ext_val:
                        matched += 0.8  # 부분 매칭
                        print(f"  Partial [{row_idx},{col_idx}]: '{ext_val[:30]}' vs '{gt_val[:30]}'")
                    else:
                        print(f"  Mismatch [{row_idx},{col_idx}]: '{ext_val[:30]}' vs '{gt_val[:30]}'")

            accuracy = matched / total if total > 0 else 0
            print(f"\n정확도: {accuracy*100:.1f}% ({matched}/{total})")
            return accuracy

    return 0

def test_table_9_20_5_2_A():
    """Table 9.20.5.2.-A 상세 테스트"""
    print("\n" + "="*70)
    print("Table 9.20.5.2.-A - Loose Steel Lintels for Masonry")
    print("="*70)

    # 이 테이블은 매우 복잡함 (19x11, 다중 헤더, 많은 병합 셀)
    # 핵심 데이터만 검증

    # 핵심 데이터 포인트 (스팟 체크)
    SPOT_CHECKS = [
        {'row': 4, 'col': 0, 'expected': 'No Floor Load'},  # 또는 포함
        {'row': 17, 'col': 0, 'expected': '3.0 m'},
        {'row': 17, 'col': 1, 'expected': 'L-152'},  # 포함
    ]

    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[840]
        tables = page.extract_tables()

        if tables:
            table = filldown_none_cells(tables[0])

            print(f"테이블 크기: {len(table)} rows x {len(table[0]) if table else 0} cols")

            # 스팟 체크
            passed = 0
            for check in SPOT_CHECKS:
                row = check['row']
                col = check['col']
                expected = check['expected'].lower()

                if row < len(table) and col < len(table[row]):
                    actual = normalize(table[row][col])
                    if expected in actual:
                        passed += 1
                        print(f"  ✓ [{row},{col}]: '{actual[:40]}' contains '{expected}'")
                    else:
                        print(f"  ✗ [{row},{col}]: '{actual[:40]}' does NOT contain '{expected}'")
                else:
                    print(f"  ✗ [{row},{col}]: Out of range")

            spot_accuracy = passed / len(SPOT_CHECKS) if SPOT_CHECKS else 0
            print(f"\n스팟 체크 정확도: {spot_accuracy*100:.1f}%")

            # 전체 셀 채움률
            filled = sum(1 for row in table for cell in row if cell and str(cell).strip())
            total = sum(len(row) for row in table)
            fill_rate = filled / total if total > 0 else 0
            print(f"셀 채움률: {fill_rate*100:.1f}%")

            return spot_accuracy

    return 0

def comprehensive_accuracy_test():
    """종합 정확도 테스트"""
    print("\n" + "="*70)
    print("종합 정확도 테스트 - pdfplumber + filldown")
    print("="*70)

    # 모든 검증 테이블에 대해 테스트
    test_tables = [
        {'name': 'Table 9.23.3.1', 'page': 865, 'rows': 6, 'cols': 2},
        {'name': 'Table 9.20.3.2.-A', 'page': 838, 'rows': 7, 'cols': 3, 'index': 0},
        {'name': 'Table 9.20.3.2.-B', 'page': 838, 'rows': 6, 'cols': 6, 'index': 1},
        {'name': 'Table 9.3.2.1', 'page': 718, 'rows': 14, 'cols': 5},
        {'name': 'Table 9.23.3.5.-A', 'page': 867, 'rows': 9, 'cols': 6},
        {'name': 'Table 9.20.5.2.-A', 'page': 840, 'rows': 19, 'cols': 11},
        {'name': 'Table 9.20.5.2.-B', 'page': 841, 'rows': 13, 'cols': 6},
    ]

    results = []

    with pdfplumber.open(PDF_PATH) as pdf:
        for tc in test_tables:
            page = pdf.pages[tc['page']]
            tables = page.extract_tables()

            table_index = tc.get('index', 0)
            if table_index < len(tables):
                table = filldown_none_cells(tables[table_index])
                actual_rows = len(table)
                actual_cols = len(table[0]) if table else 0

                # 구조 정확도
                row_acc = min(actual_rows, tc['rows']) / max(actual_rows, tc['rows'])
                col_acc = min(actual_cols, tc['cols']) / max(actual_cols, tc['cols'])

                # 셀 채움률
                filled = sum(1 for row in table for cell in row if cell and str(cell).strip())
                total = sum(len(row) for row in table)
                fill_rate = filled / total if total > 0 else 0

                # 종합 점수
                score = (row_acc * 0.3 + col_acc * 0.3 + fill_rate * 0.4)

                status = '✓' if score >= 0.9 else '△' if score >= 0.7 else '✗'
                print(f"{status} {tc['name']}: {score*100:.1f}% "
                      f"(rows: {actual_rows}/{tc['rows']}, cols: {actual_cols}/{tc['cols']}, fill: {fill_rate*100:.0f}%)")

                results.append({'name': tc['name'], 'score': score})
            else:
                print(f"✗ {tc['name']}: Not found")
                results.append({'name': tc['name'], 'score': 0})

    avg = sum(r['score'] for r in results) / len(results)
    print(f"\n평균 점수: {avg*100:.1f}%")
    return avg

if __name__ == "__main__":
    acc1 = test_table_9_3_2_1()
    acc2 = test_table_9_20_5_2_A()
    avg = comprehensive_accuracy_test()

    print("\n" + "="*70)
    print("최종 결과 요약")
    print("="*70)
    print(f"Table 9.3.2.1 데이터 정확도: {acc1*100:.1f}%")
    print(f"Table 9.20.5.2.-A 스팟 체크: {acc2*100:.1f}%")
    print(f"종합 구조 점수: {avg*100:.1f}%")
