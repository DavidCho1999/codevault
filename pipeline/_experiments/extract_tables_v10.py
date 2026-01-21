"""
extract_tables_v10.py - 테이블 파싱 재작성
- bbox 기반 테이블 ID 매칭 (정확한 위치 기반)
- pdfplumber 단일 사용 (안정성)
- 서브테이블 (-A, -B, ...) 정확히 추출
- 중복 제거 (해시 기반)
"""

import sys
import os
import json
import re
import hashlib
from typing import List, Dict, Tuple, Optional

sys.stdout.reconfigure(encoding='utf-8')

import pdfplumber
import fitz  # PyMuPDF for text position

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


def find_table_titles_with_bbox(pdf_path: str, page_num: int) -> List[Dict]:
    """
    페이지에서 테이블 제목과 위치(bbox) 찾기
    - 줄 시작에 "Table X.X.X.X" 패턴이 있는 것만 (Notes 참조 제외)
    - 각 테이블 ID당 첫 번째 등장만 사용
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]  # 0-indexed

    # 텍스트 딕셔너리로 추출 (위치 정보 포함)
    text_dict = page.get_text("dict")

    table_titles = []
    seen_ids = set()

    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:  # 텍스트 블록만
            continue

        for line in block.get("lines", []):
            line_text = ""
            line_bbox = None

            for span in line.get("spans", []):
                line_text += span.get("text", "")
                if line_bbox is None:
                    line_bbox = span.get("bbox")

            line_text = line_text.strip()

            # Notes to Table, See Table 등 참조 제외
            if 'Notes to' in line_text or 'See Table' in line_text:
                continue

            # 줄 시작에 Table ID가 있는 경우만 (테이블 제목)
            match = re.match(r'^Table\s+(9\.\d+\.\d+\.\d+(?:\.-[A-Z])?)', line_text)
            if match:
                table_id = "Table " + match.group(1)

                # 이미 본 ID는 스킵 (중복 방지)
                if table_id in seen_ids:
                    continue
                seen_ids.add(table_id)

                table_titles.append({
                    'id': table_id,
                    'y': line_bbox[1] if line_bbox else 0,  # y 좌표
                    'bbox': line_bbox,
                    'full_text': line_text
                })

    doc.close()

    # y 좌표로 정렬
    table_titles.sort(key=lambda x: x['y'])

    return table_titles


def extract_tables_pdfplumber(pdf_path: str, page_num: int) -> List[Dict]:
    """
    pdfplumber로 페이지의 모든 테이블 추출
    """
    with pdfplumber.open(pdf_path) as pdf:
        if page_num - 1 >= len(pdf.pages):
            return []

        page = pdf.pages[page_num - 1]
        tables = page.find_tables()

        results = []
        for i, table in enumerate(tables):
            bbox = table.bbox  # (x0, y0, x1, y1)
            data = table.extract()

            if data and len(data) > 0:
                # 데이터 정리
                cleaned = clean_table_data(data)
                if cleaned:
                    results.append({
                        'index': i,
                        'bbox': bbox,
                        'y': bbox[1],  # 상단 y 좌표
                        'data': cleaned
                    })

        return results


def clean_table_data(data: List[List]) -> List[List]:
    """테이블 데이터 정리"""
    if not data:
        return []

    cleaned = []
    for row in data:
        cleaned_row = []
        for cell in row:
            if cell is None:
                cleaned_row.append("")
            else:
                # 줄바꿈 정리
                text = str(cell).strip()
                text = re.sub(r'\n+', ' ', text)
                text = re.sub(r'\s+', ' ', text)
                cleaned_row.append(text)

        # 빈 행 제외
        if any(c for c in cleaned_row):
            cleaned.append(cleaned_row)

    return cleaned


def match_tables_to_ids(titles: List[Dict], tables: List[Dict]) -> List[Tuple[str, Dict]]:
    """
    테이블 제목과 추출된 테이블 매칭 (y 좌표 기반)
    """
    if not titles or not tables:
        return []

    matched = []
    used_tables = set()

    for title in titles:
        title_y = title['y']
        best_match = None
        best_distance = float('inf')

        for j, table in enumerate(tables):
            if j in used_tables:
                continue

            table_y = table['y']

            # 테이블이 제목 아래에 있어야 함
            if table_y >= title_y:
                distance = table_y - title_y

                # 가장 가까운 테이블 선택 (200px 이내)
                if distance < best_distance and distance < 200:
                    best_distance = distance
                    best_match = j

        if best_match is not None:
            used_tables.add(best_match)
            matched.append((title['id'], tables[best_match]))

    return matched


def table_hash(data: List[List]) -> str:
    """테이블 데이터 해시 생성 (중복 감지용)"""
    content = json.dumps(data, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()[:12]


def data_to_html(table_id: str, data: List[List]) -> str:
    """테이블 데이터를 HTML로 변환"""
    if not data:
        return ""

    html = f'<table class="obc-table" data-table-id="{table_id}">\n'

    # 첫 행을 헤더로
    if len(data) > 0:
        html += '<thead>\n<tr>\n'
        for cell in data[0]:
            html += f'<th>{cell}</th>\n'
        html += '</tr>\n</thead>\n'

    # 나머지 행을 본문으로
    if len(data) > 1:
        html += '<tbody>\n'
        for i, row in enumerate(data[1:]):
            bg = 'bg-white' if i % 2 == 0 else 'bg-gray-50'
            html += f'<tr class="{bg}">\n'
            for j, cell in enumerate(row):
                tag = 'th' if j == 0 else 'td'
                html += f'<{tag}>{cell}</{tag}>\n'
            html += '</tr>\n'
        html += '</tbody>\n'

    html += '</table>'
    return html


def extract_all_tables():
    """전체 테이블 추출"""
    pdf_path, output_path = get_paths()

    print("=" * 70)
    print("Part 9 Table Extraction v10 (bbox-based matching)")
    print("=" * 70)
    print(f"PDF: {pdf_path}")
    print(f"Range: p.{START_PAGE} - p.{END_PAGE}")

    all_tables = {}  # table_id -> table_data
    seen_hashes = {}  # hash -> table_id (중복 감지)

    stats = {
        'pages_processed': 0,
        'tables_found': 0,
        'duplicates_skipped': 0
    }

    print("\nProcessing pages...")

    for page_num in range(START_PAGE, END_PAGE + 1):
        # 1. 테이블 제목 찾기
        titles = find_table_titles_with_bbox(pdf_path, page_num)

        if not titles:
            continue

        # 2. 테이블 추출
        tables = extract_tables_pdfplumber(pdf_path, page_num)

        if not tables:
            continue

        # 3. 매칭
        matched = match_tables_to_ids(titles, tables)

        for table_id, table_data in matched:
            data = table_data['data']

            # 중복 체크
            h = table_hash(data)
            if h in seen_hashes:
                stats['duplicates_skipped'] += 1
                continue

            # 이미 같은 ID로 저장된 경우
            if table_id in all_tables:
                # 더 많은 데이터를 가진 것 선택
                if len(data) <= len(all_tables[table_id]['data']):
                    stats['duplicates_skipped'] += 1
                    continue

            seen_hashes[h] = table_id

            all_tables[table_id] = {
                'title': table_id,
                'page': page_num,
                'rows': len(data),
                'cols': len(data[0]) if data else 0,
                'data': data,
                'html': data_to_html(table_id, data)
            }

            stats['tables_found'] += 1

        stats['pages_processed'] += 1

        # 진행 상황
        if stats['pages_processed'] % 50 == 0:
            print(f"  Processed {stats['pages_processed']} pages, {stats['tables_found']} tables...")

    print(f"\nExtraction complete:")
    print(f"  Pages processed: {stats['pages_processed']}")
    print(f"  Tables found: {stats['tables_found']}")
    print(f"  Duplicates skipped: {stats['duplicates_skipped']}")

    # JSON 저장 (table_id를 키로)
    os.makedirs(output_path, exist_ok=True)
    output_file = os.path.join(output_path, 'part9_tables_v10.json')

    # data 필드 제거 (html만 유지)
    output_data = {}
    for table_id, table_info in all_tables.items():
        output_data[table_id] = {
            'title': table_info['title'],
            'page': table_info['page'],
            'rows': table_info['rows'],
            'cols': table_info['cols'],
            'html': table_info['html']
        }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\nSaved: {output_file}")

    # 검증
    validate_extraction(output_data)

    return output_data


def validate_extraction(tables: Dict):
    """추출 결과 검증"""
    print("\n" + "=" * 70)
    print("Validation Report")
    print("=" * 70)

    # 9.6.1 테이블 확인
    glass_tables = [k for k in tables.keys() if k.startswith('Table 9.6.1')]
    print(f"\n9.6.1 Glass tables ({len(glass_tables)}):")
    for t in sorted(glass_tables):
        info = tables[t]
        print(f"  {t}: {info['rows']}x{info['cols']} (p.{info['page']})")

    # 9.4.3 테이블 확인
    deflection_tables = [k for k in tables.keys() if k.startswith('Table 9.4.3')]
    print(f"\n9.4.3 Deflection tables ({len(deflection_tables)}):")
    for t in sorted(deflection_tables):
        info = tables[t]
        print(f"  {t}: {info['rows']}x{info['cols']} (p.{info['page']})")

    # 9.15 테이블 확인
    foundation_tables = [k for k in tables.keys() if k.startswith('Table 9.15')]
    print(f"\n9.15 Foundation tables ({len(foundation_tables)}):")
    for t in sorted(foundation_tables):
        info = tables[t]
        print(f"  {t}: {info['rows']}x{info['cols']} (p.{info['page']})")

    # 전체 통계
    sections = {}
    for table_id in tables.keys():
        match = re.match(r'Table (\d+\.\d+)', table_id)
        if match:
            section = match.group(1)
            sections[section] = sections.get(section, 0) + 1

    print(f"\nTables by section:")
    for section in sorted(sections.keys()):
        print(f"  {section}: {sections[section]} tables")


if __name__ == "__main__":
    tables = extract_all_tables()
    print("\nDone!")
