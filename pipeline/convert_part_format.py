#!/usr/bin/env python3
"""
Part JSON 형식 변환 스크립트 (범용)
- Part 8, 9에 적용 가능
- Article 헤딩에 #### 마크다운 추가
- Table 헤딩에 #### 마크다운 추가
"""

import json
import re
import sys
from pathlib import Path

# 경로 설정
DATA_DIR = Path(__file__).parent.parent / "codevault" / "public" / "data"
ARCHIVE_DIR = DATA_DIR / "_archive"

def convert_content(content: str, part_num: int) -> str:
    """
    content 내의 Article 헤딩을 마크다운 형식으로 변환

    변환 전: 9.1.1.1.  Application
    변환 후: #### 9.1.1.1. Application
    """
    if not content:
        return content

    # Article 헤딩 패턴: 줄 시작에서 X.x.x.x. 형식 (공백 2개 후 제목)
    # 예: "9.1.1.1.  Scope" -> "#### 9.1.1.1. Scope"
    pattern = rf'^({part_num}\.\d+\.\d+\.\d+\.)\s{{2,}}(\S.*)$'

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

def convert_table_headings(content: str, part_num: int) -> str:
    """
    Table 헤딩도 마크다운 형식으로 변환

    변환 전: Table 9.3.1.7.  Site-Batched...
    변환 후: #### Table 9.3.1.7. Site-Batched...
    """
    if not content:
        return content

    # Table 헤딩 패턴
    # 형식 1: Table 9.3.1.7.  Site-Batched Concrete Mixes
    # 형식 2: Table 9.4.3.1.
    pattern = rf'^(Table {part_num}\.\d+\.\d+\.\d+\.(?:-[A-Z])?(?:\s*\(Cont\'d\))?)\s*(.*)$'

    lines = content.split('\n')
    converted_lines = []

    for line in lines:
        # 이미 #### 로 시작하면 건너뜀
        if line.strip().startswith('####'):
            converted_lines.append(line)
            continue

        match = re.match(pattern, line)
        if match:
            table_id = match.group(1)
            rest = match.group(2).strip()
            if rest:
                converted_lines.append(f"#### {table_id} {rest}")
            else:
                converted_lines.append(f"#### {table_id}")
        else:
            converted_lines.append(line)

    return '\n'.join(converted_lines)

def convert_part_json(part_num: int, dry_run: bool = False):
    """Part JSON 변환 실행"""

    input_path = DATA_DIR / f"part{part_num}.json"
    output_path = DATA_DIR / f"part{part_num}_converted.json"
    backup_path = ARCHIVE_DIR / f"part{part_num}_original.json"

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        return None

    # 원본 읽기
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Part {part_num} JSON 로드: {len(data.get('sections', []))} sections")

    # 통계
    stats = {
        'sections': 0,
        'subsections': 0,
        'articles_converted': 0,
        'tables_converted': 0
    }

    # 각 섹션 변환
    for section in data.get('sections', []):
        stats['sections'] += 1

        for subsection in section.get('subsections', []):
            stats['subsections'] += 1
            original_content = subsection.get('content', '')

            if original_content:
                # Article 헤딩 변환
                converted = convert_content(original_content, part_num)
                article_count = len(re.findall(rf'^#### {part_num}\.\d+\.\d+\.\d+\.', converted, re.MULTILINE))
                stats['articles_converted'] += article_count

                # Table 헤딩 변환
                converted = convert_table_headings(converted, part_num)
                table_count = len(re.findall(r'^#### Table', converted, re.MULTILINE))
                stats['tables_converted'] += table_count

                subsection['content'] = converted

    # 통계 출력
    print(f"\n=== 변환 통계 ===")
    print(f"Sections: {stats['sections']}")
    print(f"Subsections: {stats['subsections']}")
    print(f"Articles 변환: {stats['articles_converted']}")
    print(f"Tables 변환: {stats['tables_converted']}")

    if dry_run:
        print("\n[DRY RUN] 파일 저장 건너뜀")
        return stats

    # 백업 디렉토리 생성
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    # 원본 백업
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(json.load(open(input_path, 'r', encoding='utf-8')), f, indent=2, ensure_ascii=False)
    print(f"\n원본 백업: {backup_path}")

    # 변환 결과 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"변환 결과 저장: {output_path}")

    return stats

def verify_conversion(part_num: int):
    """변환 결과 검증"""

    output_path = DATA_DIR / f"part{part_num}_converted.json"

    if not output_path.exists():
        print(f"Error: {output_path} not found")
        return

    with open(output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"\n=== Part {part_num} 변환 결과 샘플 ===")

    # 첫 번째 subsection content 확인
    if data.get('sections') and data['sections'][0].get('subsections'):
        first_content = data['sections'][0]['subsections'][0]['content']
        print(f"\n[첫 번째 Subsection]")
        print(first_content[:800])

    # Article 헤딩 패턴 확인
    article_pattern = rf'^#### {part_num}\.\d+\.\d+\.\d+\.'
    all_articles = []

    for section in data.get('sections', []):
        for subsection in section.get('subsections', []):
            content = subsection.get('content', '')
            articles = re.findall(article_pattern, content, re.MULTILINE)
            all_articles.extend(articles)

    print(f"\n총 Article 헤딩: {len(all_articles)}")
    print("샘플 (처음 10개):")
    for a in all_articles[:10]:
        print(f"  {a}")

def apply_conversion(part_num: int):
    """변환 결과를 원본에 적용"""

    converted_path = DATA_DIR / f"part{part_num}_converted.json"
    original_path = DATA_DIR / f"part{part_num}.json"

    if not converted_path.exists():
        print(f"Error: {converted_path} not found. Run conversion first.")
        return False

    # 교체
    import shutil
    shutil.copy(converted_path, original_path)
    converted_path.unlink()

    print(f"Part {part_num} JSON 교체 완료")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_part_format.py <part_num> [--dry-run] [--apply] [--verify]")
        print("  --dry-run: 변환만 하고 파일 저장 안 함")
        print("  --apply: 변환 결과를 원본에 적용")
        print("  --verify: 변환 결과 검증")
        sys.exit(1)

    part_num = int(sys.argv[1])
    dry_run = "--dry-run" in sys.argv
    apply_flag = "--apply" in sys.argv
    verify_flag = "--verify" in sys.argv

    if apply_flag:
        apply_conversion(part_num)
    elif verify_flag:
        verify_conversion(part_num)
    else:
        convert_part_json(part_num, dry_run)
        if not dry_run:
            verify_conversion(part_num)
