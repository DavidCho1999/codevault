# -*- coding: utf-8 -*-
"""
Marker 마크다운에서 Part 12 (Resource Conservation) 파싱
OBC 구조에 맞게 JSON 변환
"""

import re
import json
from pathlib import Path

# 경로 설정
MARKER_FILE = Path("output_marker/301880_full_normalized.md")  # normalized 버전 사용
OUTPUT_FILE = Path("codevault/public/data/part12.json")

def extract_part12_content(md_content: str) -> str:
    """Part 12 내용만 추출 (Division C 시작 전까지)"""

    # Part 12 시작 찾기 - 두 번째 Part 12 (첫 번째는 목차)
    matches = list(re.finditer(r'^# Part 12\s*$', md_content, re.MULTILINE))
    if len(matches) < 2:
        # 대안: Resource Conservation으로 시작점 찾기
        part12_match = re.search(r'^# Part 12.*$\s*^# Resource Conservation', md_content, re.MULTILINE)
        if part12_match:
            start_pos = part12_match.start()
        else:
            raise ValueError("Part 12 시작점을 찾을 수 없습니다")
    else:
        start_pos = matches[1].start()  # 두 번째 "# Part 12" 사용

    # Division C 또는 다음 Part 시작점 찾기 (종료 지점)
    end_match = re.search(r'^# Division C', md_content[start_pos:], re.MULTILINE)
    if end_match:
        end_pos = start_pos + end_match.start()
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

def normalize_markdown(text: str) -> str:
    """마크다운 헤딩을 정규화 - 헤딩 제거하고 일반 텍스트로"""
    # #### Article 헤딩을 볼드 + 줄바꿈으로 변환
    text = re.sub(r'^#{1,4}\s*(12\.\d+\.\d+\.\d+)\.\s*(.*)$', r'**\1. \2**\n', text, flags=re.MULTILINE)
    # Section 헤딩 제거 (구조는 JSON으로 표현됨)
    text = re.sub(r'^#{1,4}\s*Section\s+12\.\d+\..*$', '', text, flags=re.MULTILINE)
    # 남은 마크다운 헤딩 정리
    text = re.sub(r'^#{1,4}\s+', '', text, flags=re.MULTILINE)
    return text

def parse_part12(content: str) -> dict:
    """Part 12 구조 파싱"""

    content = clean_content(content)
    lines = content.split('\n')

    result = {
        "id": "12",
        "title": "Resource Conservation and Environmental Integrity",
        "sections": []
    }

    current_section = None
    current_subsection = None
    current_content = []

    for line in lines:
        # Part 헤더 스킵
        if re.match(r'^#+ Part 12', line):
            continue
        if re.match(r'^#+ Resource Conservation', line):
            continue

        # 목차 테이블 스킵 (| 로 시작하고 12.X. 패턴이 첫 셀)
        if line.startswith('|') and re.match(r'\|\s*12\.\d+', line):
            continue
        if line.startswith('|') and '---' in line:
            continue

        # Section 헤더: ## Section 12.X. Title
        section_match = re.match(r'^#{2,3}\s*Section\s+(12\.\d+)\.\s*(.*)$', line)
        if section_match:
            save_current_structure(result, current_section, current_subsection, current_content)

            current_section = {
                "id": section_match.group(1),
                "title": section_match.group(2).strip(),
                "subsections": []
            }
            current_subsection = None
            current_content = []
            result["sections"].append(current_section)
            continue

        # Article 헤더 먼저 체크 (4자리): #### 12.X.X.X. Title
        # Subsection보다 먼저 체크해야 12.1.1.1이 12.1.1로 잘못 매칭되지 않음
        article_match = re.match(r'^#{2,4}\s*(12\.\d+\.\d+\.\d+)\.\s*(.*)$', line)
        if article_match:
            # Article 헤딩을 볼드로 변환하여 content에 추가
            normalized = f"**{article_match.group(1)}. {article_match.group(2).strip()}**\n"
            current_content.append(normalized)
            continue

        # Subsection 헤더 (3자리): ### 12.X.X. Title
        subsection_match = re.match(r'^#{2,4}\s*(12\.\d+\.\d+)\.\s*(.*)$', line)
        if subsection_match:
            save_current_structure(result, current_section, current_subsection, current_content)

            current_subsection = {
                "id": subsection_match.group(1),
                "title": subsection_match.group(2).strip(),
                "content": ""
            }
            current_content = []
            if current_section:
                current_section["subsections"].append(current_subsection)
            continue

        # 일반 콘텐츠
        current_content.append(line)

    # 마지막 구조 저장
    save_current_structure(result, current_section, current_subsection, current_content)

    # content 정리: 마크다운 잔류물 제거
    for section in result.get("sections", []):
        for subsection in section.get("subsections", []):
            if subsection.get("content"):
                subsection["content"] = clean_final_content(subsection["content"])

    return result

def clean_final_content(text: str) -> str:
    """최종 content 정리"""
    # ** 볼드 마크다운 유지 (Article 헤딩)
    # #### 같은 마크다운 헤딩 제거
    text = re.sub(r'^#{1,4}\s+', '', text, flags=re.MULTILINE)
    # 연속 빈 줄 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def save_current_structure(result, section, subsection, content):
    """현재 구조에 콘텐츠 저장"""
    content_text = '\n'.join(content).strip()

    if subsection and content_text:
        subsection["content"] = content_text

def main():
    print("Loading Marker output...")
    md_content = MARKER_FILE.read_text(encoding='utf-8')

    print("Extracting Part 12...")
    part12_content = extract_part12_content(md_content)
    print(f"  Extracted {len(part12_content)} chars")

    # 디버깅: 추출된 내용 일부 출력
    print("\n=== First 500 chars ===")
    print(part12_content[:500])
    print("\n=== Last 500 chars ===")
    print(part12_content[-500:])

    print("\nParsing structure...")
    result = parse_part12(part12_content)

    # 통계 출력
    print("\n=== Part 12 Structure ===")
    print(f"Sections: {len(result['sections'])}")
    for section in result['sections']:
        print(f"  {section['id']}: {section['title']}")
        for sub in section.get('subsections', []):
            print(f"    {sub['id']}: {sub['title']} ({len(sub.get('content', ''))} chars)")

    # JSON 저장
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
