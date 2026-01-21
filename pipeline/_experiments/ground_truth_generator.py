"""
Ground Truth 생성 및 셀 단위 정확도 검증
수동으로 검증된 데이터와 비교
"""
import sys
import json
import pdfplumber
import fitz
from copy import deepcopy
sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'
OUTPUT_DIR = './extraction_test_results'

# Ground Truth 데이터 (PDF에서 수동 확인)
GROUND_TRUTH = {
    'Table 9.23.3.1': {
        'page': 866,
        'page_index': 865,
        'description': 'Diameter of Nails',
        'data': [
            ['Minimum Length of Nails, mm', 'Minimum Diameter of Nails, mm'],
            ['57', '2.87'],
            ['63', '3.25'],
            ['76', '3.66'],
            ['82', '3.66'],
            ['101 or greater', '4.88'],
        ]
    },
    'Table 9.20.3.2.-A': {
        'page': 839,
        'page_index': 838,
        'table_index': 0,
        'description': 'Mortar Types for Masonry',
        'data': [
            ['Location', 'Building Element', 'Mortar Type'],
            ['Exterior, Above Ground', 'Loadbearing walls and columns', 'S'],
            ['Exterior, Above Ground', 'Non-loadbearing walls and columns', 'N or S'],
            ['Exterior, Above Ground', 'Parapets, chimneys and masonry veneer', 'N or S'],
            ['Exterior, At or Below Ground', 'Foundation walls and chimneys', 'S'],
            ['Interior', 'Loadbearing walls and columns', 'N'],
            ['Interior', 'Non-loadbearing walls and columns', 'N'],
        ]
    },
    'Table 9.20.3.2.-B': {
        'page': 839,
        'page_index': 838,
        'table_index': 1,
        'description': 'Mortar Proportions by Volume',
        'data': [
            ['Mortar Type', 'Portland Cement', 'Lime', 'Masonry Cement Type N', 'Masonry Cement Type S', 'Fine Aggregate (damp, loose-state sand)'],
            ['S', '1', '½', '—', '—', '3½ to 4½'],
            ['S', '—', '—', '—', '1', '2¼ to 3'],
            ['S', '½', '—', '1', '—', '3½ to 4½'],
            ['N', '1', '1', '—', '—', '4½ to 6'],
            ['N', '—', '—', '1', '—', '2¼ to 3'],
        ]
    },
}


def normalize_text(text):
    """텍스트 정규화 (비교용)"""
    if text is None:
        return ''
    text = str(text).strip()
    text = ' '.join(text.split())  # 다중 공백 제거
    text = text.replace('\n', ' ')
    # 특수 문자 정규화
    text = text.replace('—', '-').replace('–', '-')
    text = text.replace('½', '1/2').replace('¼', '1/4')
    return text.lower()


def compare_cells(extracted, ground_truth):
    """셀 단위 비교"""
    if not extracted or not ground_truth:
        return {'match': 0, 'total': 0, 'accuracy': 0}

    total_cells = 0
    matched_cells = 0
    mismatches = []

    min_rows = min(len(extracted), len(ground_truth))

    for row_idx in range(min_rows):
        ext_row = extracted[row_idx]
        gt_row = ground_truth[row_idx]
        min_cols = min(len(ext_row), len(gt_row))

        for col_idx in range(min_cols):
            total_cells += 1
            ext_val = normalize_text(ext_row[col_idx])
            gt_val = normalize_text(gt_row[col_idx])

            if ext_val == gt_val:
                matched_cells += 1
            else:
                # 부분 매칭 체크
                if ext_val in gt_val or gt_val in ext_val:
                    matched_cells += 0.5  # 부분 점수
                    mismatches.append({
                        'row': row_idx,
                        'col': col_idx,
                        'extracted': ext_val,
                        'expected': gt_val,
                        'partial': True
                    })
                else:
                    mismatches.append({
                        'row': row_idx,
                        'col': col_idx,
                        'extracted': ext_val,
                        'expected': gt_val,
                        'partial': False
                    })

    accuracy = matched_cells / total_cells if total_cells > 0 else 0

    return {
        'match': matched_cells,
        'total': total_cells,
        'accuracy': accuracy,
        'mismatches': mismatches[:10]  # 상위 10개만
    }


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


def extract_pdfplumber(page_index, table_index=0):
    """pdfplumber로 추출"""
    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[page_index]
        tables = page.extract_tables()
        if table_index < len(tables):
            return filldown_none_cells(tables[table_index])
    return None


def extract_pymupdf(page_index, table_index=0):
    """PyMuPDF로 추출"""
    doc = fitz.open(PDF_PATH)
    page = doc[page_index]
    tabs = page.find_tables()
    result = None
    if tabs.tables and table_index < len(tabs.tables):
        data = tabs.tables[table_index].extract()
        result = filldown_none_cells(data)
    doc.close()
    return result


def main():
    """Ground Truth 비교 테스트"""
    print("="*70)
    print("셀 단위 정확도 검증 (Ground Truth 비교)")
    print("="*70)

    results = {}

    for table_id, gt_info in GROUND_TRUTH.items():
        print(f"\n{'='*60}")
        print(f"{table_id} - {gt_info['description']}")
        print(f"{'='*60}")

        page_index = gt_info['page_index']
        table_index = gt_info.get('table_index', 0)
        gt_data = gt_info['data']

        # pdfplumber
        print("\n[pdfplumber]")
        extracted = extract_pdfplumber(page_index, table_index)
        if extracted:
            comparison = compare_cells(extracted, gt_data)
            print(f"  Accuracy: {comparison['accuracy']*100:.1f}%")
            print(f"  Matched: {comparison['match']}/{comparison['total']}")

            if comparison['mismatches']:
                print("  Mismatches:")
                for m in comparison['mismatches'][:3]:
                    print(f"    [{m['row']},{m['col']}] '{m['extracted']}' vs '{m['expected']}'")

            results[f"{table_id}_pdfplumber"] = comparison['accuracy']
        else:
            print("  Not found")
            results[f"{table_id}_pdfplumber"] = 0

        # PyMuPDF
        print("\n[PyMuPDF]")
        extracted = extract_pymupdf(page_index, table_index)
        if extracted:
            comparison = compare_cells(extracted, gt_data)
            print(f"  Accuracy: {comparison['accuracy']*100:.1f}%")
            print(f"  Matched: {comparison['match']}/{comparison['total']}")

            if comparison['mismatches']:
                print("  Mismatches:")
                for m in comparison['mismatches'][:3]:
                    print(f"    [{m['row']},{m['col']}] '{m['extracted']}' vs '{m['expected']}'")

            results[f"{table_id}_pymupdf"] = comparison['accuracy']
        else:
            print("  Not found")
            results[f"{table_id}_pymupdf"] = 0

    # 요약
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    pdfplumber_avg = sum(v for k, v in results.items() if 'pdfplumber' in k) / len([k for k in results if 'pdfplumber' in k])
    pymupdf_avg = sum(v for k, v in results.items() if 'pymupdf' in k) / len([k for k in results if 'pymupdf' in k])

    print(f"pdfplumber average: {pdfplumber_avg*100:.1f}%")
    print(f"PyMuPDF average: {pymupdf_avg*100:.1f}%")

    # JSON 저장
    output = {
        'results': results,
        'averages': {
            'pdfplumber': pdfplumber_avg,
            'pymupdf': pymupdf_avg
        }
    }

    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(f'{OUTPUT_DIR}/ground_truth_comparison.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {OUTPUT_DIR}/ground_truth_comparison.json")


if __name__ == "__main__":
    main()
