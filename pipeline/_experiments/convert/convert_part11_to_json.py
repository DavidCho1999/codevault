# -*- coding: utf-8 -*-
"""
Marker MD에서 Part 11을 추출하여 flat JSON으로 변환
"""

import json
import re

def parse_part11(md_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Part 11 범위 찾기 (38076 ~ 39989)
    start_line = None
    end_line = None

    for i, line in enumerate(lines):
        if '# Part 11' in line and 'Renovation' in lines[i+1] if i+1 < len(lines) else False:
            if start_line is None:
                start_line = i
        if '# Part 12' in line and start_line is not None:
            end_line = i
            break

    if not start_line:
        # 수동 설정
        start_line = 38075
        end_line = 39988

    part11_lines = lines[start_line:end_line]
    md_content = ''.join(part11_lines)

    # 이미지 참조 제거
    md_content = re.sub(r'!\[\]\([^)]+\)\n*', '', md_content)
    # span 태그 제거
    md_content = re.sub(r'<span[^>]*>', '', md_content)
    md_content = re.sub(r'</span>', '', md_content)

    # 구조 파싱
    data = {
        "id": "11",
        "title": "Renovation",
        "sections": []
    }

    current_section = None
    current_subsection = None
    current_content = []

    for line in md_content.split('\n'):
        # Section 감지: ## Section 11.X. Title 또는 ### Section 11.X. Title
        section_match = re.match(r'^#{2,3}\s+Section\s+(11\.\d+)\.\s+(.+)$', line)
        if section_match:
            # 이전 subsection 저장
            if current_subsection and current_content:
                current_subsection['content'] = '\n'.join(current_content).strip()
                current_content = []

            # 새 section
            current_section = {
                "id": section_match.group(1),
                "title": section_match.group(2).strip(),
                "subsections": []
            }
            data['sections'].append(current_section)
            current_subsection = None
            continue

        # Subsection 감지: ### 11.X.X. Title (Section 키워드 없는 것만)
        subsection_match = re.match(r'^###\s+(11\.\d+\.\d+)\.\s+(.+)$', line)

        if subsection_match:
            # 이전 subsection 저장
            if current_subsection and current_content:
                current_subsection['content'] = '\n'.join(current_content).strip()
                current_content = []

            sub_id = subsection_match.group(1)
            sub_title = subsection_match.group(2).strip()

            # Section이 없으면 에러 방지
            if current_section is None:
                continue

            current_subsection = {
                "id": sub_id,
                "title": sub_title,
                "content": ""
            }
            current_section['subsections'].append(current_subsection)
            continue

        # Article 감지: ### 11.X.X.X. Title - content에 포함
        article_match = re.match(r'^###\s+(11\.\d+\.\d+\.\d+)\.\s+(.+)$', line)
        if article_match:
            # Article을 마크다운 헤더로 content에 추가
            current_content.append(f"\n#### {article_match.group(1)}. {article_match.group(2)}")
            current_content.append("")
            continue

        # 일반 콘텐츠
        if current_subsection is not None:
            current_content.append(line)

    # 마지막 subsection 저장
    if current_subsection and current_content:
        current_subsection['content'] = '\n'.join(current_content).strip()

    return data


def main():
    data = parse_part11('output_marker/301880_full.md')

    # 저장
    with open('codevault/public/data/part11.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 요약
    total_subsections = sum(len(s['subsections']) for s in data['sections'])
    print(f"Part 11 변환 완료")
    print(f"- Sections: {len(data['sections'])}")
    print(f"- Subsections: {total_subsections}")

    for section in data['sections']:
        print(f"  {section['id']}: {section['title']} ({len(section['subsections'])} subsections)")


if __name__ == "__main__":
    main()
