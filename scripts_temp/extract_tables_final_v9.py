"""
extract_tables_final_v9.py - 최적화된 테이블 추출
- 빠른 속도: PyMuPDF로 테이블 감지, Camelot으로 정밀 추출
- 하이브리드: 감지 실패시 stream 모드로 폴백
- 검증 포함
"""

import sys
import os
import json
import re
from copy import deepcopy
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

import fitz  # PyMuPDF for fast detection
import pdfplumber  # backup option

try:
    import camelot
    HAS_CAMELOT = True
except ImportError:
    HAS_CAMELOT = False
    print("⚠️ Camelot 없음 - pdfplumber 사용")

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'
OUTPUT_DIR = '../codevault/public/data'

# Part 9 범위
START_PAGE = 715
END_PAGE = 1050


def get_paths():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.normpath(os.path.join(script_dir, PDF_PATH))
    output_path = os.path.normpath(os.path.join(script_dir, OUTPUT_DIR))
    return pdf_path, output_path


def filldown_cells(data):
    """병합 셀 처리"""
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
    if cell is None:
        return None
    text = str(cell).strip()
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip() if text.strip() else None


def clean_table(data):
    if not data:
        return []
    cleaned = []
    for row in data:
        cleaned_row = [clean_cell(cell) for cell in row]
        if any(cell is not None for cell in cleaned_row):
            cleaned.append(cleaned_row)
    return cleaned


def detect_tables_pymupdf(pdf_path):
    """PyMuPDF로 빠르게 테이블 위치 감지"""
    print("1단계: PyMuPDF로 테이블 위치 스캔...")

    doc = fitz.open(pdf_path)
    table_pages = []

    for page_num in range(START_PAGE - 1, min(END_PAGE, len(doc))):
        page = doc[page_num]
        tabs = page.find_tables()

        if tabs.tables:
            table_info = []
            for tab in tabs.tables:
                table_info.append({
                    'bbox': tab.bbox,
                    'rows': tab.row_count,
                    'cols': tab.col_count
                })
            table_pages.append({
                'page': page_num + 1,
                'tables': table_info
            })

    doc.close()
    print(f"   → {len(table_pages)} 페이지에서 테이블 발견")
    return table_pages


def extract_with_pdfplumber(pdf_path, page_num):
    """pdfplumber로 테이블 추출 (폴백)"""
    with pdfplumber.open(pdf_path) as pdf:
        if page_num - 1 >= len(pdf.pages):
            return []

        page = pdf.pages[page_num - 1]
        tables = page.extract_tables()

        results = []
        for table in tables:
            if table and len(table) > 1:
                cleaned = clean_table(table)
                filled = filldown_cells(cleaned)
                if filled:
                    results.append({
                        'source': 'pdfplumber',
                        'data': filled
                    })
        return results


def extract_with_camelot(pdf_path, page_num):
    """Camelot으로 테이블 추출"""
    if not HAS_CAMELOT:
        return extract_with_pdfplumber(pdf_path, page_num)

    results = []

    # Lattice 먼저
    try:
        tables = camelot.read_pdf(pdf_path, pages=str(page_num), flavor='lattice')
        for table in tables:
            df = table.df
            data = df.values.tolist()
            if data and len(data) > 1:
                cleaned = clean_table(data)
                filled = filldown_cells(cleaned)
                if filled:
                    results.append({
                        'source': 'camelot-lattice',
                        'accuracy': table.accuracy if hasattr(table, 'accuracy') else 0,
                        'data': filled
                    })
    except:
        pass

    # Lattice 실패시 Stream
    if not results:
        try:
            tables = camelot.read_pdf(pdf_path, pages=str(page_num), flavor='stream')
            for table in tables:
                df = table.df
                data = df.values.tolist()
                if data and len(data) > 1:
                    cleaned = clean_table(data)
                    filled = filldown_cells(cleaned)
                    if filled:
                        results.append({
                            'source': 'camelot-stream',
                            'accuracy': table.accuracy if hasattr(table, 'accuracy') else 0,
                            'data': filled
                        })
        except:
            pass

    # Camelot 실패시 pdfplumber
    if not results:
        results = extract_with_pdfplumber(pdf_path, page_num)

    return results


def find_table_id_on_page(pdf_path, page_num):
    """페이지에서 테이블 ID 찾기"""
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    text = page.get_text()
    doc.close()

    pattern = r'Table\s+(\d+\.\d+\.\d+\.\d+(?:-[A-Z])?)'
    matches = re.findall(pattern, text, re.IGNORECASE)

    return list(dict.fromkeys(matches))  # 중복 제거, 순서 유지


def extract_all_tables():
    """전체 추출 프로세스"""
    pdf_path, output_path = get_paths()

    print("=" * 70)
    print("🚀 Part 9 테이블 추출 v9 (하이브리드)")
    print(f"   PDF: {pdf_path}")
    print(f"   범위: p.{START_PAGE} - p.{END_PAGE}")
    print("=" * 70)

    # 1단계: 빠른 스캔
    table_pages = detect_tables_pymupdf(pdf_path)

    if not table_pages:
        print("❌ 테이블을 찾을 수 없습니다.")
        return []

    # 2단계: 정밀 추출
    print(f"\n2단계: 정밀 추출 ({len(table_pages)} 페이지)...")

    all_tables = []
    source_counts = {'camelot-lattice': 0, 'camelot-stream': 0, 'pdfplumber': 0}

    for i, page_info in enumerate(table_pages):
        page_num = page_info['page']

        # 테이블 ID 찾기
        table_ids = find_table_id_on_page(pdf_path, page_num)

        # 추출
        extracted = extract_with_camelot(pdf_path, page_num)

        for idx, table_data in enumerate(extracted):
            data = table_data['data']
            source = table_data.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1

            # 테이블 ID 매칭 (추출 순서대로)
            table_id = table_ids[idx] if idx < len(table_ids) else None

            table_entry = {
                'page': page_num,
                'index': idx,
                'table_id': table_id,
                'source': source,
                'accuracy': table_data.get('accuracy', 0),
                'rows': len(data),
                'cols': len(data[0]) if data else 0,
                'headers': data[0] if data else [],
                'data': data[1:] if len(data) > 1 else [],
                'raw_data': data
            }
            all_tables.append(table_entry)

        # 진행 상황 (10개마다)
        if (i + 1) % 10 == 0:
            print(f"   진행: {i+1}/{len(table_pages)} 페이지...")

    print(f"\n📊 추출 완료:")
    print(f"   총 테이블: {len(all_tables)}개")
    for source, count in source_counts.items():
        if count > 0:
            print(f"   - {source}: {count}개")

    # 저장
    os.makedirs(output_path, exist_ok=True)
    output_file = os.path.join(output_path, 'part9_tables_v9.json')

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_tables, f, ensure_ascii=False, indent=2)

    print(f"\n💾 저장됨: {output_file}")

    # 검증
    validate_and_report(all_tables)

    return all_tables


def validate_and_report(tables):
    """검증 및 리포트"""
    print("\n" + "=" * 70)
    print("✅ 검증 리포트")
    print("=" * 70)

    # 통계
    total_rows = sum(t['rows'] for t in tables)
    with_id = sum(1 for t in tables if t.get('table_id'))

    print(f"   테이블 수: {len(tables)}")
    print(f"   총 행 수: {total_rows}")
    print(f"   ID 있는 테이블: {with_id}/{len(tables)}")

    # 문제 테이블
    issues = []
    for t in tables:
        null_count = sum(1 for row in t['raw_data'] for c in row if c is None or c == '')
        total = t['rows'] * t['cols']
        if total > 0 and null_count / total > 0.3:
            issues.append(f"p.{t['page']} ({t.get('table_id', 'N/A')}): NULL {null_count/total*100:.0f}%")

    if issues:
        print(f"\n   ⚠️ 주의 필요 ({len(issues)}개):")
        for issue in issues[:5]:
            print(f"      - {issue}")
    else:
        print("\n   ✅ 모든 테이블 품질 양호")

    # 샘플
    print("\n📋 샘플 테이블 (처음 3개):")
    for t in tables[:3]:
        print(f"\n  📊 {t.get('table_id', 'Unknown')} (p.{t['page']}, {t['source']})")
        print(f"     크기: {t['rows']}x{t['cols']}")
        if t['headers']:
            print(f"     헤더: {t['headers'][:3]}...")


if __name__ == "__main__":
    tables = extract_all_tables()
    print("\n🎉 완료!")
