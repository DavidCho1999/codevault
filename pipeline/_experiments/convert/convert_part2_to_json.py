# -*- coding: utf-8 -*-
"""
Marker MD에서 Part 2를 추출하여 JSON으로 변환
Part 2: Objectives (Division A)

Part 2 구조:
- Section 2.1: Application
  - 2.1.1. Application
    - 2.1.1.1. Application
    - 2.1.1.2. Application of Objectives
- Section 2.2: Objectives
  - 2.2.1. Objectives
    - 2.2.1.1. Objectives (모든 Objective 코드 포함)
      - OS Safety (OS1-OS4)
      - OH Health (OH1-OH7)
      - OA Accessibility (OA1-OA2)
      - OP Fire/Structural/Water Protection (OP1-OP5)
      - OR Resource Conservation (OR1-OR2)
      - OE Environmental Integrity (OE1-OE2)
      - OC Conservation of Buildings
"""

import json
import re
import sys


def normalize_content(content: str) -> str:
    """정규화: bold, italic, 마크다운 헤딩 제거"""
    if not content:
        return content

    result = content

    # 1. 마크다운 헤딩 제거: ### Title → Title (단, Article 헤딩은 유지)
    # Article은 나중에 [ARTICLE:] 마커로 변환

    # 2. Bold clause: **(1)** → (1)
    result = re.sub(r'\*\*\((\d+)\)\*\*', r'(\1)', result)

    # 3. Bold 제거: **text** → text (테이블/Notes 헤딩 제외)
    # 단, OS1, OH1 같은 Objective 코드는 bold 유지해야 할 수도...
    # 일단 제거하고 렌더링에서 처리
    result = re.sub(r'\*\*([^*]+)\*\*', r'\1', result)

    # 4. 이탤릭: *term* → term
    result = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'\1', result)

    # 5. 리스트 마커: - (a) → (a), - (1) → (1)
    result = re.sub(r'^- \(([a-z])\)', r'(\1)', result, flags=re.MULTILINE)
    result = re.sub(r'^- \((\d+)\)', r'(\1)', result, flags=re.MULTILINE)

    # 6. 빈 줄 정리
    result = re.sub(r'\n{3,}', '\n\n', result)

    return result.strip()


def parse_part2(md_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Part 2 범위 찾기 - "# Part 2 Objectives" 찾기
    start_line = None
    end_line = None

    for i, line in enumerate(lines):
        # Part 2 시작: "# Part 2 Objectives"
        if re.match(r'^#\s+Part\s+2\s+Objectives', line):
            if start_line is None:
                start_line = i
                print(f"Part 2 start found at line {i}: {line.strip()}")

        # Part 3 시작으로 종료
        if re.match(r'^#\s+Part\s+3', line) and start_line is not None:
            end_line = i
            print(f"Part 3 start found at line {i}: {line.strip()}")
            break

        # "## Part 3 Functional Statements"도 체크
        if '## Part 3 Functional Statements' in line and start_line is not None:
            end_line = i
            print(f"Part 3 section found at line {i}: {line.strip()}")
            break

    if not end_line:
        end_line = len(lines)

    if not start_line:
        print("ERROR: Part 2 not found in file")
        return None

    print(f"Part 2 found: lines {start_line} to {end_line}")

    part2_lines = lines[start_line:end_line]
    md_content = ''.join(part2_lines)

    # 이미지 참조 제거 (줄바꿈 유지!)
    md_content = re.sub(r'!\[\]\([^)]+\)', '', md_content)

    # span 태그 제거
    md_content = re.sub(r'<span[^>]*>', '', md_content)
    md_content = re.sub(r'</span>', '', md_content)

    # 구조 파싱
    data = {
        "id": "2",
        "title": "Objectives",
        "division": "A",
        "sections": []
    }

    current_section = None
    current_subsection = None
    current_content = []

    for line in md_content.split('\n'):
        stripped = line.strip()

        # Section 감지: ## Section 2.X. Title 또는 ## Section 2.X Title
        section_match = re.match(r'^#{2,3}\s+Section\s+(2\.\d+)\.?\s+(.+)$', line)
        if section_match:
            # 이전 subsection 저장
            if current_subsection and current_content:
                current_subsection['content'] = normalize_content('\n'.join(current_content))
                current_content = []

            # 새 section
            current_section = {
                "id": section_match.group(1),
                "title": section_match.group(2).strip(),
                "subsections": []
            }
            data['sections'].append(current_section)
            current_subsection = None
            print(f"  Section: {current_section['id']} - {current_section['title']}")
            continue

        # Subsection 감지: ## 2.X.X. Title (Section 키워드 없는 것)
        subsection_match = re.match(r'^#{2,4}\s+(2\.\d+\.\d+)\.?\s+(.+)$', line)
        if subsection_match and 'Section' not in line:
            # 이전 subsection 저장
            if current_subsection and current_content:
                current_subsection['content'] = normalize_content('\n'.join(current_content))
                current_content = []

            sub_id = subsection_match.group(1)
            sub_title = subsection_match.group(2).strip()

            # Section이 없으면 생성
            if current_section is None:
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
            print(f"    Subsection: {current_subsection['id']} - {current_subsection['title']}")
            continue

        # Article 감지: #### 2.X.X.X. Title
        article_match = re.match(r'^#{2,4}\s+(2\.\d+\.\d+\.\d+)\.?\s+(.+)$', line)
        if article_match:
            # Article을 [ARTICLE:id:title] 마커로 content에 추가
            article_id = article_match.group(1)
            article_title = article_match.group(2).strip()
            current_content.append(f"\n[ARTICLE:{article_id}:{article_title}]")
            current_content.append("")
            print(f"      Article: {article_id} - {article_title}")
            continue

        # Objective 코드 감지: ## **OS Safety** 또는 #### **OS1 Fire Safety**
        objective_match = re.match(r'^#{2,4}\s+\*?\*?([A-Z]{2,3}\d*)\s+(.+?)\*?\*?\s*$', line)
        if objective_match:
            obj_code = objective_match.group(1)
            obj_title = objective_match.group(2).strip().rstrip('*')
            # Objective를 헤딩으로 추가
            current_content.append(f"\n**{obj_code} {obj_title}**")
            current_content.append("")
            continue

        # 일반 콘텐츠
        if current_subsection is not None:
            current_content.append(line)

    # 마지막 subsection 저장
    if current_subsection and current_content:
        current_subsection['content'] = normalize_content('\n'.join(current_content))

    return data


def main():
    md_file = sys.argv[1] if len(sys.argv) > 1 else "data/marker/301880_full.md"
    output_file = "codevault/public/data/part2.json"

    print(f"Parsing Part 2 from: {md_file}")
    data = parse_part2(md_file)

    if data:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 통계 출력
        section_count = len(data['sections'])
        subsection_count = sum(len(s['subsections']) for s in data['sections'])

        print(f"\nPart 2 JSON created: {output_file}")
        print(f"  Sections: {section_count}")
        print(f"  Subsections: {subsection_count}")

        for section in data['sections']:
            print(f"  - {section['id']} {section['title']}: {len(section['subsections'])} subsections")


if __name__ == '__main__':
    main()
