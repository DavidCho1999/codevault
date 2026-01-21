"""
extract_tables_camelot.py - Camelot 기반 Part 9 테이블 추출
테스트 결과 Camelot이 78.8%로 최고 성능

특징:
1. lattice (선 기반) 우선, 실패시 stream (공백 기반) 시도
2. filldown으로 병합 셀 처리
3. 다중 헤더 행 자동 감지
4. 검증 및 품질 리포트
"""

import sys
import os
import json
import re
from copy import deepcopy
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

try:
    import camelot
except ImportError:
    print("❌ Camelot이 설치되지 않았습니다.")
    print("   pip install camelot-py[cv]")
    sys.exit(1)

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'
OUTPUT_DIR = '../codevault/public/data'

# Part 9 페이지 범위
START_PAGE = 715
END_PAGE = 1050


def get_pdf_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(script_dir, PDF_PATH))


def get_output_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(script_dir, OUTPUT_DIR))


def filldown_cells(data):
    """병합 셀 처리: None/빈 값을 위의 값으로 채움"""
    if not data:
        return data

    result = deepcopy(data)

    for col in range(len(result[0]) if result else 0):
        last_value = None
        for row in range(len(result)):
            cell = result[row][col]
            if cell is None or (isinstance(cell, str) and cell.strip() == ''):
                result[row][col] = last_value
            else:
                last_value = str(cell).strip()
                result[row][col] = last_value

    return result


def clean_cell(cell):
    """셀 텍스트 정규화"""
    if cell is None:
        return None

    text = str(cell).strip()
    # 여러 줄 바꿈 → 공백
    text = re.sub(r'\n+', ' ', text)
    # 연속 공백 제거
    text = re.sub(r'\s+', ' ', text)

    return text.strip() if text.strip() else None


def clean_table(data):
    """테이블 데이터 정리"""
    if not data:
        return []

    cleaned = []
    for row in data:
        cleaned_row = [clean_cell(cell) for cell in row]
        # 모든 셀이 비어있으면 제외
        if any(cell is not None for cell in cleaned_row):
            cleaned.append(cleaned_row)

    return cleaned


def detect_header_rows(table_data):
    """헤더 행 수 자동 감지"""
    if not table_data or len(table_data) < 2:
        return 1

    header_rows = 1

    # 처음 4행 분석
    for i, row in enumerate(table_data[:4]):
        # 숫자가 많으면 데이터 행으로 판단
        numeric_count = sum(1 for cell in row if cell and re.match(r'^[\d.,\-\s]+$', str(cell)))

        if numeric_count > len(row) / 2:
            break
        header_rows = i + 1

    return min(header_rows, 3)  # 최대 3행


def find_table_id(page_text):
    """페이지 텍스트에서 테이블 ID 찾기"""
    pattern = r'Table\s+(\d+\.\d+\.\d+\.\d+(?:\.-[A-Z])?(?:-[A-Z])?)'
    matches = re.findall(pattern, page_text, re.IGNORECASE)

    # 중복 제거하고 첫 번째 반환
    seen = set()
    unique = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            unique.append(m)

    return unique


def extract_table_from_page(pdf_path, page_num):
    """단일 페이지에서 테이블 추출 (Camelot)"""
    tables_extracted = []

    # 1. Lattice (선 기반) 먼저 시도
    try:
        tables = camelot.read_pdf(
            pdf_path,
            pages=str(page_num),
            flavor='lattice',
            line_scale=40,
            process_background=True
        )

        for i, table in enumerate(tables):
            df = table.df
            data = df.values.tolist()

            if data and len(data) > 1:
                # 정리 및 filldown
                cleaned = clean_table(data)
                filled = filldown_cells(cleaned)

                if filled:
                    tables_extracted.append({
                        'source': 'lattice',
                        'accuracy': table.accuracy if hasattr(table, 'accuracy') else 0,
                        'data': filled
                    })

    except Exception as e:
        pass  # lattice 실패시 stream 시도

    # 2. Stream (공백 기반) - lattice 결과가 없거나 품질 낮을 때
    if not tables_extracted:
        try:
            tables = camelot.read_pdf(
                pdf_path,
                pages=str(page_num),
                flavor='stream',
                edge_tol=50,
                row_tol=15
            )

            for i, table in enumerate(tables):
                df = table.df
                data = df.values.tolist()

                if data and len(data) > 1:
                    cleaned = clean_table(data)
                    filled = filldown_cells(cleaned)

                    if filled:
                        tables_extracted.append({
                            'source': 'stream',
                            'accuracy': table.accuracy if hasattr(table, 'accuracy') else 0,
                            'data': filled
                        })

        except Exception as e:
            pass

    return tables_extracted


def extract_all_tables():
    """Part 9 전체 테이블 추출"""
    pdf_path = get_pdf_path()
    output_path = get_output_path()

    print("=" * 70)
    print("🚀 Part 9 테이블 추출 (Camelot 기반)")
    print(f"   PDF: {pdf_path}")
    print(f"   범위: p.{START_PAGE} - p.{END_PAGE}")
    print("=" * 70)

    all_tables = []
    pages_with_tables = 0
    total_tables = 0

    # 페이지별 추출
    for page_num in range(START_PAGE, END_PAGE + 1):
        tables = extract_table_from_page(pdf_path, page_num)

        if tables:
            pages_with_tables += 1

            for idx, table_info in enumerate(tables):
                data = table_info['data']
                header_rows = detect_header_rows(data)

                # 테이블 정보 구성
                table_entry = {
                    'page': page_num,
                    'index': idx,
                    'source': table_info['source'],
                    'accuracy': table_info.get('accuracy', 0),
                    'rows': len(data),
                    'cols': len(data[0]) if data else 0,
                    'header_rows': header_rows,
                    'headers': data[:header_rows] if data else [],
                    'data': data[header_rows:] if len(data) > header_rows else [],
                    'raw_data': data
                }

                all_tables.append(table_entry)
                total_tables += 1

            # 진행 상황 출력 (10페이지마다)
            if (page_num - START_PAGE) % 50 == 0:
                print(f"   진행: p.{page_num} / {total_tables} 테이블...")

    print(f"\n📊 추출 완료:")
    print(f"   총 페이지: {END_PAGE - START_PAGE + 1}")
    print(f"   테이블 포함 페이지: {pages_with_tables}")
    print(f"   총 테이블 수: {total_tables}")

    # JSON 저장
    os.makedirs(output_path, exist_ok=True)
    output_file = os.path.join(output_path, 'part9_tables_camelot.json')

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_tables, f, ensure_ascii=False, indent=2)

    print(f"\n💾 저장됨: {output_file}")

    # 품질 요약
    print("\n" + "=" * 70)
    print("📋 품질 요약")
    print("=" * 70)

    lattice_count = sum(1 for t in all_tables if t['source'] == 'lattice')
    stream_count = sum(1 for t in all_tables if t['source'] == 'stream')

    print(f"   Lattice 추출: {lattice_count}개")
    print(f"   Stream 추출: {stream_count}개")

    # 샘플 출력
    print("\n샘플 테이블 (처음 3개):")
    for t in all_tables[:3]:
        print(f"\n  📊 페이지 {t['page']} ({t['source']}, {t['rows']}x{t['cols']})")
        print(f"     헤더: {t['headers'][0][:3] if t['headers'] else 'N/A'}...")
        if t['data']:
            print(f"     첫 행: {t['data'][0][:3]}...")

    return all_tables


def validate_extraction(tables):
    """추출 결과 검증"""
    print("\n" + "=" * 70)
    print("✅ 검증")
    print("=" * 70)

    issues = []

    for t in tables:
        # 1. 빈 테이블
        if not t['raw_data']:
            issues.append(f"p.{t['page']}: 빈 테이블")

        # 2. 열 수 불일치
        col_counts = [len(row) for row in t['raw_data']]
        if len(set(col_counts)) > 1:
            issues.append(f"p.{t['page']}: 열 수 불일치 {set(col_counts)}")

        # 3. 너무 많은 빈 셀
        total_cells = sum(len(row) for row in t['raw_data'])
        null_cells = sum(1 for row in t['raw_data'] for c in row if c is None or c == '')
        if total_cells > 0 and null_cells / total_cells > 0.5:
            issues.append(f"p.{t['page']}: 빈 셀 {null_cells/total_cells*100:.0f}%")

    if issues:
        print(f"   ⚠️ 발견된 문제: {len(issues)}개")
        for issue in issues[:10]:
            print(f"      - {issue}")
    else:
        print("   ✅ 문제 없음")

    return len(issues) == 0


if __name__ == "__main__":
    tables = extract_all_tables()
    validate_extraction(tables)
    print("\n🎉 완료!")
