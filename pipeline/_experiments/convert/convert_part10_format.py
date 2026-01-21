# -*- coding: utf-8 -*-
"""
Part 10 JSON을 Part 9 형식으로 변환
- articles 배열을 content 문자열로 합침
- page 필드 추가
"""

import json
from pathlib import Path

INPUT_FILE = Path("codevault/public/data/part10.json")
OUTPUT_FILE = Path("codevault/public/data/part10.json")

# Part 10 시작 페이지 (OBC PDF 기준)
PART10_START_PAGE = 1131

def convert_to_part9_format(data: dict) -> dict:
    """Part 10 데이터를 Part 9 형식으로 변환"""

    result = {
        "id": data["id"],
        "title": data["title"],
        "sections": []
    }

    page_offset = 0

    for section in data["sections"]:
        new_section = {
            "id": section["id"],
            "title": section["title"],
            "page": PART10_START_PAGE + page_offset,
            "subsections": []
        }

        for subsection in section.get("subsections", []):
            # articles 내용을 content로 합침
            content_parts = []

            # subsection 레벨 content
            if subsection.get("content"):
                content_parts.append(subsection["content"])

            # articles 내용 추가
            for article in subsection.get("articles", []):
                article_header = f"## {article['id']}. {article['title']}\n\n"
                article_content = article.get("content", "")
                content_parts.append(article_header + article_content)

            combined_content = "\n\n".join(content_parts)

            new_subsection = {
                "id": subsection["id"],
                "title": subsection["title"],
                "page": PART10_START_PAGE + page_offset,
                "content": combined_content,
                "articles": [],  # Part 9 스타일: 빈 배열
                "content_format": "markdown"  # markdown 형식 표시
            }

            new_section["subsections"].append(new_subsection)
            page_offset += 1

        result["sections"].append(new_section)

    return result

def main():
    print("Loading Part 10 JSON...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("Converting to Part 9 format...")
    converted = convert_to_part9_format(data)

    # 통계 출력
    print("\n=== Converted Structure ===")
    print(f"Sections: {len(converted['sections'])}")
    for section in converted['sections']:
        print(f"  {section['id']}: {section['title']} (page {section['page']})")
        for sub in section.get('subsections', []):
            content_len = len(sub.get('content', ''))
            print(f"    {sub['id']}: {sub['title']} ({content_len} chars)")

    # 저장
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
