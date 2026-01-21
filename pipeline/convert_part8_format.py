#!/usr/bin/env python3
"""
Part 8 JSON 형식 변환 스크립트
- Part 10, 11, 12와 동일한 형식으로 변환
- Article 헤딩에 #### 마크다운 추가
"""

import json
import re
from pathlib import Path

# 경로 설정
DATA_DIR = Path(__file__).parent.parent / "codevault" / "public" / "data"
INPUT_PATH = DATA_DIR / "part8.json"
OUTPUT_PATH = DATA_DIR / "part8_converted.json"
BACKUP_PATH = DATA_DIR / "_archive" / "part8_original.json"

def convert_content(content: str) -> str:
    """
    content 내의 Article 헤딩을 마크다운 형식으로 변환

    변환 전: 8.1.1.1.  Scope
    변환 후: #### 8.1.1.1. Scope
    """
    if not content:
        return content

    # Article 헤딩 패턴: 줄 시작에서 8.x.x.x. 형식 (공백 2개 후 제목)
    # 예: "8.1.1.1.  Scope" -> "#### 8.1.1.1. Scope"
    pattern = r'^(8\.\d+\.\d+\.\d+\.)\s{2,}(\S.*)$'

    lines = content.split('\n')
    converted_lines = []

    for line in lines:
        match = re.match(pattern, line)
        if match:
            article_id = match.group(1)
            title = match.group(2)
            converted_lines.append(f"#### {article_id} {title}")
        else:
            converted_lines.append(line)

    return '\n'.join(converted_lines)

def convert_table_headings(content: str) -> str:
    """
    Table 헤딩도 마크다운 형식으로 변환

    변환 전: Table 8.2.1.3.-A
    변환 후: #### Table 8.2.1.3.-A
    """
    if not content:
        return content

    # Table 헤딩 패턴
    pattern = r'^(Table 8\.\d+\.\d+\.\d+\.-[A-Z](?:\s*\(Cont\'d\))?)$'

    lines = content.split('\n')
    converted_lines = []

    for line in lines:
        match = re.match(pattern, line)
        if match:
            converted_lines.append(f"#### {line}")
        else:
            converted_lines.append(line)

    return '\n'.join(converted_lines)

def convert_part8_json():
    """Part 8 JSON 변환 실행"""

    # 원본 읽기
    with open(INPUT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Part 8 JSON 로드: {len(data['sections'])} sections")

    # 통계
    stats = {
        'sections': 0,
        'subsections': 0,
        'articles_converted': 0,
        'tables_converted': 0
    }

    # 각 섹션 변환
    for section in data['sections']:
        stats['sections'] += 1

        for subsection in section.get('subsections', []):
            stats['subsections'] += 1
            original_content = subsection.get('content', '')

            if original_content:
                # Article 헤딩 변환
                converted = convert_content(original_content)
                article_count = len(re.findall(r'^#### 8\.\d+\.\d+\.\d+\.', converted, re.MULTILINE))
                stats['articles_converted'] += article_count

                # Table 헤딩 변환
                converted = convert_table_headings(converted)
                table_count = len(re.findall(r'^#### Table', converted, re.MULTILINE))
                stats['tables_converted'] += table_count

                subsection['content'] = converted

    # 백업 디렉토리 생성
    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 원본 백업
    with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
        json.dump(json.load(open(INPUT_PATH, 'r', encoding='utf-8')), f, indent=2, ensure_ascii=False)
    print(f"원본 백업: {BACKUP_PATH}")

    # 변환 결과 저장
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"변환 결과 저장: {OUTPUT_PATH}")

    # 통계 출력
    print("\n=== 변환 통계 ===")
    print(f"Sections: {stats['sections']}")
    print(f"Subsections: {stats['subsections']}")
    print(f"Articles 변환: {stats['articles_converted']}")
    print(f"Tables 변환: {stats['tables_converted']}")

    return stats

def verify_conversion():
    """변환 결과 검증"""

    with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("\n=== 변환 결과 샘플 ===")

    # 첫 번째 subsection content 확인
    first_content = data['sections'][0]['subsections'][0]['content']
    print(f"\n[8.1.1 Scope]")
    print(first_content[:500])

    # Article 헤딩 패턴 확인
    article_pattern = r'^#### 8\.\d+\.\d+\.\d+\.'
    all_articles = []

    for section in data['sections']:
        for subsection in section.get('subsections', []):
            content = subsection.get('content', '')
            articles = re.findall(article_pattern, content, re.MULTILINE)
            all_articles.extend(articles)

    print(f"\n총 Article 헤딩: {len(all_articles)}")
    print("샘플 (처음 10개):")
    for a in all_articles[:10]:
        print(f"  {a}")

if __name__ == "__main__":
    convert_part8_json()
    verify_conversion()
