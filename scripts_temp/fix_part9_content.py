"""
fix_part9_content.py - Part 9 본문 데이터 후처리
- revision marker 제거 (r1, e2 등)
- 본문에 섞인 테이블 데이터 제거
- 문장 파편화 병합
"""

import json
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

INPUT_FILE = '../codevault/public/data/part9.json'
OUTPUT_FILE = '../codevault/public/data/part9_fixed.json'


def get_paths():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.normpath(os.path.join(script_dir, INPUT_FILE))
    output_path = os.path.normpath(os.path.join(script_dir, OUTPUT_FILE))
    return input_path, output_path


def remove_revision_markers(text: str) -> str:
    """
    revision marker 제거
    예: "r1 (1)" -> "(1)", "e2 (2)" -> "(2)"
    """
    # 패턴: r1, e1, e2 등이 문장 시작이나 번호 앞에 있는 경우
    text = re.sub(r'\b[re]\d\s+(\(\d+\))', r'\1', text)
    # 단독으로 있는 revision marker
    text = re.sub(r'\b[re]\d\b\s*', '', text)
    return text


def remove_inline_table_data(text: str) -> str:
    """
    본문에 섞인 테이블 데이터 제거
    테이블 제목 다음에 오는 데이터 행들을 제거
    """
    lines = text.split('\n')
    result = []
    skip_until_article = False

    for line in lines:
        stripped = line.strip()

        # 테이블 제목 감지 (Table X.X.X.X로 시작)
        if re.match(r'^Table\s+\d+\.\d+\.\d+\.\d+', stripped):
            result.append(line)
            skip_until_article = True
            continue

        # Forming Part of 라인은 유지
        if 'Forming Part of' in stripped:
            result.append(line)
            continue

        # Notes to Table은 유지
        if stripped.startswith('Notes to Table'):
            result.append(line)
            skip_until_article = False
            continue

        # Article 번호 감지 - 테이블 데이터 스킵 종료
        if re.match(r'^\d+\.\d+\.\d+\.\d+\.?\s+\w', stripped):
            skip_until_article = False
            result.append(line)
            continue

        # 조항 번호 감지 (1), (2) 등 - 테이블 데이터 스킵 종료
        if re.match(r'^\(\d+\)\s+\w', stripped):
            skip_until_article = False
            result.append(line)
            continue

        # 테이블 데이터 스킵 중
        if skip_until_article:
            # 테이블 데이터 패턴 (숫자나 단위가 많은 줄)
            if re.match(r'^[\d\s/\-—]+$', stripped):
                continue
            # 테이블 헤더 패턴
            if re.match(r'^[A-Z][a-z]+\s+(of|for|in|to)\s+', stripped):
                continue
            # 빈 줄
            if not stripped:
                continue

        result.append(line)

    return '\n'.join(result)


def merge_fragmented_sentences(text: str) -> str:
    """
    파편화된 문장 병합
    예: "flooding." 가 별도 줄인 경우 이전 줄에 병합
    """
    lines = text.split('\n')
    result = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 짧은 단어 + 마침표만 있는 줄 (파편)
        if re.match(r'^[a-z]+\.$', stripped) and len(stripped) < 15:
            if result:
                # 이전 줄에 병합
                result[-1] = result[-1].rstrip() + ' ' + stripped
                continue

        # 단독 마침표
        if stripped == '.':
            if result:
                result[-1] = result[-1].rstrip() + '.'
                continue

        # 괄호가 닫히지 않은 참조 (예: "(See also Articles 9.15.4.5. and")
        if result and re.search(r'\(See also[^)]+$', result[-1]):
            if re.match(r'^[\d\.]+\)', stripped):
                result[-1] = result[-1].rstrip() + ' ' + stripped
                continue

        result.append(line)

    return '\n'.join(result)


def clean_title_splits(text: str) -> str:
    """
    분리된 제목 병합
    예: "9.10.9.Fire Separations..." / "and Spaces within Buildings" 병합
    """
    lines = text.split('\n')
    result = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 소문자로 시작하는 짧은 줄 (제목 연속)
        if re.match(r'^(and|or|in|of|for|to|the|with)\s+\w', stripped.lower()):
            if result:
                prev = result[-1].strip()
                # 이전 줄이 섹션 제목인 경우
                if re.match(r'^\d+\.\d+\.\d+\.?\s*\w', prev):
                    result[-1] = result[-1].rstrip() + ' ' + stripped
                    continue

        result.append(line)

    return '\n'.join(result)


def clean_empty_lines(text: str) -> str:
    """연속 빈 줄 정리"""
    return re.sub(r'\n{3,}', '\n\n', text)


def fix_content(content: str) -> str:
    """모든 정리 적용"""
    if not content:
        return content

    content = remove_revision_markers(content)
    content = remove_inline_table_data(content)
    content = merge_fragmented_sentences(content)
    content = clean_title_splits(content)
    content = clean_empty_lines(content)

    return content.strip()


def process_data(data: dict) -> dict:
    """전체 데이터 처리"""
    stats = {
        'sections': 0,
        'subsections': 0,
        'content_fixed': 0
    }

    for section in data.get('sections', []):
        stats['sections'] += 1

        for subsection in section.get('subsections', []):
            stats['subsections'] += 1

            original = subsection.get('content', '')
            fixed = fix_content(original)

            if original != fixed:
                stats['content_fixed'] += 1
                subsection['content'] = fixed

    return data, stats


def main():
    input_path, output_path = get_paths()

    print("=" * 60)
    print("Part 9 Content Fix")
    print("=" * 60)
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")

    # 로드
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 처리
    print("\nProcessing...")
    data, stats = process_data(data)

    print(f"\nStats:")
    print(f"  Sections: {stats['sections']}")
    print(f"  Subsections: {stats['subsections']}")
    print(f"  Content fixed: {stats['content_fixed']}")

    # 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nSaved: {output_path}")

    # 샘플 검증
    print("\n" + "=" * 60)
    print("Sample verification (9.6.1):")
    print("=" * 60)

    for section in data['sections']:
        for sub in section.get('subsections', []):
            if sub['id'] == '9.6.1':
                content = sub['content']
                # revision marker 확인
                markers = re.findall(r'\b[re]\d\b', content)
                print(f"  Revision markers remaining: {len(markers)}")
                if markers:
                    print(f"    Found: {markers[:5]}")
                break


if __name__ == "__main__":
    main()
