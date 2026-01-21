# -*- coding: utf-8 -*-
"""
Marker 마크다운을 part9.json 형식으로 변환
9.4 섹션만 업데이트
"""

import json
import re

def parse_marker_md(md_content):
    """Marker 마크다운을 파싱하여 섹션별 구조로 변환"""

    # 이미지 참조 제거 (페이지 이미지)
    md_content = re.sub(r'!\[\]\(_page_\d+_Picture_\d+\.jpeg\)\n*', '', md_content)

    # 파일 링크 제거
    md_content = re.sub(r'\[([^\]]+)\]\(file://[^)]+\)', r'\1', md_content)

    # span 태그 제거
    md_content = re.sub(r'<span[^>]*>', '', md_content)
    md_content = re.sub(r'</span>', '', md_content)

    subsections = {}
    current_subsection = None
    current_content = []

    lines = md_content.split('\n')

    for line in lines:
        # Subsection 헤더 감지: # 9.4.X. Title (X는 1자리 숫자, 뒤에 숫자가 아닌 문자)
        # 예: # 9.4.1. Structural... (O)
        # 예: ## 9.4.2.1. Application... (X - Article임)
        subsection_match = re.match(r'^#+\s*(9\.4\.\d)\.\s+([A-Z].*)$', line)
        if subsection_match:
            # 이전 subsection 저장
            if current_subsection:
                subsections[current_subsection['id']] = {
                    'id': current_subsection['id'],
                    'title': current_subsection['title'],
                    'content': '\n'.join(current_content).strip()
                }

            current_subsection = {
                'id': subsection_match.group(1),
                'title': subsection_match.group(2).strip()
            }
            current_content = []
            continue

        # Section 헤더 (# Section 9.4. 또는 # Section 9.5.) - 9.4만 포함
        if re.match(r'^#+\s*Section 9\.[45]\.', line):
            # 9.5 섹션 시작하면 중단
            if '9.5.' in line and current_subsection:
                subsections[current_subsection['id']] = {
                    'id': current_subsection['id'],
                    'title': current_subsection['title'],
                    'content': '\n'.join(current_content).strip()
                }
                break
            continue

        if current_subsection:
            current_content.append(line)

    # 마지막 subsection 저장
    if current_subsection and current_subsection['id'] not in subsections:
        subsections[current_subsection['id']] = {
            'id': current_subsection['id'],
            'title': current_subsection['title'],
            'content': '\n'.join(current_content).strip()
        }

    return subsections

def update_part9_json(marker_subsections):
    """part9.json의 9.4 섹션을 Marker 결과로 업데이트"""

    with open('codevault/public/data/part9.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 9.4 섹션 찾기
    for section in data['sections']:
        if section['id'] == '9.4':
            # subsections 업데이트
            for sub in section['subsections']:
                sub_id = sub['id']
                if sub_id in marker_subsections:
                    print(f"Updating {sub_id}: {sub['title']}")
                    # 마크다운 content로 교체
                    sub['content'] = marker_subsections[sub_id]['content']
                    sub['content_format'] = 'markdown'  # 마크다운 형식 표시
            break

    # 저장
    with open('codevault/public/data/part9.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Updated part9.json")

def main():
    # Marker 결과 읽기
    with open('scripts_temp/marker_output/section_9_4.md', 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 파싱
    subsections = parse_marker_md(md_content)

    print("Parsed subsections:")
    for sub_id, sub in subsections.items():
        print(f"  {sub_id}: {sub['title'][:50]}... ({len(sub['content'])} chars)")

    # JSON 업데이트
    update_part9_json(subsections)

if __name__ == "__main__":
    main()
