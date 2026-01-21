"""
Part 12 JSON 콘텐츠 정규화 스크립트

Part 12의 raw markdown 형식을 Part 11과 동일한 형식으로 변환:
- **12.x.x.x. Title** → [ARTICLE:12.x.x.x:Title]
- **(1)** → (1)
- *term* → term (이탤릭 제거)
- - (a) → (a) (리스트 마커 제거)
"""

import json
import re
from pathlib import Path

def normalize_content(content: str) -> str:
    """Part 12 content를 Part 11 형식으로 정규화"""
    if not content:
        return content

    result = content

    # 1. Article 헤더 변환: **12.x.x.x. Title** → [ARTICLE:12.x.x.x:Title]
    # 패턴: **12.1.1.1. Scope** 또는 **12.2.1.2. Energy Efficiency Design**
    result = re.sub(
        r'\*\*(12\.\d+\.\d+\.\d+)\.\s*([^*]+)\*\*',
        r'[ARTICLE:\1:\2]',
        result
    )

    # 2. Bold clause 번호 제거: **(1)** → (1)
    result = re.sub(r'\*\*\((\d+)\)\*\*', r'(\1)', result)

    # 3. 이탤릭 제거: *term* → term
    # 주의: **bold** 패턴과 겹치지 않도록 단일 * 만 처리
    result = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'\1', result)

    # 4. 리스트 마커 제거: - (a) → (a), - (i) → (i), - (1) → (1)
    result = re.sub(r'^- \(([a-z])\)', r'(\1)', result, flags=re.MULTILINE)
    result = re.sub(r'^- \(([ivx]+)\)', r'(\1)', result, flags=re.MULTILINE)
    result = re.sub(r'^- \*\*\((\d+)\)\*\*', r'(\1)', result, flags=re.MULTILINE)
    result = re.sub(r'^- \((\d+)\)', r'(\1)', result, flags=re.MULTILINE)  # - (1) → (1)

    # 5. 들여쓰기된 sub-clause 정리: "  - (i)" → "(i)"
    result = re.sub(r'^\s+- \(([ivx]+)\)', r'  (\1)', result, flags=re.MULTILINE)

    # 6. Article 제목 뒤 공백 정리
    result = re.sub(r'\[ARTICLE:([^:]+):([^\]]+)\s*\]', r'[ARTICLE:\1:\2]', result)

    return result


def normalize_part12_json(input_path: str, output_path: str = None):
    """Part 12 JSON 파일 정규화"""

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 모든 subsection의 content 정규화
    normalized_count = 0
    for section in data.get('sections', []):
        for subsection in section.get('subsections', []):
            if 'content' in subsection and subsection['content']:
                original = subsection['content']
                normalized = normalize_content(original)
                if original != normalized:
                    subsection['content'] = normalized
                    normalized_count += 1
                    print(f"  [OK] {subsection['id']} normalized")

    # 출력 경로 결정
    if output_path is None:
        output_path = input_path  # 덮어쓰기

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n총 {normalized_count}개 subsection 정규화 완료")
    print(f"저장: {output_path}")

    return data


def verify_normalization(data: dict):
    """정규화 결과 검증"""
    print("\n=== 정규화 검증 ===")

    issues = []

    for section in data.get('sections', []):
        for subsection in section.get('subsections', []):
            content = subsection.get('content', '')

            # 남은 markdown 패턴 체크
            if re.search(r'\*\*12\.\d+\.\d+\.\d+\.', content):
                issues.append(f"{subsection['id']}: Article 헤더 변환 안됨")

            if re.search(r'\*\*\(\d+\)\*\*', content):
                issues.append(f"{subsection['id']}: Bold clause 번호 남음")

            if re.search(r'(?<!\*)\*[a-z]+\*(?!\*)', content):
                issues.append(f"{subsection['id']}: 이탤릭 남음")

            if re.search(r'^- \([a-z]\)', content, re.MULTILINE):
                issues.append(f"{subsection['id']}: 리스트 마커 남음")

    if issues:
        print("[WARNING] Remaining issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("[SUCCESS] All patterns normalized!")

    return len(issues) == 0


if __name__ == "__main__":
    input_file = Path(__file__).parent.parent / "codevault/public/data/part12.json"

    print(f"입력: {input_file}")
    print("\n정규화 시작...")

    data = normalize_part12_json(str(input_file))

    verify_normalization(data)

    # 샘플 출력
    print("\n=== 샘플 출력 (12.1.1) ===")
    for section in data['sections']:
        for subsection in section['subsections']:
            if subsection['id'] == '12.1.1':
                print(subsection['content'][:500])
                break
