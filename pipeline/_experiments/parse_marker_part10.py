# -*- coding: utf-8 -*-
"""
Marker 마크다운에서 Part 10 (Change of Use) 파싱
OBC 구조에 맞게 JSON 변환
"""

import re
import json
from pathlib import Path

# 경로 설정
MARKER_FILE = Path("output_marker/301880_full.md")
OUTPUT_FILE = Path("codevault/public/data/part10.json")

def extract_part10_content(md_content: str) -> str:
    """Part 10 내용만 추출 (Part 11 시작 전까지)"""

    # Part 10 시작 찾기
    part10_match = re.search(r'^# Part 10\s*$\s*^# Change of Use', md_content, re.MULTILINE)
    if not part10_match:
        # 대안 패턴
        part10_match = re.search(r'^# Part 10 Change of Use', md_content, re.MULTILINE)

    if not part10_match:
        raise ValueError("Part 10 시작점을 찾을 수 없습니다")

    start_pos = part10_match.start()

    # Part 11 시작점 찾기 (종료 지점)
    part11_match = re.search(r'^# Part 11', md_content[start_pos:], re.MULTILINE)
    if part11_match:
        end_pos = start_pos + part11_match.start()
    else:
        end_pos = len(md_content)

    return md_content[start_pos:end_pos]

def clean_content(text: str) -> str:
    """마크다운 정리"""
    # 이미지 참조 제거
    text = re.sub(r'!\[\]\(_page_\d+_Picture_\d+\.jpeg\)\n*', '', text)
    # span 태그 제거
    text = re.sub(r'<span[^>]*>', '', text)
    text = re.sub(r'</span>', '', text)
    # 파일 링크 제거
    text = re.sub(r'\[([^\]]+)\]\(file://[^)]+\)', r'\1', text)
    # 연속 빈 줄 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def parse_part10(content: str) -> dict:
    """Part 10 구조 파싱"""

    content = clean_content(content)
    lines = content.split('\n')

    result = {
        "id": "10",
        "title": "Change of Use",
        "sections": []
    }

    current_section = None
    current_subsection = None
    current_article = None
    current_content = []

    for line in lines:
        # Part 헤더 스킵
        if re.match(r'^#+ Part 10', line):
            continue
        if re.match(r'^#+ Change of Use', line):
            continue

        # 목차 테이블 스킵 (| 로 시작하고 10.X. 패턴이 첫 셀)
        if line.startswith('|') and re.match(r'\|\s*10\.\d+', line):
            continue

        # Section 헤더: ## Section 10.X. Title 또는 ### Section 10.X. Title
        section_match = re.match(r'^#{2,3}\s*Section\s+(10\.\d+)\.\s*(.*)$', line)
        if section_match:
            save_current_structure(result, current_section, current_subsection,
                                  current_article, current_content)

            current_section = {
                "id": section_match.group(1),
                "title": section_match.group(2).strip(),
                "subsections": []
            }
            current_subsection = None
            current_article = None
            current_content = []
            result["sections"].append(current_section)
            continue

        # Article 헤더 먼저 (4자리): ### 10.X.X.X. Title
        article_match = re.match(r'^#{2,4}\s*(10\.\d+\.\d+\.\d+)\.\s*(.*)$', line)
        if article_match:
            save_current_structure(result, current_section, current_subsection,
                                  current_article, current_content)

            current_article = {
                "id": article_match.group(1),
                "title": article_match.group(2).strip(),
                "content": ""
            }
            current_content = []
            if current_subsection:
                current_subsection["articles"].append(current_article)
            continue

        # Subsection 헤더 (3자리): ### 10.X.X. Title
        subsection_match = re.match(r'^#{2,3}\s*(10\.\d+\.\d+)\.\s*(.*)$', line)
        if subsection_match:
            save_current_structure(result, current_section, current_subsection,
                                  current_article, current_content)

            current_subsection = {
                "id": subsection_match.group(1),
                "title": subsection_match.group(2).strip(),
                "content": "",
                "articles": []
            }
            current_article = None
            current_content = []
            if current_section:
                current_section["subsections"].append(current_subsection)
            continue

        # 일반 콘텐츠
        current_content.append(line)

    # 마지막 구조 저장
    save_current_structure(result, current_section, current_subsection,
                          current_article, current_content)

    return result

def save_current_structure(result, section, subsection, article, content):
    """현재 구조에 콘텐츠 저장"""
    content_text = '\n'.join(content).strip()

    if article and content_text:
        article["content"] = content_text
    elif subsection and content_text and not article:
        subsection["content"] = content_text

def main():
    print("Loading Marker output...")
    md_content = MARKER_FILE.read_text(encoding='utf-8')

    print("Extracting Part 10...")
    part10_content = extract_part10_content(md_content)
    print(f"  Extracted {len(part10_content)} chars")

    print("Parsing structure...")
    result = parse_part10(part10_content)

    # 통계 출력
    print("\n=== Part 10 Structure ===")
    print(f"Sections: {len(result['sections'])}")
    for section in result['sections']:
        print(f"  {section['id']}: {section['title']}")
        for sub in section.get('subsections', []):
            print(f"    {sub['id']}: {sub['title']} ({len(sub.get('content', ''))} chars)")
            for art in sub.get('articles', []):
                print(f"      {art['id']}: {art['title']} ({len(art.get('content', ''))} chars)")

    # JSON 저장
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {OUTPUT_FILE}")

    # 샘플 출력
    print("\n=== Sample Content (10.3.2.2) ===")
    for section in result['sections']:
        for sub in section.get('subsections', []):
            for art in sub.get('articles', []):
                if art['id'] == '10.3.2.2':
                    print(art['content'][:1000])
                    print("...")

if __name__ == "__main__":
    main()
