"""
Part 9 테이블 추출 스크립트 v7
- Deep Search: 테이블 내용 검증 알고리즘
- 키워드 매칭으로 올바른 테이블 식별
"""

import fitz
import json
import re
import sys
import os
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'
OUTPUT_DIR = './output'

# Part 9 테이블별 예상 키워드 (테이블 내용 검증용)
TABLE_KEYWORDS = {
    'Table 9.3.2.1': ['lumber', 'grade', 'stud', 'joist', 'rafter', 'plank', 'framing'],
    'Table 9.20.3.2': ['mortar', 'type', 'location', 'loadbearing', 'exterior', 'interior'],
    'Table 9.23.3.1': ['nail', 'diameter', 'mm', 'length', 'penny'],
    'Table 9.23.3.4': ['nail', 'framing', 'joist', 'stud', 'rafter', 'sheathing', 'spacing'],
    'Table 9.23.3.5': ['sheathing', 'subflooring', 'fastener', 'nail', 'screw', 'spacing'],
    'Table 9.6.1.3': ['glass', 'area', 'thickness', 'height'],
    'Table 9.15.4.5': ['foundation', 'wall', 'thickness', 'height', 'backfill'],
    'Table 9.23.17.1': ['sheathing', 'wall', 'thickness', 'stud'],
    'Table 9.23.17.2': ['sheathing', 'bracing', 'panel'],
    'Table 9.27.2.1': ['cladding', 'precipitation', 'moisture'],
    'Table 9.32.3.13': ['ventilation', 'exhaust', 'capacity', 'fan'],
}

# 수동 매핑 (확실한 테이블)
MANUAL_TABLES = {
    'Table 9.3.2.1': {'page': 719, 'idx': 0, 'title': 'Minimum Lumber Grades for Specific End Uses'},
    'Table 9.20.3.2': {'page': 839, 'idx': 0, 'title': 'Mortar Proportions by Volume'},
}


def get_table_text(tab):
    """테이블에서 모든 텍스트 추출"""
    data = tab.extract()
    if not data:
        return ""
    text_parts = []
    for row in data:
        for cell in row:
            if cell:
                text_parts.append(str(cell).lower())
    return " ".join(text_parts)


def calculate_keyword_score(table_text, keywords):
    """키워드 매칭 점수 계산"""
    if not keywords:
        return 0
    score = 0
    for keyword in keywords:
        if keyword.lower() in table_text:
            score += 1
    return score / len(keywords)


def validate_part9_content(table_text):
    """Part 9 관련 내용인지 검증"""
    # Part 9가 아닌 내용의 키워드
    invalid_keywords = [
        'compliance alternative', 'heritage building', 'retirement home',
        'article 11', 'sentence 11', 'part 11', 'sewage system',
        'performance level', 'chief building official'
    ]

    for keyword in invalid_keywords:
        if keyword in table_text:
            return False
    return True


def find_best_table_on_page(page, table_id, keywords):
    """페이지에서 가장 적합한 테이블 찾기"""
    tabs = page.find_tables()
    if not tabs.tables:
        return None, 0

    best_tab = None
    best_score = 0

    for tab in tabs.tables:
        table_text = get_table_text(tab)

        # Part 9 내용 검증
        if not validate_part9_content(table_text):
            continue

        # 키워드 점수 계산
        score = calculate_keyword_score(table_text, keywords)

        # 테이블 크기 보너스 (2행 이상)
        if tab.row_count >= 2:
            score += 0.1

        if score > best_score:
            best_score = score
            best_tab = tab

    return best_tab, best_score


def deep_search_table(doc, table_id, start_page, end_page):
    """
    Deep Search: 여러 페이지에서 최적의 테이블 찾기
    """
    base_id = re.match(r'Table \d+\.\d+\.\d+\.\d+', table_id)
    if base_id:
        base_id = base_id.group()
    else:
        base_id = table_id

    # 키워드 가져오기
    keywords = TABLE_KEYWORDS.get(base_id, [])

    # 일반적인 Part 9 키워드 추가
    general_keywords = ['mm', 'minimum', 'maximum', 'spacing', 'size', 'type']
    all_keywords = keywords + general_keywords

    best_result = None
    best_score = 0
    best_page = None

    for page_num in range(start_page, min(end_page, len(doc))):
        page = doc[page_num]
        text = page.get_text()

        # 테이블 ID가 페이지에 있는지 확인
        if table_id not in text and base_id not in text:
            continue

        tab, score = find_best_table_on_page(page, table_id, all_keywords)

        if tab and score > best_score:
            best_score = score
            best_result = tab
            best_page = page_num + 1

    return best_result, best_page, best_score


def extract_table_html(tab, table_id):
    """테이블 데이터를 HTML로 변환"""
    data = tab.extract()

    if not data or len(data) < 2:
        return None

    # Clean data
    cleaned_data = []
    for row in data:
        cleaned_row = []
        for cell in row:
            if cell is None:
                cleaned_row.append('')
            else:
                text = str(cell).strip().replace('\n', ' ')
                text = re.sub(r'\s+', ' ', text)
                cleaned_row.append(text)
        cleaned_data.append(cleaned_row)

    # 빈 행 제거
    cleaned_data = [row for row in cleaned_data if any(cell.strip() for cell in row)]

    if len(cleaned_data) < 2:
        return None

    # 헤더 행 수 결정
    header_end = 1
    for i, row in enumerate(cleaned_data):
        if i == 0:
            continue
        first_cell = row[0].strip() if row[0] else ''
        # 데이터 패턴 감지
        if first_cell and any(first_cell.startswith(w) for w in ['Stud', 'Plank', 'Post', 'Roof', 'Sub', 'Wall', 'Floor', 'Ceiling']):
            header_end = i
            break
        if first_cell and re.match(r'^[\d.,]+', first_cell):
            header_end = i
            break
        if i >= 4:
            header_end = i
            break

    # Build HTML
    html_parts = [f'<table class="obc-table" data-table-id="{table_id}">']

    # Header
    html_parts.append('<thead>')
    for row in cleaned_data[:max(1, header_end)]:
        html_parts.append('<tr>')
        for cell in row:
            html_parts.append(f'<th>{cell}</th>')
        html_parts.append('</tr>')
    html_parts.append('</thead>')

    # Body
    if header_end < len(cleaned_data):
        html_parts.append('<tbody>')
        for ri, row in enumerate(cleaned_data[header_end:]):
            row_class = 'bg-white' if ri % 2 == 0 else 'bg-gray-50'
            html_parts.append(f'<tr class="{row_class}">')
            for j, cell in enumerate(row):
                tag = 'th' if j == 0 else 'td'
                display = cell if cell and cell != '-' else '—'
                html_parts.append(f'<{tag}>{display}</{tag}>')
            html_parts.append('</tr>')
        html_parts.append('</tbody>')

    html_parts.append('</table>')

    return '\n'.join(html_parts)


def find_table_references(doc):
    """
    PDF 전체에서 테이블 참조 찾기
    """
    table_refs = {}

    # Part 9 페이지 범위
    for page_num in range(700, 1050):
        page = doc[page_num]
        text = page.get_text()

        # 테이블 타이틀 패턴
        pattern = r'Table\s+(9\.\d+\.\d+\.\d+)(\.-[A-G])?\.'
        matches = re.finditer(pattern, text)

        for match in matches:
            table_num = match.group(1)
            suffix = match.group(2) or ''
            table_id = f'Table {table_num}{suffix}'

            # "Forming Part of" 확인
            context_start = max(0, match.start() - 100)
            context_end = min(len(text), match.end() + 300)
            context = text[context_start:context_end]

            is_table_definition = 'Forming Part of' in context or 'Notes to Table' in text

            if is_table_definition:
                if table_id not in table_refs:
                    table_refs[table_id] = {
                        'pages': [],
                        'title_context': context[:100]
                    }
                table_refs[table_id]['pages'].append(page_num)

    return table_refs


def main():
    doc = fitz.open(PDF_PATH)
    print(f"PDF opened: {len(doc)} pages")

    tables_data = {}
    errors = []
    low_confidence = []

    # 1. 수동 매핑된 테이블 먼저 처리
    print("\n1. Processing manually mapped tables...")
    for table_id, info in MANUAL_TABLES.items():
        page_num = info['page']
        idx = info['idx']
        title = info['title']

        page = doc[page_num - 1]
        tabs = page.find_tables()

        if tabs.tables and idx < len(tabs.tables):
            tab = tabs.tables[idx]
            html = extract_table_html(tab, table_id)
            if html:
                tables_data[table_id] = {
                    'title': f'{table_id}. {title}',
                    'page': page_num,
                    'rows': tab.row_count,
                    'cols': tab.col_count,
                    'html': html,
                    'confidence': 'manual'
                }
                print(f"  ✓ {table_id}: {tab.row_count}x{tab.col_count} (p.{page_num}) [MANUAL]")

    # 2. 테이블 참조 찾기
    print("\n2. Finding table references...")
    table_refs = find_table_references(doc)
    print(f"   Found {len(table_refs)} table references")

    # 3. Deep Search로 테이블 추출
    print("\n3. Deep searching for tables...")
    for table_id, ref_info in sorted(table_refs.items()):
        # 수동 매핑된 것은 스킵
        if table_id in MANUAL_TABLES or table_id in tables_data:
            continue

        pages = ref_info['pages']
        if not pages:
            continue

        # 검색 범위: 참조된 페이지 ± 5
        start_page = max(700, min(pages) - 5)
        end_page = min(1050, max(pages) + 5)

        tab, found_page, score = deep_search_table(doc, table_id, start_page, end_page)

        if tab and score > 0:
            html = extract_table_html(tab, table_id)
            if html:
                confidence = 'high' if score >= 0.3 else 'medium' if score >= 0.1 else 'low'
                tables_data[table_id] = {
                    'title': table_id,
                    'page': found_page,
                    'rows': tab.row_count,
                    'cols': tab.col_count,
                    'html': html,
                    'confidence': confidence,
                    'score': round(score, 2)
                }

                status = '✓' if confidence in ['high', 'medium'] else '?'
                print(f"  {status} {table_id}: {tab.row_count}x{tab.col_count} (p.{found_page}) [{confidence}, score={score:.2f}]")

                if confidence == 'low':
                    low_confidence.append(table_id)
            else:
                errors.append(f"{table_id}: HTML conversion failed")
        else:
            errors.append(f"{table_id}: No valid table found (pages: {pages})")

    # 4. 저장
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # confidence 필드 제거하고 저장
    output_data = {}
    for table_id, data in tables_data.items():
        output_data[table_id] = {
            'title': data['title'],
            'page': data['page'],
            'rows': data['rows'],
            'cols': data['cols'],
            'html': data['html']
        }

    output_path = os.path.join(OUTPUT_DIR, 'part9_tables_v7.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    # 5. Summary
    print(f"\n\n=== Summary ===")
    print(f"Successfully extracted: {len(tables_data)} tables")
    print(f"  - Manual: {len(MANUAL_TABLES)}")
    print(f"  - High confidence: {len([t for t in tables_data.values() if t.get('confidence') == 'high'])}")
    print(f"  - Medium confidence: {len([t for t in tables_data.values() if t.get('confidence') == 'medium'])}")
    print(f"  - Low confidence: {len(low_confidence)}")
    print(f"Errors: {len(errors)}")

    if low_confidence:
        print(f"\nLow confidence tables (may need manual review):")
        for t in low_confidence[:10]:
            print(f"  - {t}")

    if errors:
        print(f"\nErrors:")
        for e in errors[:10]:
            print(f"  - {e}")

    print(f"\nSaved to: {output_path}")

    # 6. 검증
    print("\n=== Verification ===")
    for key_table in ['Table 9.3.2.1', 'Table 9.20.3.2', 'Table 9.23.3.1', 'Table 9.23.3.5.-A']:
        if key_table in tables_data:
            t = tables_data[key_table]
            conf = t.get('confidence', 'unknown')
            score = t.get('score', 'N/A')
            print(f"{key_table}: Page {t['page']}, {t['rows']}x{t['cols']}, confidence={conf}, score={score}")
        else:
            print(f"{key_table}: NOT FOUND")

    doc.close()


if __name__ == "__main__":
    main()
