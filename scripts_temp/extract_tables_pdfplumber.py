"""
pdfplumber 기반 테이블 추출 스크립트
- 복잡한 Building Code 테이블 지원
- 병합 셀 처리
- 다중 페이지 테이블 감지
"""

import pdfplumber
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'
OUTPUT_DIR = './output'

# 테이블 설정 (기존 extract_tables_final.py에서 가져옴)
# bbox는 나중에 조정 필요
TABLE_CONFIG = {
    'Table 9.3.1.7': {'page': 717, 'header_rows': 2},
    'Table 9.3.2.1': {'page': 719, 'header_rows': 2},
    'Table 9.6.1.3-A': {'page': 731, 'header_rows': 3},
    'Table 9.6.1.3-B': {'page': 732, 'header_rows': 3},
    'Table 9.6.1.3-C': {'page': 732, 'header_rows': 3},
    'Table 9.6.1.3-D': {'page': 733, 'header_rows': 3},
    'Table 9.6.1.3-E': {'page': 733, 'header_rows': 3},
    'Table 9.6.1.3-F': {'page': 734, 'header_rows': 3},
    'Table 9.6.1.3-G': {'page': 734, 'header_rows': 3},
    'Table 9.15.3.4': {'page': 820, 'header_rows': 2},
    'Table 9.15.4.2': {'page': 823, 'header_rows': 2},
    'Table 9.15.4.3-A': {'page': 824, 'header_rows': 2},
    'Table 9.15.4.3-B': {'page': 824, 'header_rows': 2},
    'Table 9.15.4.5-A': {'page': 826, 'header_rows': 2},
    'Table 9.15.4.5-B': {'page': 826, 'header_rows': 2},
    'Table 9.15.4.5-C': {'page': 826, 'header_rows': 2},
    'Table 9.23.3.1': {'page': 867, 'header_rows': 2},
    'Table 9.23.3.5-A': {'page': 868, 'header_rows': 2},
    'Table 9.23.3.5-B': {'page': 869, 'header_rows': 2},
    'Table 9.23.4.2-A': {'page': 871, 'header_rows': 3},
    'Table 9.23.4.2-B': {'page': 872, 'header_rows': 3},
    'Table 9.23.4.2-C': {'page': 873, 'header_rows': 3},
    'Table 9.23.4.2-D': {'page': 874, 'header_rows': 3},
    'Table 9.23.4.2-E': {'page': 875, 'header_rows': 3},
    'Table 9.23.4.3': {'page': 876, 'header_rows': 2},
}

def clean_cell(cell):
    """셀 데이터 정리"""
    if cell is None:
        return ''

    text = str(cell)

    # 여러 줄 바꿈 정리
    text = re.sub(r'\n+', ' ', text)
    # 연속 공백 정리
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def clean_table_data(table_data):
    """테이블 데이터 정리"""
    if not table_data:
        return []

    cleaned = []
    seen_rows = set()

    for row in table_data:
        # 빈 행 제거
        if all(cell is None or str(cell).strip() == '' for cell in row):
            continue

        # 중복 행 제거 (헤더 반복 등)
        row_key = tuple(clean_cell(cell) for cell in row)
        if row_key in seen_rows:
            continue
        seen_rows.add(row_key)

        # 셀 정리
        cleaned_row = [clean_cell(cell) for cell in row]
        cleaned.append(cleaned_row)

    return cleaned

def detect_table_continuation(pdf, page_num):
    """다음 페이지로 테이블이 이어지는지 감지"""
    if page_num >= len(pdf.pages) - 1:
        return False

    current_page = pdf.pages[page_num]
    next_page = pdf.pages[page_num + 1]

    # 현재 페이지 테이블
    current_tables = current_page.find_tables()
    if not current_tables:
        return False

    # 다음 페이지 테이블
    next_tables = next_page.find_tables()
    if not next_tables:
        return False

    # 컬럼 수 비교
    try:
        current_data = current_tables[-1].extract()
        next_data = next_tables[0].extract()

        current_cols = len(current_data[0]) if current_data else 0
        next_cols = len(next_data[0]) if next_data else 0

        return current_cols == next_cols
    except:
        return False

def extract_table_with_continuation(pdf, start_page, config):
    """다중 페이지 테이블 추출 (연속 페이지 병합)"""
    all_rows = []
    current_page_num = start_page - 1  # 0-indexed
    header = None
    header_rows = config.get('header_rows', 1)

    while current_page_num < len(pdf.pages):
        page = pdf.pages[current_page_num]

        # 테이블 설정
        table_settings = {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 3,
        }

        tables = page.find_tables(table_settings)

        if not tables:
            break

        # 테이블 선택 (첫 페이지는 모든 테이블, 이후는 첫 번째만)
        if current_page_num == start_page - 1:
            table_data = tables[0].extract()
        else:
            table_data = tables[0].extract()

        if not table_data:
            break

        if current_page_num == start_page - 1:
            # 첫 페이지: 헤더 저장
            header = table_data[:header_rows]
            all_rows.extend(table_data)
        else:
            # 이후 페이지: 헤더 중복 확인 및 제거
            if table_data[:header_rows] == header:
                all_rows.extend(table_data[header_rows:])
            else:
                all_rows.extend(table_data)

        # 다음 페이지 확인
        if not detect_table_continuation(pdf, current_page_num):
            break

        current_page_num += 1

    return all_rows

def extract_single_table(pdf, page_num, config):
    """단일 페이지 테이블 추출"""
    page = pdf.pages[page_num - 1]

    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "join_tolerance": 3,
        "edge_min_length": 3,
    }

    tables = page.find_tables(table_settings)

    if not tables:
        return None

    # 첫 번째 테이블 추출
    return tables[0].extract()

def validate_table(table_data, table_id):
    """테이블 검증"""
    issues = []

    if not table_data:
        issues.append('empty_table')
        return issues

    # 컬럼 수 일관성
    col_counts = set(len(row) for row in table_data)
    if len(col_counts) > 1:
        issues.append(f'inconsistent_columns: {col_counts}')

    # 너무 긴 셀 (병합 셀 의심)
    for i, row in enumerate(table_data):
        for j, cell in enumerate(row):
            if cell and len(str(cell)) > 500:
                issues.append(f'long_cell_r{i}_c{j}')

    # 빈 컬럼
    if table_data:
        empty_cols = []
        for col_idx in range(len(table_data[0])):
            if all(not row[col_idx] if col_idx < len(row) else True for row in table_data[1:]):
                empty_cols.append(col_idx)
        if empty_cols:
            issues.append(f'empty_columns: {empty_cols}')

    return issues

def table_to_html(table_data, header_rows=1):
    """테이블을 HTML로 변환"""
    if not table_data:
        return ''

    html = ['<table class="border-collapse border border-gray-300 w-full text-sm">']

    # 헤더
    if header_rows > 0:
        html.append('<thead class="bg-gray-100">')
        for row in table_data[:header_rows]:
            html.append('<tr>')
            for cell in row:
                html.append(f'<th class="border border-gray-300 px-2 py-1 text-left">{cell or ""}</th>')
            html.append('</tr>')
        html.append('</thead>')

    # 바디
    html.append('<tbody>')
    for row in table_data[header_rows:]:
        html.append('<tr>')
        for cell in row:
            html.append(f'<td class="border border-gray-300 px-2 py-1">{cell or ""}</td>')
        html.append('</tr>')
    html.append('</tbody>')

    html.append('</table>')

    return '\n'.join(html)

def extract_all_tables():
    """모든 테이블 추출"""
    results = {}
    stats = {'success': 0, 'failed': 0, 'issues': 0}

    print("=" * 60)
    print("pdfplumber 테이블 추출 시작")
    print("=" * 60)

    with pdfplumber.open(PDF_PATH) as pdf:
        for table_id, config in TABLE_CONFIG.items():
            print(f"\n[{table_id}] Page {config['page']}...")

            try:
                # 테이블 추출
                table_data = extract_single_table(pdf, config['page'], config)

                if table_data:
                    # 데이터 정리
                    cleaned = clean_table_data(table_data)

                    # 검증
                    issues = validate_table(cleaned, table_id)

                    # HTML 변환
                    html = table_to_html(cleaned, config.get('header_rows', 1))

                    results[table_id] = {
                        'id': table_id,
                        'page': config['page'],
                        'rows': len(cleaned),
                        'cols': len(cleaned[0]) if cleaned else 0,
                        'data': cleaned,
                        'html': html,
                        'issues': issues
                    }

                    if issues:
                        print(f"  ⚠️ {len(cleaned)} rows, issues: {issues}")
                        stats['issues'] += 1
                    else:
                        print(f"  ✅ {len(cleaned)} rows, {len(cleaned[0]) if cleaned else 0} cols")
                        stats['success'] += 1
                else:
                    print(f"  ❌ No table found")
                    stats['failed'] += 1

            except Exception as e:
                print(f"  ❌ Error: {e}")
                stats['failed'] += 1

    print("\n" + "=" * 60)
    print(f"완료: 성공 {stats['success']}, 경고 {stats['issues']}, 실패 {stats['failed']}")
    print("=" * 60)

    return results

def main():
    # 출력 디렉토리 생성
    Path(OUTPUT_DIR).mkdir(exist_ok=True)

    # 추출
    results = extract_all_tables()

    # JSON 저장
    output_path = Path(OUTPUT_DIR) / 'tables_pdfplumber.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nJSON saved: {output_path}")

    # HTML 저장 (각 테이블)
    html_dir = Path(OUTPUT_DIR) / 'tables_html'
    html_dir.mkdir(exist_ok=True)

    for table_id, data in results.items():
        html_path = html_dir / f"{table_id.replace(' ', '_').replace('.', '_')}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{table_id}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="p-8">
    <h1 class="text-2xl font-bold mb-4">{table_id}</h1>
    <p class="mb-4 text-gray-600">Page {data['page']} | {data['rows']} rows | {data['cols']} columns</p>
    {data.get('html', 'No data')}
</body>
</html>""")

    print(f"HTML files saved: {html_dir}")

if __name__ == '__main__':
    main()
