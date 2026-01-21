# -*- coding: utf-8 -*-
"""
Marker MD에서 Part 12를 추출하여 JSON으로 변환
Part 12: Resource Conservation and Environmental Integrity
"""

import json
import re

def parse_part12(md_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Part 12 범위 찾기
    start_line = None
    end_line = None

    for i, line in enumerate(lines):
        if '# Part 12' in line:
            if start_line is None:
                start_line = i
        # Part 13 또는 파일 끝으로 종료
        if '# Part 13' in line and start_line is not None:
            end_line = i
            break

    if not end_line:
        end_line = len(lines)

    if not start_line:
        print("ERROR: Part 12 not found in file")
        return None

    print(f"Part 12 found: lines {start_line} to {end_line}")

    part12_lines = lines[start_line:end_line]
    md_content = ''.join(part12_lines)

    # 이미지 참조 제거
    md_content = re.sub(r'!\[\]\([^)]+\)\n*', '', md_content)
    # span 태그 제거
    md_content = re.sub(r'<span[^>]*>', '', md_content)
    md_content = re.sub(r'</span>', '', md_content)

    # 구조 파싱
    data = {
        "id": "12",
        "title": "Resource Conservation and Environmental Integrity",
        "sections": []
    }

    current_section = None
    current_subsection = None
    current_content = []

    for line in md_content.split('\n'):
        # Section 감지: ## Section 12.X. Title
        section_match = re.match(r'^#{2,3}\s+Section\s+(12\.\d+)\.\s+(.+)$', line)
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

        # Subsection 감지: ## 12.X.X. Title (Section 키워드 없는 것)
        subsection_match = re.match(r'^#{2,4}\s+(12\.\d+\.\d+)\.\s+(.+)$', line)
        if subsection_match and 'Section' not in line:
            # 이전 subsection 저장
            if current_subsection and current_content:
                current_subsection['content'] = '\n'.join(current_content).strip()
                current_content = []

            sub_id = subsection_match.group(1)
            sub_title = subsection_match.group(2).strip()

            # Section이 없으면 생성
            if current_section is None:
                # Section ID 추출 (12.X)
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

        # Article 감지: ### 12.X.X.X. Title 또는 #### 12.X.X.X. Title
        article_match = re.match(r'^#{2,4}\s+(12\.\d+\.\d+\.\d+)\.\s+(.+)$', line)
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
    import sys

    md_file = sys.argv[1] if len(sys.argv) > 1 else "output_marker/301880_full.md"
    output_file = "codevault/public/data/part12.json"

    print(f"Parsing Part 12 from: {md_file}")
    data = parse_part12(md_file)

    if data:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 통계 출력
        section_count = len(data['sections'])
        subsection_count = sum(len(s['subsections']) for s in data['sections'])

        print(f"\nPart 12 JSON created: {output_file}")
        print(f"  Sections: {section_count}")
        print(f"  Subsections: {subsection_count}")

        for section in data['sections']:
            print(f"  - {section['id']} {section['title']}: {len(section['subsections'])} subsections")


if __name__ == '__main__':
    main()
