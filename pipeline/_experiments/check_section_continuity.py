"""
섹션 ID 연속성 체크 스크립트
- JSON에서 Article ID가 연속되는지 확인
- 예: 9.4.2.1 → 9.4.2.4 이면 9.4.2.2, 9.4.2.3 누락!
"""

import json
import re
import sys
from pathlib import Path

# 설정
JSON_PATH = Path(__file__).parent.parent / "codevault/public/data/part9.json"


def extract_article_ids(content):
    """content에서 Article ID 추출 (예: 9.4.2.1, 9.4.2.2)"""
    # 패턴: 9.X.X.X. 또는 9.X.X.X (마침표 선택적)
    pattern = r'\b(9\.\d+\.\d+\.\d+)\.?\s'
    matches = re.findall(pattern, content)
    return list(dict.fromkeys(matches))  # 중복 제거, 순서 유지


def check_continuity(article_ids):
    """Article ID 연속성 체크"""
    gaps = []

    for i in range(len(article_ids) - 1):
        current = article_ids[i]
        next_id = article_ids[i + 1]

        # 같은 Subsection 내에서만 체크
        current_parts = current.split('.')
        next_parts = next_id.split('.')

        if current_parts[:3] == next_parts[:3]:  # 같은 Subsection
            current_num = int(current_parts[3])
            next_num = int(next_parts[3])

            if next_num > current_num + 1:
                missing = [f"{'.'.join(current_parts[:3])}.{n}"
                          for n in range(current_num + 1, next_num)]
                gaps.append({
                    'after': current,
                    'before': next_id,
                    'missing': missing
                })

    return gaps


def main():
    print("=" * 60)
    print("  섹션 ID 연속성 체크 (Part 9)")
    print("=" * 60)

    if not JSON_PATH.exists():
        print(f"ERROR: JSON not found at {JSON_PATH}")
        return 1

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_gaps = []
    sections_checked = 0

    for section in data['sections']:
        section_id = section['id']

        # Subsection 체크
        for subsection in section.get('subsections', []):
            sub_id = subsection['id']
            content = subsection.get('content', '')

            if not content:
                continue

            sections_checked += 1
            article_ids = extract_article_ids(content)

            if len(article_ids) >= 2:
                gaps = check_continuity(article_ids)
                for gap in gaps:
                    gap['section'] = sub_id
                    total_gaps.append(gap)

    # 결과 출력
    print(f"\n검사한 Subsection: {sections_checked}개\n")

    if total_gaps:
        print(f"## 발견된 누락 ({len(total_gaps)}건)")
        print("-" * 60)
        for gap in total_gaps:
            print(f"\n[{gap['section']}]")
            print(f"  {gap['after']} → {gap['before']}")
            print(f"  누락: {', '.join(gap['missing'])}")
    else:
        print("## 결과: 누락 없음!")
        print("  모든 Article ID가 연속됩니다.")

    print("\n" + "=" * 60)
    print(f"  총 {len(total_gaps)}개 누락 발견")
    print("=" * 60)

    return len(total_gaps)


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result == 0 else 1)
