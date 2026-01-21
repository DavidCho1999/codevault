#!/usr/bin/env python3
"""
하이브리드 테이블 파서

MD 파일에서:
- 메타데이터 추출 (title, forming_part, notes)
- Pipe table → 그대로 HTML 변환
- Flat text → pdfplumber로 재추출

Usage:
    python hybrid_table_parser.py [--part 8]
"""

import re
import json
import pdfplumber
from pathlib import Path
from typing import Optional

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
MARKER_DIR = BASE_DIR / "data" / "marker"
PDF_PATH = BASE_DIR / "source" / "2024 Building Code Compendium" / "301880.pdf"
OUTPUT_DIR = BASE_DIR / "codevault" / "public" / "data"

# Part별 시작 페이지 (0-indexed)
PART_START_PAGES = {
    8: 678,   # Part 8 starts at page 679
    9: 711,   # Part 9 starts at page 712
    10: 1028, # Part 10
    11: 1040, # Part 11
    12: 1098, # Part 12
}


class TableBlock:
    """테이블 블록 데이터 클래스"""
    def __init__(self):
        self.id: str = ""
        self.title: str = ""
        self.forming_part: str = ""
        self.content_lines: list = []
        self.notes: list = []
        self.is_flat: bool = False
        self.page_hint: Optional[int] = None  # PDF 페이지 힌트

    def __repr__(self):
        return f"TableBlock({self.id}, flat={self.is_flat}, notes={len(self.notes)})"


def parse_md_tables(md_path: Path) -> list[TableBlock]:
    """MD 파일에서 테이블 블록 파싱"""

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    tables = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 테이블 시작 감지 - 모든 패턴:
        # - ### Table ...
        # - ### **Table ...**
        # - **Table ...** (볼드 텍스트)
        # (Cont'd) 테이블은 건너뛰기
        if "(Cont'd)" in line or "(Cont'd)" in line:
            i += 1
            continue

        # 패턴 1: ### Table 또는 ### **Table
        table_match = re.match(r'^###\s+\*?\*?Table\s+(\d+\.\d+\.\d+\.\d+\.?-?[A-Z]?)', line)

        # 패턴 2: **Table ...** (볼드 텍스트, ### 없음)
        if not table_match:
            table_match = re.match(r'^\*\*Table\s+(\d+\.\d+\.\d+\.\d+\.?-?[A-Z]?)', line)

        if table_match:
            table = TableBlock()
            table.id = table_match.group(1)

            # Pattern A: 한 줄에 Title + Forming Part
            if 'Forming Part' in line:
                # Title 추출
                title_match = re.search(r'Table\s+[\d.\-A-Z]+\s+(.+?)\s*\*?\*?\s*Forming Part', line)
                if title_match:
                    table.title = title_match.group(1).strip('*').strip()

                # Forming Part 추출
                forming_match = re.search(r'Forming Part of Sentences?\s+([\d.,()\s]+)', line)
                if forming_match:
                    table.forming_part = forming_match.group(1).strip()

                i += 1
            else:
                # Pattern B: 여러 줄
                i += 1
                while i < len(lines):
                    curr_line = lines[i].strip()

                    # 빈 줄 건너뛰기
                    if not curr_line:
                        i += 1
                        continue

                    # Title (** 로 감싸진 줄)
                    if curr_line.startswith('**') and not 'Notes' in curr_line:
                        table.title = curr_line.strip('*').strip()
                        i += 1
                        continue

                    # Forming Part (* 로 감싸진 줄)
                    if 'Forming Part' in curr_line:
                        forming_match = re.search(r'Forming Part of Sentences?\s+([\d.,()\s]+)', curr_line)
                        if forming_match:
                            table.forming_part = forming_match.group(1).strip()
                        i += 1
                        continue

                    # 테이블 콘텐츠 시작
                    break

            # 테이블 콘텐츠 캡처 (Notes 또는 다음 섹션까지)
            content_lines = []
            while i < len(lines):
                curr_line = lines[i]

                # Notes to Table 시작
                if 'Notes to Table' in curr_line:
                    break

                # 다음 섹션/테이블 시작
                if curr_line.startswith('### ') or curr_line.startswith('## '):
                    break

                # 이미지 참조 건너뛰기
                if curr_line.strip().startswith('![]'):
                    i += 1
                    continue

                content_lines.append(curr_line)
                i += 1

            table.content_lines = content_lines

            # Flat text 감지
            content_text = '\n'.join(content_lines)
            has_pipe_table = bool(re.search(r'^\|.+\|', content_text, re.MULTILINE))
            has_long_text = len(content_text.replace('\n', '').replace(' ', '')) > 200

            if not has_pipe_table and has_long_text:
                table.is_flat = True

            # Notes 캡처
            if i < len(lines) and 'Notes to Table' in lines[i]:
                i += 1
                while i < len(lines):
                    curr_line = lines[i].strip()

                    # 다음 섹션 시작
                    if curr_line.startswith('### ') or curr_line.startswith('## '):
                        break

                    # 이미지 참조 건너뛰기
                    if curr_line.startswith('![]'):
                        i += 1
                        continue

                    # Note 항목 캡처
                    note_match = re.match(r'^-?\s*\((\d+)\)\s*(.+)', curr_line)
                    if note_match:
                        note_num = note_match.group(1)
                        note_text = note_match.group(2).strip()
                        table.notes.append((note_num, note_text))

                    i += 1

            tables.append(table)
        else:
            i += 1

    return tables


def pipe_table_to_html(lines: list[str]) -> str:
    """Markdown Pipe 테이블 → HTML 변환"""

    # 실제 테이블 라인만 필터링
    table_lines = [l.strip() for l in lines if l.strip().startswith('|')]

    if len(table_lines) < 2:
        return ""

    # 헤더 파싱
    headers = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]

    # 구분선 확인 후 데이터 시작 위치 결정
    data_start = 1
    if len(table_lines) > 1 and re.match(r'^\|[\s\-:]+\|', table_lines[1]):
        data_start = 2

    # 데이터 행 파싱
    rows = []
    for line in table_lines[data_start:]:
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        rows.append(cells)

    # HTML 생성
    html_parts = ['<table class="obc-table">']

    # Header
    html_parts.append('<thead><tr>')
    for h in headers:
        html_parts.append(f'<th>{h}</th>')
    html_parts.append('</tr></thead>')

    # Body
    html_parts.append('<tbody>')
    for row in rows:
        html_parts.append('<tr>')
        for cell in row:
            html_parts.append(f'<td>{cell}</td>')
        html_parts.append('</tr>')
    html_parts.append('</tbody>')

    html_parts.append('</table>')

    return ''.join(html_parts)


def extract_table_with_pdfplumber(table_id: str, part_num: int = 8) -> Optional[str]:
    """pdfplumber로 테이블 추출"""

    # 테이블 ID에서 페이지 힌트 추출 (나중에 매핑 테이블로 대체)
    # 임시: Part 8의 알려진 테이블 페이지 매핑
    table_page_map = {
        "8.2.1.3.-A": 682,   # Page 683 (0-indexed: 682)
        "8.2.1.3.-B": 683,   # Page 684
        "8.2.1.5.": 685,     # Page 686
        "8.2.1.6.-A": 686,
        "8.2.1.6.-B": 686,
        "8.2.1.6.-C": 687,
        "8.7.2.3.": 710,
        "8.7.3.1.": 711,
        "8.7.3.2.": 712,
        "8.7.3.4.": 713,
    }

    page_num = table_page_map.get(table_id)
    if page_num is None:
        print(f"  [WARN]  페이지 매핑 없음: {table_id}")
        return None

    try:
        with pdfplumber.open(PDF_PATH) as pdf:
            page = pdf.pages[page_num]
            tables = page.extract_tables()

            if not tables:
                print(f"  [WARN]  테이블 없음: {table_id} (page {page_num + 1})")
                return None

            # 첫 번째 테이블 사용 (여러 개면 나중에 개선)
            table_data = tables[0]

            # HTML 생성
            html_parts = ['<table class="obc-table">']

            # 첫 행을 헤더로
            if table_data:
                html_parts.append('<thead><tr>')
                for cell in table_data[0]:
                    cell_text = cell if cell else ''
                    html_parts.append(f'<th>{cell_text}</th>')
                html_parts.append('</tr></thead>')

                # 나머지는 바디
                html_parts.append('<tbody>')
                for row in table_data[1:]:
                    html_parts.append('<tr>')
                    for cell in row:
                        cell_text = cell if cell else ''
                        html_parts.append(f'<td>{cell_text}</td>')
                    html_parts.append('</tr>')
                html_parts.append('</tbody>')

            html_parts.append('</table>')

            return ''.join(html_parts)

    except Exception as e:
        print(f"  [ERROR] pdfplumber 오류: {table_id} - {e}")
        return None


def format_table_block(table: TableBlock, part_num: int = 8) -> str:
    """테이블 블록을 Part 11 형식으로 변환 (SectionView 호환)"""

    parts = []

    # 1. 테이블 제목 (Part 11 형식: 한 줄에 모두!)
    title_text = table.title or ""
    forming_text = f"Forming Part of Sentence {table.forming_part}" if table.forming_part else ""

    # #### Table ID Title Forming Part of... (모두 한 줄!)
    header_line = f'#### Table {table.id} {title_text}'
    if forming_text:
        header_line += f' {forming_text}'
    parts.append(header_line)
    parts.append('')  # 빈 줄

    # 2. 테이블 본문
    if table.is_flat:
        print(f"  [FLAT] {table.id} -> pdfplumber")
        html_table = extract_table_with_pdfplumber(table.id, part_num)
        if html_table:
            parts.append(html_table)
        else:
            # 실패 시 원본 텍스트 유지
            parts.append(f'<p class="flat-table-warning">[Flat table - needs manual fix]</p>')
            parts.append('\n'.join(table.content_lines))
    else:
        # Pipe table → HTML 변환
        html_table = pipe_table_to_html(table.content_lines)
        if html_table:
            parts.append(html_table)
        else:
            # 변환 실패 시 원본 유지
            parts.append('\n'.join(table.content_lines))

    # 3. Notes (Markdown 형식 - SectionView 호환)
    if table.notes:
        parts.append('')  # 빈 줄
        parts.append(f'Notes to Table {table.id}:')
        parts.append('')
        for num, text in table.notes:
            parts.append(f'- ({num}) {text}')  # 대시 필수!

    return '\n\n'.join(parts)


def analyze_tables(md_path: Path):
    """테이블 분석 (디버그용)"""

    print(f"\n{'='*60}")
    print(f"[FILE] {md_path.name}")
    print(f"{'='*60}\n")

    tables = parse_md_tables(md_path)

    flat_count = 0
    pipe_count = 0

    for table in tables:
        status = "[FLAT]" if table.is_flat else "[PIPE]"
        if table.is_flat:
            flat_count += 1
        else:
            pipe_count += 1

        print(f"{status} Table {table.id}")
        print(f"       Title: {table.title[:50]}..." if len(table.title) > 50 else f"       Title: {table.title}")
        print(f"       Forming: {table.forming_part}")
        print(f"       Notes: {len(table.notes)}")
        print()

    print(f"{'='*60}")
    print(f"[SUMMARY] Pipe={pipe_count}, Flat={flat_count}, Total={len(tables)}")
    print(f"{'='*60}\n")

    return tables


def export_tables_json(tables: list[TableBlock], part_num: int = 8) -> dict:
    """테이블을 JSON 형식으로 내보내기"""

    result = {
        "part": part_num,
        "tables": []
    }

    for table in tables:
        formatted_html = format_table_block(table, part_num)

        table_entry = {
            "id": f"Table {table.id}",
            "subsection_id": '.'.join(table.id.replace('-', '.').split('.')[:3]),  # 8.2.1.3.-A → 8.2.1
            "title": table.title,
            "forming_part": table.forming_part,
            "html": formatted_html,
            "notes_count": len(table.notes),
            "extraction_method": "pdfplumber" if table.is_flat else "markdown"
        }
        result["tables"].append(table_entry)

    return result


def update_part_json(part_num: int, tables_data: dict):
    """part{n}.json 파일의 테이블 업데이트"""

    json_path = OUTPUT_DIR / f"part{part_num}.json"

    if not json_path.exists():
        print(f"[ERROR] JSON 없음: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 테이블 ID → HTML 매핑
    table_html_map = {}
    for t in tables_data["tables"]:
        table_html_map[t["id"]] = t["html"]

    updated_count = 0

    # 각 subsection의 content에서 테이블 교체
    for section in data.get("sections", []):
        for subsection in section.get("subsections", []):
            content = subsection.get("content", "")

            for table_id, new_html in table_html_map.items():
                # 기존 테이블 패턴 찾기
                # <h4 class="table-title">Table 8.2.1.3.-A...까지 Notes 끝까지
                table_num = table_id.replace("Table ", "")
                pattern = rf'<h4 class="table-title">{re.escape(table_id)}.*?(?=<h4 class="table-title">|\[ARTICLE:|$)'

                if re.search(pattern, content, re.DOTALL):
                    content = re.sub(pattern, new_html + "\n\n", content, flags=re.DOTALL)
                    updated_count += 1
                    print(f"  [UPDATED] {table_id} in {subsection['id']}")

            subsection["content"] = content

    # 저장
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n[SAVED] {json_path}")
    print(f"[TOTAL] {updated_count} tables updated")


def main():
    """메인 실행"""

    import sys

    # Part 8 기본
    part_num = 8
    mode = "analyze"  # analyze, export, update

    args = sys.argv[1:]
    if '--part' in args:
        idx = args.index('--part')
        part_num = int(args[idx + 1])
    if '--export' in args:
        mode = "export"
    if '--update' in args:
        mode = "update"

    md_path = MARKER_DIR / f"part{part_num}.md"

    if not md_path.exists():
        print(f"[ERROR] 파일 없음: {md_path}")
        return

    # 테이블 파싱
    tables = parse_md_tables(md_path)

    if mode == "analyze":
        # 분석만
        analyze_tables(md_path)

    elif mode == "export":
        # JSON 내보내기
        analyze_tables(md_path)
        tables_data = export_tables_json(tables, part_num)

        output_path = OUTPUT_DIR / f"part{part_num}_tables_hybrid.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tables_data, f, ensure_ascii=False, indent=2)

        print(f"\n[EXPORTED] {output_path}")
        print(f"[TOTAL] {len(tables_data['tables'])} tables")

    elif mode == "update":
        # 직접 JSON 업데이트
        print("\n" + "="*60)
        print(f"[UPDATE] part{part_num}.json")
        print("="*60 + "\n")

        tables_data = export_tables_json(tables, part_num)
        update_part_json(part_num, tables_data)


if __name__ == "__main__":
    main()
