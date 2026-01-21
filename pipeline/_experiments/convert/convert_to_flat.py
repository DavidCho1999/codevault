# -*- coding: utf-8 -*-
"""
Part 10 JSON을 flat 구조로 변환
articles 배열 → content 마크다운으로 합침
"""

import json

def convert_to_flat(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for section in data['sections']:
        for subsection in section['subsections']:
            # articles가 있으면 content로 합침
            if 'articles' in subsection and subsection['articles']:
                content_parts = []

                for article in subsection['articles']:
                    # Article 헤더
                    header = f"#### {article['id']}. {article['title']}"
                    content_parts.append(header)
                    content_parts.append("")  # 빈 줄

                    # Article 내용
                    if article.get('content'):
                        content_parts.append(article['content'])

                    content_parts.append("")  # Article 사이 빈 줄

                # content로 합침
                subsection['content'] = '\n'.join(content_parts).strip()

                # articles 배열 제거
                del subsection['articles']

    # 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"변환 완료: {output_file}")

    # 결과 요약
    total_subsections = sum(len(s['subsections']) for s in data['sections'])
    print(f"총 {len(data['sections'])} sections, {total_subsections} subsections")

if __name__ == "__main__":
    convert_to_flat(
        'codevault/public/data/part10.json',
        'codevault/public/data/part10_flat.json'
    )
