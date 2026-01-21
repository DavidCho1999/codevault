#!/usr/bin/env python3
"""
Part 9 전체 PDF를 파싱하여 SQLite DB에 저장
- 4단계 + 변형 구조 지원
- Alternative Subsection, Article Suffix, 0A Article, Sub-Article 처리
"""

import fitz
import sqlite3
import re
from pathlib import Path
from tree_builder import TreeBuilder
from patterns import detect_type

# === 설정 ===
PDF_PATH = Path(__file__).parent.parent / "source/2024 Building Code Compendium/301880.pdf"
DB_PATH = Path(__file__).parent.parent / "data" / "obc.db"
PART9_START = 710  # 0-indexed
PART9_END = 1034

# Section 목록 (part9.json에서 가져옴)
SECTIONS = [
    ('9.1', 'General'),
    ('9.2', 'Definitions'),
    ('9.3', 'Materials, Systems and Equipment'),
    ('9.4', 'Structural Requirements'),
    ('9.5', 'Design of Areas, Spaces and Doorways'),
    ('9.6', 'Glass'),
    ('9.7', 'Windows, Doors and Skylights'),
    ('9.8', 'Stairs, Ramps, Handrails and Guards'),
    ('9.9', 'Means of Egress'),
    ('9.10', 'Fire Protection'),
    ('9.11', 'Sound Transmission'),
    ('9.12', 'Excavation'),
    ('9.13', 'Dampproofing, Waterproofing and Soil Gas Control'),
    ('9.14', 'Drainage'),
    ('9.15', 'Footings and Foundations'),
    ('9.16', 'Floors-on-Ground'),
    ('9.17', 'Columns'),
    ('9.18', 'Crawl Spaces'),
    ('9.19', 'Roof Spaces'),
    ('9.20', 'Masonry and Insulating Concrete Form Walls Not In Contact with the Ground'),
    ('9.21', 'Masonry and Concrete Chimneys and Flues'),
    ('9.22', 'Fireplaces'),
    ('9.23', 'Wood Frame Construction'),
    ('9.24', 'Sheet Steel Stud Wall Framing'),
    ('9.25', 'Heat Transfer, Air Leakage and Condensation Control'),
    ('9.26', 'Roofing'),
    ('9.27', 'Cladding'),
    ('9.28', 'Stucco'),
    ('9.29', 'Interior Wall and Ceiling Finishes'),
    ('9.30', 'Flooring'),
    ('9.31', 'Plumbing Facilities'),
    ('9.32', 'Ventilation'),
    ('9.33', 'Heating and Air-Conditioning'),
    ('9.34', 'Electrical Facilities'),
    ('9.35', 'Garages and Carports'),
    ('9.36', 'Reserved'),
    ('9.37', 'Cottages'),
    ('9.38', 'Log Construction'),
    ('9.39', 'Park Model Trailers'),
    ('9.40', 'Reinforced Concrete Slabs'),
    ('9.41', 'Additional Requirements for Change of Use'),
]


def extract_text_sorted(page) -> str:
    """페이지 텍스트를 좌표 순으로 정렬하여 추출"""
    blocks = page.get_text("blocks")
    sorted_blocks = sorted(blocks, key=lambda b: (b[1], b[0]))

    lines = []
    for block in sorted_blocks:
        if block[6] == 0:  # 텍스트 블록만 (이미지 제외)
            text = block[4].strip()
            if text:
                lines.append(text)

    return '\n'.join(lines)


def clean_text(text: str) -> str:
    """텍스트 정리"""
    # 페이지 번호 제거
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)

    # 헤더/푸터 제거 (더 정밀한 패턴 사용)
    text = re.sub(r'^\d{4}\s+Building Code.*$', '', text, flags=re.MULTILINE)  # "2024 Building Code Compendium"
    text = re.sub(r'^Division [ABC]\s*[-–?]\s*Part\s*\d+.*$', '', text, flags=re.MULTILINE)  # "Division B - Part 9" (- or – or ?)
    text = re.sub(r'^Part 9\s*$', '', text, flags=re.MULTILINE)
    # Footer: "20 Division B ? Part 9" (페이지 번호 + Division)
    text = re.sub(r'^\d+\s+Division [ABC].*Part\s*\d+.*$', '', text, flags=re.MULTILINE)

    # 헤더의 running Article ID 제거
    # 간단한 접근: 텍스트 시작 부분에서 "Division B" 이전에 나오는 standalone Article ID만 제거
    # "Division B" 이후에 나오는 모든 Article ID는 유지

    # Division 위치 찾기
    div_match = re.search(r'Division [ABC]\s*[-–]\s*Part', text)
    if div_match:
        # Division 이전 텍스트에서만 Article ID 제거
        before_div = text[:div_match.start()]
        after_div = text[div_match.end():]

        # 헤더 Article ID 제거 (9.X.X.X. 형식으로 단독 줄에 있는 것만)
        before_div = re.sub(r'^9\.\d+\.\d+\.\d+[A-Z]?\.\s*$', '', before_div, flags=re.MULTILINE)

        text = before_div + after_div
    else:
        # Division이 없는 페이지는 그대로 유지
        pass

    # 연속 빈 줄 정리
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def is_id_only(line: str) -> tuple:
    """ID만 있는 줄인지 확인 (Title은 다음 줄에)"""
    # Subsection ID: 9.5.3.
    m = re.match(r'^(9\.\d+\.\d+)\.\s*$', line)
    if m:
        return ('subsection', m.group(1))

    # Article ID: 9.5.3.1.
    m = re.match(r'^(9\.\d+\.\d+\.\d+)\.\s*$', line)
    if m:
        return ('article', m.group(1))

    # Alt Subsection ID: 9.5.3A.
    m = re.match(r'^(9\.\d+\.\d+[A-Z])\.\s*$', line)
    if m:
        return ('alt_subsection', m.group(1))

    # Sub-Article ID: 9.5.3A.1.
    m = re.match(r'^(9\.\d+\.\d+[A-Z]\.\d+)\.\s*$', line)
    if m:
        return ('sub_article', m.group(1))

    # Article Suffix ID: 9.5.1.1A.
    m = re.match(r'^(9\.\d+\.\d+\.\d+[A-Z])\.\s*$', line)
    if m:
        return ('article_suffix', m.group(1))

    return None


def parse_page(builder: TreeBuilder, text: str, page_num: int, state: dict = None):
    """한 페이지 파싱 (특수 패턴 포함)

    Args:
        state: 페이지 간 유지되는 상태 {'content': [], 'type': None, 'data': None}
    Returns:
        state: 다음 페이지로 전달할 상태
    """
    lines = text.split('\n')

    # 이전 페이지에서 상태 복원
    if state:
        current_content = state.get('content', [])
        current_type = state.get('type')
        current_data = state.get('data')
    else:
        current_content = []
        current_type = None
        current_data = None

    skip_next = False
    in_table_notes = False  # Table 노트 영역 내에 있는지

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Table 노트 영역 감지 (Notes to Table X.X.X.X.:)
        if re.match(r'^Notes? to Table', line):
            in_table_notes = True
            continue

        # Table 노트 영역 종료 (새로운 Subsection/Article ID 발견)
        if in_table_notes:
            if re.match(r'^9\.\d+\.\d+\.?\s*$', line) or re.match(r'^9\.\d+\.\d+\.\d+\.?\s', line):
                in_table_notes = False
            else:
                # Table 노트 내 clause는 건너뛰기
                continue

        # 이전 줄이 ID only였으면 skip (Title로 사용됨)
        if skip_next:
            skip_next = False
            continue

        # ID only 패턴 체크 (Title이 다음 줄에)
        id_only = is_id_only(line)
        if id_only:
            node_type, node_id = id_only
            # 다음 줄이 Title인지 확인
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ''

            # 이전 clause 처리
            if current_type == 'clause' and current_content:
                full_content = '\n'.join(current_content)
                parent = builder.context_stack[-1] if builder.context_stack else None
                if parent and '(' not in parent:
                    clause_id = f"{parent}.({current_data['num']})"
                    builder.add_node('clause', clause_id, content=full_content, page=page_num)
                current_content = []

            # Section 헤더는 title로 사용하지 않음 (9.19.2.2 같은 Reserved 처리)
            if next_line and next_line[0].isupper() and not next_line.startswith('(') and not next_line.startswith('Section 9.'):
                title = next_line
                skip_next = True
            else:
                # Title이 없으면 Reserved로 처리
                title = 'Reserved' if not next_line or next_line.startswith('Section 9.') else None
                skip_next = False

            builder.add_node(node_type, node_id, title=title, page=page_num)
            current_type = node_type
            current_data = {'id': node_id, 'title': title}
            continue

        result = detect_type(line)

        if result:
            node_type, data = result

            # subclause/subsubclause가 아닐 때만 이전 content 저장 및 current_type 변경
            if node_type not in ('subclause', 'subsubclause'):
                # 이전에 쌓인 content 처리
                if current_type == 'clause' and current_content:
                    full_content = '\n'.join(current_content)
                    parent = builder.context_stack[-1] if builder.context_stack else None
                    if parent and '(' not in parent:  # Article 아래
                        clause_id = f"{parent}.({current_data['num']})"
                        builder.add_node('clause', clause_id, content=full_content, page=page_num)
                    current_content = []

                current_type = node_type
                current_data = data

            # === 기본 타입 ===
            if node_type == 'subsection':
                builder.add_node('subsection', data['id'], title=data['title'], page=page_num)

            elif node_type == 'article':
                builder.add_node('article', data['id'], title=data['title'], page=page_num)

            # === 특수 타입 (중요!) ===
            elif node_type == 'alt_subsection':
                # 9.5.3A → parent는 9.5 (Section)
                builder.add_node('alt_subsection', data['id'], title=data['title'], page=page_num)

            elif node_type == 'article_suffix':
                # 9.5.1.1A → parent는 9.5.1 (Subsection)
                builder.add_node('article_suffix', data['id'], title=data['title'], page=page_num)

            elif node_type == 'article_0a':
                # 9.33.6.10A → parent는 해당 Subsection
                builder.add_node('article_0a', data['id'], title=data['title'], page=page_num)

            elif node_type == 'sub_article':
                # 9.5.3A.1 → parent는 9.5.3A (Alt Subsection)
                builder.add_node('sub_article', data['id'], title=data['title'], page=page_num)

            # === Clause 레벨 ===
            elif node_type == 'clause':
                # 이전 clause 먼저 저장!
                if current_type == 'clause' and current_content and current_data:
                    full_content = '\n'.join(current_content)
                    parent = builder.context_stack[-1] if builder.context_stack else None
                    if parent and '(' not in parent:
                        clause_id = f"{parent}.({current_data['num']})"
                        builder.add_node('clause', clause_id, content=full_content, page=page_num)

                # 새 clause 시작
                current_content = [data['content']]

            elif node_type in ('subclause', 'subsubclause'):
                # Subclause/Subsubclause - 현재 clause content에 추가
                # current_type을 'clause'로 유지하여 content가 계속 쌓이도록 함
                if current_content:
                    if node_type == 'subclause':
                        current_content.append(f"({data['letter']}) {data['content']}")
                    else:
                        current_content.append(f"({data['numeral']}) {data['content']}")
                # current_type을 변경하지 않음 (clause 상태 유지)

        else:
            # Section 헤더는 건너뛰기 (예: "Section 9.2.  Definitions")
            if re.match(r'^Section\s+9\.\d+\.?\s+', line):
                continue

            # 이전 Clause의 연속
            if current_type == 'clause':
                current_content.append(line)

    # 마지막 content는 저장하지 않고 상태로 반환 (다음 페이지에서 계속될 수 있음)
    # 단, 새로운 Article/Subsection이 시작되면 이전 content는 저장됨
    return {
        'content': current_content,
        'type': current_type,
        'data': current_data
    }


def save_to_db(builder: TreeBuilder, db_path: Path):
    """트리를 SQLite에 저장"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 기존 Part 9 데이터 삭제
    cursor.execute("DELETE FROM nodes WHERE part = 9")
    cursor.execute("DELETE FROM refs WHERE source_id LIKE '9.%'")

    # nodes 저장
    for node_id, node in builder.to_dict().items():
        cursor.execute('''
            INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            node['id'],
            node['type'],
            node['part'],
            node['parent_id'],
            node['title'],
            node['content'],
            node['page'],
            node['seq']
        ))

        # refs 저장
        refs = node.get('refs', {})
        for ref_type, ref_list in refs.items():
            for ref in ref_list:
                target_type = ref_type.rstrip('s')  # 'tables' -> 'table'
                cursor.execute('''
                    INSERT INTO refs (source_id, target_id, target_type)
                    VALUES (?, ?, ?)
                ''', (node_id, ref, target_type))

    # === Article에 Clause content 합치기 ===
    print("  Merging clause content into articles...")

    # Article 타입들
    article_types = ('article', 'article_suffix', 'article_0a', 'sub_article')

    # 각 Article의 하위 Clause content 합치기
    cursor.execute(f'''
        SELECT id FROM nodes
        WHERE type IN {article_types} AND part = 9
    ''')
    articles = cursor.fetchall()

    for (article_id,) in articles:
        # 해당 Article의 모든 Clause 조회 (순서대로)
        cursor.execute('''
            SELECT id, content FROM nodes
            WHERE parent_id = ? AND type = 'clause'
            ORDER BY seq
        ''', (article_id,))
        clauses = cursor.fetchall()

        if clauses:
            # Clause content 합치기: "(1) content\n(2) content..."
            merged_content = '\n'.join([
                f"({clause_id.split('(')[-1].rstrip(')')}) {content}"
                for clause_id, content in clauses
                if content
            ])

            # Section 헤더 제거 (content 끝에 포함된 경우)
            # 예: "...coating. Section 9.8. Stairs, Ramps..."
            merged_content = re.sub(r'\s*Section\s+9\.\d+\.?\s+[A-Z].*$', '', merged_content)

            # Article content 업데이트
            cursor.execute('''
                UPDATE nodes SET content = ? WHERE id = ?
            ''', (merged_content, article_id))

    print(f"    Updated {len(articles)} articles with clause content")

    # 검색 인덱스 업데이트
    cursor.execute("DELETE FROM search_index WHERE node_id LIKE '9.%'")
    cursor.execute('''
        INSERT INTO search_index (node_id, title, content)
        SELECT id, title, content FROM nodes
        WHERE part = 9 AND (title IS NOT NULL OR content IS NOT NULL)
    ''')

    conn.commit()
    conn.close()
    print(f"[OK] Saved to {db_path}")


def main():
    print("=== Part 9 PDF 파싱 시작 ===\n")

    # PDF 열기
    if not PDF_PATH.exists():
        print(f"[ERROR] PDF not found: {PDF_PATH}")
        return

    doc = fitz.open(PDF_PATH)
    print(f"PDF loaded: {PDF_PATH.name}")
    print(f"Total pages: {len(doc)}")
    print(f"Part 9 range: {PART9_START + 1} - {PART9_END}\n")

    # TreeBuilder 초기화
    builder = TreeBuilder(part_num=9)

    # Part 노드 추가
    builder.add_node('part', '9', title='Housing and Small Buildings', page=PART9_START + 1)

    # Section 노드들 추가
    for sec_id, sec_title in SECTIONS:
        builder.add_node('section', sec_id, title=sec_title)

    # 페이지별 파싱 (상태를 페이지 간 유지)
    page_state = None  # 페이지 간 clause 상태 유지

    for page_idx in range(PART9_START, PART9_END):
        page = doc[page_idx]
        text = extract_text_sorted(page)
        text = clean_text(text)

        if text:
            page_state = parse_page(builder, text, page_idx + 1, page_state)

        # 진행률 표시
        if (page_idx - PART9_START) % 50 == 0:
            print(f"  Processed page {page_idx + 1}...")

    # 마지막 남은 clause content 저장
    if page_state and page_state.get('type') == 'clause' and page_state.get('content'):
        full_content = '\n'.join(page_state['content'])
        parent = builder.context_stack[-1] if builder.context_stack else None
        if parent and '(' not in parent:
            clause_id = f"{parent}.({page_state['data']['num']})"
            builder.add_node('clause', clause_id, content=full_content, page=PART9_END)

    doc.close()

    # 결과 출력
    nodes = builder.to_dict()
    print(f"\n=== 파싱 결과 ===")
    print(f"Total nodes: {len(nodes)}")

    # 타입별 개수
    type_counts = {}
    for node in nodes.values():
        t = node['type']
        type_counts[t] = type_counts.get(t, 0) + 1

    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {count}")

    # DB 저장
    save_to_db(builder, DB_PATH)

    print("\n=== 완료 ===")


if __name__ == '__main__':
    main()
