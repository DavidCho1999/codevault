"""
Ontario Building Code Part 9 파싱 스크립트 v3
- 블록 정렬: 텍스트 순서 보장
- 정규식 분리: 섹션 경계 정확히 분리
"""

import fitz
import os
import sys
import re
import json
from typing import List, Dict, Tuple, Optional

sys.stdout.reconfigure(encoding='utf-8')

# 경로 설정
BASE_PATH = "../source/2024 Building Code Compendium"
PDF_FILE = "301880.pdf"
OUTPUT_DIR = "./output"


def get_toc_part9(doc) -> List[Dict]:
    """PDF TOC에서 Part 9 관련 항목만 추출"""
    toc = doc.get_toc()
    part9_items = []

    for level, title, page in toc:
        if (title.startswith("9.") or
            title.startswith("Part 9") or
            title.startswith("Section 9.")):
            title = title.replace('\u2003', ' ').replace('\u2002', ' ').strip()
            part9_items.append({
                'level': level,
                'title': title,
                'page': page
            })

    return part9_items


def parse_article_id(title: str) -> Tuple[str, str]:
    """제목에서 Article ID와 이름 분리"""
    # 패턴: "9.10.3.1. Title" 또는 "9.10.3.1A. Title"
    match = re.match(r'^(9\.\d+\.\d+\.\d+[A-Z]?)\.\s*(.+)$', title)
    if match:
        return match.group(1), match.group(2)

    # 패턴: "9.10.3. Title" (Subsection)
    match = re.match(r'^(9\.\d+\.\d+)\.\s*(.+)$', title)
    if match:
        return match.group(1), match.group(2)

    # 패턴: "Section 9.10. Title"
    match = re.match(r'^Section\s+(9\.\d+)\.\s*(.+)$', title)
    if match:
        return match.group(1), match.group(2)

    return "", title


def group_blocks_by_row(blocks: List, y_tolerance: float = 5.0) -> List[List]:
    """
    같은 y좌표의 블록들을 그룹화 (테이블 행 처리)
    - y_tolerance: 같은 행으로 간주할 y좌표 허용 오차 (픽셀)
    """
    if not blocks:
        return []

    # 텍스트 블록만 필터링하고 y좌표로 정렬
    text_blocks = [b for b in blocks if b[6] == 0]
    text_blocks.sort(key=lambda b: (b[1], b[0]))  # y → x 정렬

    rows = []
    current_row = []
    current_y = None

    for block in text_blocks:
        block_y = block[1]  # y0 좌표

        if current_y is None:
            current_y = block_y
            current_row = [block]
        elif abs(block_y - current_y) <= y_tolerance:
            # 같은 행
            current_row.append(block)
        else:
            # 새 행 시작
            if current_row:
                # 현재 행을 x좌표로 정렬
                current_row.sort(key=lambda b: b[0])
                rows.append(current_row)
            current_row = [block]
            current_y = block_y

    # 마지막 행 추가
    if current_row:
        current_row.sort(key=lambda b: b[0])
        rows.append(current_row)

    return rows


def extract_page_text_sorted(doc, page_num: int) -> str:
    """
    블록 정렬을 적용한 텍스트 추출
    - 같은 y좌표의 블록들을 한 줄로 합침 (테이블 지원)
    - y좌표(위→아래) → x좌표(왼→오른쪽) 순으로 정렬
    """
    if page_num < 1 or page_num > len(doc):
        return ""

    page = doc[page_num - 1]
    blocks = page.get_text("blocks")

    # 블록을 행별로 그룹화
    rows = group_blocks_by_row(blocks, y_tolerance=5.0)

    # 각 행의 블록들을 탭으로 연결
    lines = []
    for row in rows:
        row_texts = []
        for block in row:
            text = block[4].strip()
            if text:
                # 블록 내 줄바꿈을 공백으로 변환 (테이블 셀 내용 보존)
                text = text.replace('\n', ' ').strip()
                row_texts.append(text)

        if row_texts:
            # 같은 행의 셀들을 2개 공백으로 구분 (테이블 형식)
            if len(row_texts) > 1:
                lines.append("  ".join(row_texts))
            else:
                lines.append(row_texts[0])

    text = "\n".join(lines)

    # 헤더/푸터 제거
    text = re.sub(r'2024 Building Code Compendium\s*', '', text)
    text = re.sub(r'Division B – Part 9\s*\d*\s*', '', text)
    # 페이지 번호 제거 (3자리 이상 숫자만, 테이블 데이터 보존)
    text = re.sub(r'^\s*\d{3,}\s*$', '', text, flags=re.MULTILINE)

    return text.strip()


def extract_pages_text(doc, start_page: int, end_page: int) -> str:
    """여러 페이지 텍스트를 블록 정렬 후 추출"""
    all_text = []
    for p in range(start_page, end_page + 1):
        page_text = extract_page_text_sorted(doc, p)
        if page_text:
            all_text.append(page_text)
    return "\n".join(all_text)


def extract_subsection_content(full_text: str, sub_id: str, next_sub_id: Optional[str]) -> str:
    """
    정규식을 사용해 Subsection 범위 내 내용만 추출

    예: sub_id="9.3.1", next_sub_id="9.3.2"
    → "9.3.1." 부터 "9.3.2." 직전까지만 추출
    """
    # 시작점: 현재 subsection ID 찾기
    # 패턴: "9.3.1." 또는 "9.3.1.\n" 형태
    start_pattern = rf'{re.escape(sub_id)}\.\s*\n'
    start_match = re.search(start_pattern, full_text)

    if not start_match:
        # 대안 패턴: "9.3.1. Title" 형태
        start_pattern = rf'{re.escape(sub_id)}\.\s+'
        start_match = re.search(start_pattern, full_text)

    if not start_match:
        return ""

    start = start_match.start()

    # 끝점 찾기
    end = len(full_text)

    if next_sub_id:
        # 다음 subsection으로 끝점 설정
        end_pattern = rf'{re.escape(next_sub_id)}\.\s*'
        end_match = re.search(end_pattern, full_text[start + 10:])
        if end_match:
            end = start + 10 + end_match.start()
    else:
        # 다음 Section 패턴으로 끝점 찾기 (예: "Section 9.4.")
        section_parts = sub_id.split('.')
        if len(section_parts) >= 2:
            next_section_num = int(section_parts[1]) + 1
            end_pattern = rf'Section 9\.{next_section_num}\.\s+'
            end_match = re.search(end_pattern, full_text[start + 10:])
            if end_match:
                end = start + 10 + end_match.start()

    content = full_text[start:end].strip()

    # 중복 줄바꿈 정리
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content


def find_next_subsection_id(toc_items: List[Dict], current_idx: int, current_section_id: str) -> Optional[str]:
    """현재 subsection 다음의 subsection ID 찾기"""
    for j in range(current_idx + 1, len(toc_items)):
        next_id, _ = parse_article_id(toc_items[j]['title'])
        if not next_id:
            continue

        parts = next_id.split('.')

        # 같은 Section 내의 다음 Subsection (예: 9.3.2)
        if len(parts) == 3 and next_id.startswith(current_section_id + '.'):
            return next_id

        # 다른 Section으로 넘어감 (예: 9.4.x)
        if len(parts) >= 2 and not next_id.startswith(current_section_id + '.'):
            return None

    return None


def build_structure(toc_items: List[Dict], doc) -> Dict:
    """TOC 기반으로 계층 구조 생성 (블록 정렬 + 정규식 분리 적용)"""
    result = {
        'id': '9',
        'title': 'Housing and Small Buildings',
        'sections': []
    }

    current_section = None

    for i, item in enumerate(toc_items):
        title = item['title']
        page = item['page']

        article_id, article_title = parse_article_id(title)

        if not article_id:
            continue

        parts = article_id.split('.')

        if len(parts) == 2:  # Section (9.10)
            current_section = {
                'id': article_id,
                'title': article_title,
                'page': page,
                'subsections': []
            }
            result['sections'].append(current_section)

        elif len(parts) == 3:  # Subsection (9.10.1)
            if current_section:
                # 다음 Subsection ID 찾기
                next_sub_id = find_next_subsection_id(toc_items, i, current_section['id'])

                # 페이지 범위 결정
                next_page = page + 1
                for j in range(i + 1, len(toc_items)):
                    next_item_id, _ = parse_article_id(toc_items[j]['title'])
                    if next_item_id and len(next_item_id.split('.')) <= 3:
                        next_page = toc_items[j]['page']
                        break

                # 페이지 범위에서 텍스트 추출 (블록 정렬 적용)
                full_text = extract_pages_text(doc, page, min(next_page, page + 15))

                # 정규식으로 정확한 범위만 추출
                content = extract_subsection_content(full_text, article_id, next_sub_id)

                # content가 비어있으면 전체 텍스트 사용 (fallback)
                if not content:
                    content = full_text

                current_subsection = {
                    'id': article_id,
                    'title': article_title,
                    'page': page,
                    'content': content,
                    'articles': []
                }
                current_section['subsections'].append(current_subsection)

    return result


def create_search_index(data: Dict) -> List[Dict]:
    """검색 인덱스 생성 - Subsection 레벨"""
    index = []

    for section in data['sections']:
        for subsection in section.get('subsections', []):
            index.append({
                'id': subsection['id'],
                'title': subsection['title'],
                'section': section['title'],
                'sectionId': section['id'],
                'content': subsection.get('content', '')[:1000],
                'page': subsection.get('page', 0),
                'path': f"/code/{subsection['id'].replace('.', '-')}"
            })

    return index


def create_toc(data: Dict) -> List[Dict]:
    """사이드바용 목차 생성"""
    toc = []

    for section in data['sections']:
        section_item = {
            'id': section['id'],
            'title': section['title'],
            'children': []
        }

        for subsection in section.get('subsections', []):
            subsec_item = {
                'id': subsection['id'],
                'title': subsection['title'],
                'children': []
            }

            for article in subsection.get('articles', []):
                subsec_item['children'].append({
                    'id': article['id'],
                    'title': article['title']
                })

            section_item['children'].append(subsec_item)

        toc.append(section_item)

    return toc


def save_json(data, filename: str):
    """JSON 파일 저장"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"저장됨: {filepath}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.normpath(os.path.join(script_dir, BASE_PATH, PDF_FILE))

    print(f"PDF 경로: {pdf_path}")

    doc = fitz.open(pdf_path)
    print(f"총 페이지: {len(doc)}")

    # 1. TOC에서 Part 9 항목 추출
    print("\n1. TOC 분석 중...")
    toc_items = get_toc_part9(doc)
    print(f"   Part 9 항목 수: {len(toc_items)}")

    # 2. 구조화 (블록 정렬 + 정규식 분리)
    print("\n2. 구조화 중 (블록 정렬 + 정규식 분리)...")
    part9_data = build_structure(toc_items, doc)
    print(f"   섹션 수: {len(part9_data['sections'])}")

    total_subsections = sum(
        len(sec.get('subsections', []))
        for sec in part9_data['sections']
    )
    print(f"   총 Subsection 수: {total_subsections}")

    # 3. 검색 인덱스 생성
    print("\n3. 검색 인덱스 생성 중...")
    search_index = create_search_index(part9_data)
    print(f"   인덱스 항목 수: {len(search_index)}")

    # 4. 목차 생성
    print("\n4. 목차 생성 중...")
    toc = create_toc(part9_data)

    # 5. 저장
    print("\n5. JSON 저장 중...")
    save_json(part9_data, 'part9.json')
    save_json(search_index, 'part9-index.json')
    save_json(toc, 'toc.json')

    # 6. 검증용 샘플 출력
    print("\n=== 검증: 문제였던 섹션들 ===")

    for section in part9_data['sections']:
        if section['id'] in ['9.2', '9.3']:
            print(f"\n{section['id']}: {section['title']}")
            for subsec in section.get('subsections', []):
                content_preview = subsec.get('content', '')[:150].replace('\n', ' ')
                has_wrong_content = '9.1.1.' in content_preview
                status = "⚠️ 다른 섹션 내용 포함!" if has_wrong_content else "✓"
                print(f"  └─ {subsec['id']}: {subsec['title']}")
                print(f"     {status} 내용 미리보기: {content_preview[:100]}...")

    doc.close()
    print("\n완료!")


if __name__ == "__main__":
    main()
