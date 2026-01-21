"""
Part 10 JSON: Markdown → Plain Text 변환 스크립트

마크다운 형식을 Part 9 스타일의 plain text로 변환합니다.
- ## 제목 → [ARTICLE:id:title] 마커
- - **(1)** → (1)
- - (a) → (a)
- *이탤릭* → 이탤릭 (정의 용어는 유지)
- 마크다운 테이블 → HTML 테이블
"""

import json
import re
from pathlib import Path


def convert_markdown_table_to_html(lines: list, start_idx: int) -> tuple:
    """마크다운 테이블을 HTML로 변환

    Returns: (html_string, end_idx)
    """
    table_lines = []
    i = start_idx

    # 테이블 줄 수집
    while i < len(lines) and lines[i].strip().startswith('|'):
        table_lines.append(lines[i].strip())
        i += 1

    if len(table_lines) < 2:
        return None, start_idx

    # 헤더 행 파싱
    header_line = table_lines[0]
    headers = [cell.strip() for cell in header_line.split('|')[1:-1]]

    # 구분선 확인 (|---|---|)
    if len(table_lines) > 1 and re.match(r'^\|[\s\-:|]+\|$', table_lines[1]):
        data_start = 2
    else:
        data_start = 1

    # HTML 생성
    html = ['<table class="obc-table">']

    # 헤더
    html.append('<thead><tr>')
    for h in headers:
        # <br> 태그 유지, 기타 HTML 이스케이프하지 않음
        html.append(f'<th>{h}</th>')
    html.append('</tr></thead>')

    # 바디
    html.append('<tbody>')
    for row_line in table_lines[data_start:]:
        cells = [cell.strip() for cell in row_line.split('|')[1:-1]]
        html.append('<tr>')
        for cell in cells:
            html.append(f'<td>{cell}</td>')
        html.append('</tr>')
    html.append('</tbody>')

    html.append('</table>')

    # HTML을 한 줄로 출력 (SectionView.tsx에서 줄 분리 문제 방지)
    return ''.join(html), i - 1


def convert_markdown_to_plaintext(content: str) -> str:
    """마크다운 콘텐츠를 plain text로 변환"""
    if not content:
        return content

    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # ## 10.1.1.1. Title → [ARTICLE:10.1.1.1:Title]
        article_match = re.match(r'^##\s+(10\.\d+\.\d+\.\d+\.?)\s*(.*)$', line)
        if article_match:
            article_id = article_match.group(1).rstrip('.')
            article_title = article_match.group(2).strip()
            result.append(f'[ARTICLE:{article_id}:{article_title}]')
            i += 1
            continue

        # ### **Table ... → 테이블 제목 (HTML heading으로 변환, 별도 줄)
        table_title_match = re.match(r'^###\s*\*\*Table\s+(.+?)\*\*\s*$', line.strip())
        if table_title_match:
            title = table_title_match.group(1)
            # 빈 줄 추가하여 이전 텍스트와 분리
            result.append('')
            result.append(f'<h4 class="table-title">Table {title}</h4>')
            i += 1
            continue

        # #### **Notes to Table... → Notes 제목 (별도 줄)
        notes_match = re.match(r'^####\s*\*\*Notes to Table (.+?):\*\*\s*$', line.strip())
        if notes_match:
            table_ref = notes_match.group(1)
            result.append('')
            result.append(f'<h5 class="table-notes-title">Notes to Table {table_ref}:</h5>')
            i += 1
            continue

        # 마크다운 테이블 (|로 시작) → HTML 테이블로 변환 (별도 줄)
        if line.strip().startswith('|'):
            html_table, end_idx = convert_markdown_table_to_html(lines, i)
            if html_table:
                result.append('')  # 빈 줄로 분리
                result.append(html_table)
                result.append('')  # 테이블 뒤에도 빈 줄
                i = end_idx + 1
                continue
            else:
                # 변환 실패 시 그대로 유지
                result.append(line)
                i += 1
                continue

        # - **(1)** text → (1) text
        clause_match = re.match(r'^-\s+\*\*\((\d+)\)\*\*\s*(.*)$', line)
        if clause_match:
            num = clause_match.group(1)
            text = clause_match.group(2)
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            result.append(f'({num}) {text}')
            i += 1
            continue

        # - (a) text → (a) text
        subclause_match = re.match(r'^-\s+\(([a-z])\)\s*(.*)$', line)
        if subclause_match:
            letter = subclause_match.group(1)
            text = subclause_match.group(2)
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            result.append(f'({letter}) {text}')
            i += 1
            continue

        # **(1)** text (리스트 아닌 경우) → (1) text
        standalone_clause = re.match(r'^\*\*\((\d+)\)\*\*\s*(.*)$', line)
        if standalone_clause:
            num = standalone_clause.group(1)
            text = standalone_clause.group(2)
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            result.append(f'({num}) {text}')
            i += 1
            continue

        # 들여쓰기된 - **(2)** 또는 - (a) 처리
        indented_clause = re.match(r'^(\s+)-\s+\*\*\((\d+)\)\*\*\s*(.*)$', line)
        if indented_clause:
            num = indented_clause.group(2)
            text = indented_clause.group(3)
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            result.append(f'({num}) {text}')
            i += 1
            continue

        indented_subclause = re.match(r'^(\s+)-\s+\(([a-z])\)\s*(.*)$', line)
        if indented_subclause:
            letter = indented_subclause.group(2)
            text = indented_subclause.group(3)
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            result.append(f'({letter}) {text}')
            i += 1
            continue

        # (i), (ii) 등 로마 숫자 sub-sub-clause
        roman_match = re.match(r'^(\s*)-?\s*\(([ivx]+)\)\s*(.*)$', line)
        if roman_match:
            roman = roman_match.group(2)
            text = roman_match.group(3)
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            result.append(f'({roman}) {text}')
            i += 1
            continue

        # **r1**, **e2** 등 마커 → 제거
        if re.match(r'^\*\*[re]\d+\*\*$', line.strip()):
            i += 1
            continue

        # 일반 텍스트: 이탤릭 제거
        cleaned = re.sub(r'\*([^*]+)\*', r'\1', line)
        result.append(cleaned)
        i += 1

    return '\n'.join(result)


def convert_part10_json():
    """part10.json 파일 변환"""
    input_path = Path(__file__).parent.parent / 'codevault' / 'public' / 'data' / 'part10.json'

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 각 섹션의 content 변환
    for section in data.get('sections', []):
        for subsection in section.get('subsections', []):
            # subsection.content 변환
            if subsection.get('content'):
                original = subsection['content']
                converted = convert_markdown_to_plaintext(original)
                subsection['content'] = converted
                print(f"Converted subsection: {subsection['id']}")

            # articles 배열 처리
            for article in subsection.get('articles', []):
                if article.get('content'):
                    original = article['content']
                    converted = convert_markdown_to_plaintext(original)
                    article['content'] = converted
                    print(f"Converted article: {article['id']} ({len(original)} -> {len(converted)} chars)")

            # content_format 필드 제거
            if 'content_format' in subsection:
                del subsection['content_format']

    # 저장
    output_path = input_path
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to: {output_path}")


if __name__ == '__main__':
    convert_part10_json()
