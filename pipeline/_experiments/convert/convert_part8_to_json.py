# -*- coding: utf-8 -*-
"""
Marker MD에서 Part 8을 추출하여 JSON으로 변환
Part 8: Sewage Systems
"""

import json
import re
import sys


def parse_part8(md_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 파일이 Part 8로 시작하는지 확인
    if md_content.strip().startswith('# Part 8'):
        print("Part 8 file detected (starts with # Part 8)")
    else:
        print("WARNING: File does not start with # Part 8")

    # 이미지 참조 제거 (줄바꿈 유지)
    md_content = re.sub(r'!\[\]\([^)]+\)', '', md_content)
    # span 태그 제거
    md_content = re.sub(r'<span[^>]*>', '', md_content)
    md_content = re.sub(r'</span>', '', md_content)

    # 구조 파싱
    data = {
        "id": "8",
        "title": "Sewage Systems",
        "sections": []
    }

    current_section = None
    current_subsection = None
    current_content = []

    for line in md_content.split('\n'):
        # Section 감지: ## Section 8.X. Title
        section_match = re.match(r'^#{1,3}\s+Section\s+(8\.\d+)\.\s+(.+)$', line)
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

        # Subsection 감지: # 8.X.X. Title 또는 ## 8.X.X. Title (Section 키워드 없는 것)
        subsection_match = re.match(r'^#{1,4}\s+(8\.\d+\.\d+)\.\s+(.+)$', line)
        if subsection_match and 'Section' not in line:
            # 이전 subsection 저장
            if current_subsection and current_content:
                current_subsection['content'] = '\n'.join(current_content).strip()
                current_content = []

            sub_id = subsection_match.group(1)
            sub_title = subsection_match.group(2).strip()

            # Section이 없으면 생성
            if current_section is None:
                # Section ID 추출 (8.X)
                sec_id = '.'.join(sub_id.split('.')[:2])
                current_section = {
                    "id": sec_id,
                    "title": "",
                    "subsections": []
                }
                data['sections'].append(current_section)

            current_subsection = {
                "id": sub_id,
                "title": sub_title,
                "content": ""
            }
            current_section['subsections'].append(current_subsection)
            continue

        # Article 감지: ### 8.X.X.X. Title 또는 #### 8.X.X.X. Title
        article_match = re.match(r'^#{2,4}\s+(8\.\d+\.\d+\.\d+)\.\s+(.+)$', line)
        if article_match:
            # Article을 plain text 헤더로 content에 추가 (Part 9 형식과 동일)
            current_content.append(f"{article_match.group(1)}.  {article_match.group(2)}")
            continue

        # 일반 콘텐츠
        if current_subsection is not None:
            current_content.append(line)

    # 마지막 subsection 저장
    if current_subsection and current_content:
        current_subsection['content'] = '\n'.join(current_content).strip()

    return data


def main():
    md_file = sys.argv[1] if len(sys.argv) > 1 else "output_marker/part8.md"
    output_file = "codevault/public/data/part8.json"

    print(f"Parsing Part 8 from: {md_file}")
    data = parse_part8(md_file)

    if data:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 통계 출력
        section_count = len(data['sections'])
        subsection_count = sum(len(s['subsections']) for s in data['sections'])

        print(f"\nPart 8 JSON created: {output_file}")
        print(f"  Sections: {section_count}")
        print(f"  Subsections: {subsection_count}")

        for section in data['sections']:
            print(f"  - {section['id']} {section['title']}: {len(section['subsections'])} subsections")


if __name__ == '__main__':
    main()
