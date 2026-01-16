"""
Ontario Building Code Part 9 파싱 스크립트 v4
- 페이지 번호 필터링 강화 (1-2자리 포함)
- 헤더/풋터 섹션 참조 번호 제거
- 중복 섹션 번호 제거
- 잘못된 헤딩 정리
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


def is_page_number(text: str, page_range: Tuple[int, int] = (1, 1000)) -> bool:
    """
    텍스트가 페이지 번호인지 확인
    - 단독으로 존재하는 1-3자리 숫자
    - 합리적인 페이지 범위 내
    """
    text = text.strip()
    if re.match(r'^\d{1,3}$', text):
        num = int(text)
        return page_range[0] <= num <= page_range[1]
    return False


def is_header_footer_section_ref(text: str) -> bool:
    """
    헤더/풋터의 섹션 참조 번호인지 확인
    예: "9.3.1.6." (줄 시작에 섹션 번호만 있는 경우)
    """
    text = text.strip()
    # 단독 섹션 번호 패턴 (내용 없이 번호만)
    if re.match(r'^9\.\d+\.\d+\.\d*\.?$', text):
        return True
    return False


def clean_duplicate_section_numbers(text: str) -> str:
    """
    중복된 섹션 번호 제거
    예: "9.3.1.7. 9.3.1.7. Concrete Mixes" → "9.3.1.7. Concrete Mixes"
    예: "9.8.2.2.9.8.2.2. Height Over Stairs" → "9.8.2.2. Height Over Stairs"
    """
    # 패턴 1: "9.x.x.x. 9.x.x.x. Title" (공백으로 구분된 중복)
    text = re.sub(
        r'(9\.\d+\.\d+\.\d+\.)\s+\1\s*',
        r'\1 ',
        text
    )

    # 패턴 2: "9.x.x.x.9.x.x.x. Title" (공백 없이 붙어있는 중복)
    text = re.sub(
        r'(9\.\d+\.\d+\.\d+\.)(9\.\d+\.\d+\.\d+\.)\s*',
        r'\1 ',
        text
    )

    # 패턴 3: Subsection 레벨 중복 "9.x.x. 9.x.x. Title"
    text = re.sub(
        r'(9\.\d+\.\d+\.)\s+\1\s*',
        r'\1 ',
        text
    )

    return text


def clean_orphan_section_refs(text: str) -> str:
    """
    내용 없이 단독으로 존재하는 섹션 참조 제거
    예: 줄 전체가 "9.20.17.2. to 9.20.17.4.)" 같은 경우
    """
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        # 빈 줄은 유지
        if not stripped:
            cleaned_lines.append(line)
            continue

        # 단독 섹션 참조 번호 (내용 없음)
        if re.match(r'^9\.\d+\.\d+\.\d*\.?$', stripped):
            continue

        # 잘못 분리된 참조 (예: "9.20.17.2. to 9.20.17.4.)")
        if re.match(r'^9\.\d+\.\d+\.\d+\.\s*to\s+9\.\d+\.\d+\.\d+\.\)?$', stripped):
            continue

        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def group_blocks_by_row(blocks: List, y_tolerance: float = 5.0) -> List[List]:
    """
    같은 y좌표의 블록들을 그룹화 (테이블 행 처리)
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
            current_row.append(block)
        else:
            if current_row:
                current_row.sort(key=lambda b: b[0])
                rows.append(current_row)
            current_row = [block]
            current_y = block_y

    if current_row:
        current_row.sort(key=lambda b: b[0])
        rows.append(current_row)

    return rows


def extract_page_text_sorted(doc, page_num: int, page_height: float = 0) -> str:
    """
    블록 정렬을 적용한 텍스트 추출
    - 헤더/풋터 영역 제거 (상단 50px, 하단 50px)
    - 페이지 번호 및 섹션 참조 필터링
    """
    if page_num < 1 or page_num > len(doc):
        return ""

    page = doc[page_num - 1]
    blocks = page.get_text("blocks")
    page_rect = page.rect
    page_height = page_rect.height

    # 헤더/풋터 영역 제외 (상단 60px, 하단 60px)
    HEADER_MARGIN = 60
    FOOTER_MARGIN = 60

    filtered_blocks = []
    for b in blocks:
        y0, y1 = b[1], b[3]
        # 헤더/풋터 영역 제외
        if y0 < HEADER_MARGIN or y1 > (page_height - FOOTER_MARGIN):
            continue
        filtered_blocks.append(b)

    rows = group_blocks_by_row(filtered_blocks, y_tolerance=5.0)

    lines = []
    for row in rows:
        row_texts = []
        for block in row:
            text = block[4].strip()
            if text:
                text = text.replace('\n', ' ').strip()

                # 페이지 번호 필터링 (단독 1-3자리 숫자)
                if is_page_number(text, (1, 999)):
                    continue

                # 헤더/풋터 섹션 참조 필터링
                if is_header_footer_section_ref(text):
                    continue

                row_texts.append(text)

        if row_texts:
            if len(row_texts) > 1:
                lines.append("  ".join(row_texts))
            else:
                lines.append(row_texts[0])

    text = "\n".join(lines)

    # 추가 클린업
    # 1. 헤더/푸터 텍스트 제거
    text = re.sub(r'2024 Building Code Compendium\s*', '', text)
    text = re.sub(r'Division B\s*[–-]\s*Part 9\s*', '', text)

    # 2. 중복 섹션 번호 제거
    text = clean_duplicate_section_numbers(text)

    # 3. 단독 섹션 참조 제거
    text = clean_orphan_section_refs(text)

    # 4. 연속 빈 줄 정리
    text = re.sub(r'\n{3,}', '\n\n', text)

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
    """
    # 시작점: 현재 subsection ID 찾기
    start_pattern = rf'{re.escape(sub_id)}\.\s*\n'
    start_match = re.search(start_pattern, full_text)

    if not start_match:
        start_pattern = rf'{re.escape(sub_id)}\.\s+'
        start_match = re.search(start_pattern, full_text)

    if not start_match:
        return ""

    start = start_match.start()

    # 끝점 찾기
    end = len(full_text)

    if next_sub_id:
        end_pattern = rf'{re.escape(next_sub_id)}\.\s*'
        end_match = re.search(end_pattern, full_text[start + 10:])
        if end_match:
            end = start + 10 + end_match.start()
    else:
        section_parts = sub_id.split('.')
        if len(section_parts) >= 2:
            next_section_num = int(section_parts[1]) + 1
            end_pattern = rf'Section 9\.{next_section_num}\.\s+'
            end_match = re.search(end_pattern, full_text[start + 10:])
            if end_match:
                end = start + 10 + end_match.start()

    content = full_text[start:end].strip()

    # 최종 클린업
    content = clean_duplicate_section_numbers(content)
    content = clean_orphan_section_refs(content)
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content


def find_next_subsection_id(toc_items: List[Dict], current_idx: int, current_section_id: str) -> Optional[str]:
    """현재 subsection 다음의 subsection ID 찾기"""
    for j in range(current_idx + 1, len(toc_items)):
        next_id, _ = parse_article_id(toc_items[j]['title'])
        if not next_id:
            continue

        parts = next_id.split('.')

        if len(parts) == 3 and next_id.startswith(current_section_id + '.'):
            return next_id

        if len(parts) >= 2 and not next_id.startswith(current_section_id + '.'):
            return None

    return None


def build_structure(toc_items: List[Dict], doc) -> Dict:
    """TOC 기반으로 계층 구조 생성"""
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
                next_sub_id = find_next_subsection_id(toc_items, i, current_section['id'])

                next_page = page + 1
                for j in range(i + 1, len(toc_items)):
                    next_item_id, _ = parse_article_id(toc_items[j]['title'])
                    if next_item_id and len(next_item_id.split('.')) <= 3:
                        next_page = toc_items[j]['page']
                        break

                full_text = extract_pages_text(doc, page, min(next_page, page + 15))
                content = extract_subsection_content(full_text, article_id, next_sub_id)

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
    """검색 인덱스 생성"""
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


def validate_content(data: Dict) -> List[str]:
    """데이터 품질 검증"""
    issues = []

    for section in data['sections']:
        for subsection in section.get('subsections', []):
            content = subsection.get('content', '')
            sub_id = subsection['id']

            # 1. 페이지 번호 잔존 확인
            page_nums = re.findall(r'^\s*(\d{1,3})\s*$', content, re.MULTILINE)
            for num in page_nums:
                if 1 <= int(num) <= 999:
                    issues.append(f"[{sub_id}] 페이지 번호 잔존: '{num}'")

            # 2. 중복 섹션 번호 확인
            duplicates = re.findall(r'(9\.\d+\.\d+\.\d+\.)\s*\1', content)
            for dup in duplicates:
                issues.append(f"[{sub_id}] 중복 섹션 번호: '{dup}'")

            # 3. 단독 섹션 참조 확인
            orphans = re.findall(r'^\s*(9\.\d+\.\d+\.\d*\.?)\s*$', content, re.MULTILINE)
            for orphan in orphans:
                issues.append(f"[{sub_id}] 단독 섹션 참조: '{orphan}'")

    return issues


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

    # 2. 구조화
    print("\n2. 구조화 중 (v4: 강화된 필터링)...")
    part9_data = build_structure(toc_items, doc)
    print(f"   섹션 수: {len(part9_data['sections'])}")

    total_subsections = sum(
        len(sec.get('subsections', []))
        for sec in part9_data['sections']
    )
    print(f"   총 Subsection 수: {total_subsections}")

    # 3. 데이터 품질 검증
    print("\n3. 데이터 품질 검증 중...")
    issues = validate_content(part9_data)
    if issues:
        print(f"   ⚠️ 발견된 문제: {len(issues)}개")
        for issue in issues[:10]:  # 최대 10개만 출력
            print(f"      - {issue}")
        if len(issues) > 10:
            print(f"      ... 외 {len(issues) - 10}개")
    else:
        print("   ✓ 문제 없음")

    # 4. 검색 인덱스 생성
    print("\n4. 검색 인덱스 생성 중...")
    search_index = create_search_index(part9_data)
    print(f"   인덱스 항목 수: {len(search_index)}")

    # 5. 목차 생성
    print("\n5. 목차 생성 중...")
    toc = create_toc(part9_data)

    # 6. 저장
    print("\n6. JSON 저장 중...")
    save_json(part9_data, 'part9.json')
    save_json(search_index, 'part9-index.json')
    save_json(toc, 'toc.json')

    # 7. 검증용 샘플 출력
    print("\n=== 검증: 문제였던 섹션들 ===")

    problem_sections = ['9.3', '9.10']
    for section in part9_data['sections']:
        if section['id'] in problem_sections:
            print(f"\n{section['id']}: {section['title']}")
            for subsec in section.get('subsections', [])[:2]:  # 각 섹션당 2개만
                content_preview = subsec.get('content', '')[:200].replace('\n', ' ')
                print(f"  └─ {subsec['id']}: {subsec['title']}")
                print(f"     미리보기: {content_preview[:150]}...")

    doc.close()
    print("\n완료!")


if __name__ == "__main__":
    main()
