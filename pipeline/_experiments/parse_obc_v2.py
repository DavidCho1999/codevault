"""
Ontario Building Code Part 9 파싱 스크립트 v2
PDF의 TOC(목차)를 기반으로 정확한 구조화
"""

import fitz
import os
import sys
import re
import json
from typing import List, Dict, Tuple

sys.stdout.reconfigure(encoding='utf-8')

# 경로 설정
BASE_PATH = "../../source/2024 Building Code Compendium"
PDF_FILE = "301880.pdf"
OUTPUT_DIR = "./output"


def get_toc_part9(doc) -> List[Dict]:
    """PDF TOC에서 Part 9 관련 항목만 추출"""
    toc = doc.get_toc()
    part9_items = []

    for level, title, page in toc:
        # Part 9 관련 항목만 필터링
        if (title.startswith("9.") or
            title.startswith("Part 9") or
            title.startswith("Section 9.")):
            # 특수문자 정리
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


def extract_page_text(doc, page_num: int) -> str:
    """특정 페이지의 텍스트 추출 및 정리"""
    if page_num < 1 or page_num > len(doc):
        return ""

    page = doc[page_num - 1]  # 0-indexed
    text = page.get_text()

    # 헤더/푸터 제거
    text = re.sub(r'2024 Building Code Compendium\s*', '', text)
    text = re.sub(r'Division B – Part 9\s*\d*\s*', '', text)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)

    return text.strip()


def build_structure(toc_items: List[Dict], doc) -> Dict:
    """TOC 기반으로 계층 구조 생성"""
    result = {
        'id': '9',
        'title': 'Housing and Small Buildings',
        'sections': []
    }

    current_section = None
    current_subsection = None

    for i, item in enumerate(toc_items):
        title = item['title']
        page = item['page']
        level = item['level']

        article_id, article_title = parse_article_id(title)

        if not article_id:
            continue

        # ID 구조 분석
        parts = article_id.split('.')

        if len(parts) == 2:  # Section (9.10)
            current_section = {
                'id': article_id,
                'title': article_title,
                'page': page,
                'subsections': []
            }
            result['sections'].append(current_section)
            current_subsection = None

        elif len(parts) == 3:  # Subsection (9.10.1)
            if current_section:
                # 다음 항목의 페이지 찾기
                next_page = page + 1
                for j in range(i + 1, len(toc_items)):
                    next_item_id, _ = parse_article_id(toc_items[j]['title'])
                    if next_item_id and len(next_item_id.split('.')) <= 3:
                        next_page = toc_items[j]['page']
                        break

                # 페이지 범위에서 내용 추출
                content = ""
                for p in range(page, min(next_page, page + 10)):  # 최대 10페이지
                    content += extract_page_text(doc, p) + "\n"

                current_subsection = {
                    'id': article_id,
                    'title': article_title,
                    'page': page,
                    'content': content.strip(),
                    'articles': []
                }
                current_section['subsections'].append(current_subsection)

    return result


def extract_article_content(full_text: str, article_id: str) -> str:
    """전체 텍스트에서 특정 Article 내용만 추출"""
    # Article ID 패턴으로 시작 위치 찾기
    escaped_id = re.escape(article_id)
    pattern = rf'{escaped_id}[A-Z]?\.\s+'

    match = re.search(pattern, full_text)
    if not match:
        return ""

    start = match.end()

    # 다음 Article ID까지 추출
    next_pattern = r'9\.\d+\.\d+\.\d+[A-Z]?\.\s+'
    next_match = re.search(next_pattern, full_text[start:])

    if next_match:
        end = start + next_match.start()
    else:
        end = min(start + 2000, len(full_text))  # 최대 2000자

    content = full_text[start:end].strip()

    # 문장 단위로 정리
    content = re.sub(r'\n+', '\n', content)

    return content


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

    # 2. 구조화
    print("\n2. 구조화 중...")
    part9_data = build_structure(toc_items, doc)
    print(f"   섹션 수: {len(part9_data['sections'])}")

    total_articles = sum(
        len(sub.get('articles', []))
        for sec in part9_data['sections']
        for sub in sec.get('subsections', [])
    )
    print(f"   총 Article 수: {total_articles}")

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

    # 6. 샘플 출력
    print("\n=== 구조 샘플 ===")
    for section in part9_data['sections'][:5]:
        print(f"\n{section['id']}: {section['title']}")
        for subsec in section.get('subsections', [])[:2]:
            print(f"  └─ {subsec['id']}: {subsec['title']}")
            for article in subsec.get('articles', [])[:2]:
                content_preview = article.get('content', '')[:80].replace('\n', ' ')
                print(f"      └─ {article['id']}: {article['title']}")
                print(f"         {content_preview}...")

    doc.close()
    print("\n완료!")


if __name__ == "__main__":
    main()
