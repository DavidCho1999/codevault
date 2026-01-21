"""
validate_part9.py - Part 9 데이터 자동 검증 테스트
- 섹션별 Article 수 검증
- 테이블 수 검증
- 필수 콘텐츠 존재 여부 검증
"""

import json
import os
import re
import sys
from typing import Dict, List, Tuple

sys.stdout.reconfigure(encoding='utf-8')

# 경로 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '../codevault/public/data'))

# 예상 데이터 (OBC 원본 기준)
EXPECTED_DATA = {
    "9.1.1": {"title": "Application", "min_articles": 8},
    "9.2.1": {"title": "General", "min_articles": 1},
    "9.3.1": {"title": "Concrete", "min_articles": 9, "tables": ["Table 9.3.1.7"]},
    "9.4.3": {"title": "Deflections", "min_articles": 1, "tables": ["Table 9.4.3.1"]},
    "9.6.1": {"title": "General", "min_articles": 2, "tables": [
        "Table 9.6.1.3.-A", "Table 9.6.1.3.-B", "Table 9.6.1.3.-C",
        "Table 9.6.1.3.-D", "Table 9.6.1.3.-E", "Table 9.6.1.3.-F", "Table 9.6.1.3.-G"
    ]},
    "9.7.3": {"title": "Performance of Windows, Doors and Skylights", "min_articles": 1},
    "9.8.1": {"title": "Application", "min_articles": 1},
    "9.8.2": {"title": "Stair Dimensions", "min_articles": 1},
    "9.10.9": {"title": "Fire Separations", "min_articles": 1},
    "9.10.14": {"title": "Spatial Separation Between Buildings", "min_articles": 1},
    "9.15.3": {"title": "Footings", "min_articles": 9, "tables": ["Table 9.15.3.4"]},
    "9.15.4": {"title": "Foundation Walls", "min_articles": 1, "tables": [
        "Table 9.15.4.2.-A", "Table 9.15.4.2.-B"
    ]},
    "9.20.6": {"title": "Thickness and Height", "min_articles": 1},
    "9.23.3": {"title": "Fasteners and Connectors", "min_articles": 5, "tables": [
        "Table 9.23.3.1", "Table 9.23.3.4",
        "Table 9.23.3.5.-A", "Table 9.23.3.5.-B", "Table 9.23.3.5.-C"
    ]},
    "9.23.4": {"title": "Maximum Spans", "min_articles": 5, "tables": ["Table 9.23.4.3"]},
    "9.25.2": {"title": "Thermal Insulation", "min_articles": 1},
}


def load_json(filename: str) -> dict:
    """JSON 파일 로드"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def count_articles(content: str, section_id: str) -> int:
    """섹션 내 Article 수 카운트"""
    # 패턴: 9.X.X.1., 9.X.X.2., ...
    pattern = rf'{re.escape(section_id)}\.(\d+)\.'
    matches = re.findall(pattern, content)
    if matches:
        return max(int(m) for m in matches)
    return 0


def validate_section(section: dict, expected: dict, tables_data: dict) -> List[str]:
    """단일 섹션 검증"""
    errors = []
    section_id = section['id']
    content = section.get('content', '')

    # 1. 제목 검증
    if expected.get('title') and expected['title'].lower() not in section.get('title', '').lower():
        errors.append(f"제목 불일치: '{section.get('title')}' (예상: '{expected['title']}')")

    # 2. 콘텐츠 존재 검증
    if not content or len(content) < 100:
        errors.append(f"콘텐츠 부족 또는 없음 (길이: {len(content)})")

    # 3. Article 수 검증
    if expected.get('min_articles'):
        article_count = count_articles(content, section_id)
        if article_count < expected['min_articles']:
            errors.append(f"Article 수 부족: {article_count}개 (최소: {expected['min_articles']}개)")

    # 4. 테이블 검증
    if expected.get('tables'):
        for table_id in expected['tables']:
            if table_id not in tables_data:
                errors.append(f"테이블 누락: {table_id}")
            else:
                table = tables_data[table_id]
                # 테이블 HTML 존재 확인
                if not table.get('html') or len(table['html']) < 50:
                    errors.append(f"테이블 HTML 부족: {table_id}")

    return errors


def validate_table_notes(tables_data: dict) -> List[str]:
    """테이블 Notes 검증"""
    errors = []

    # Table 9.3.1.7 Notes 확인
    if 'Table 9.3.1.7' in tables_data:
        html = tables_data['Table 9.3.1.7'].get('html', '')
        if 'Notes to Table' not in html or '40 kg bag' not in html:
            errors.append("Table 9.3.1.7: Notes 누락")

    return errors


def validate_no_duplicates(tables_data: dict) -> List[str]:
    """테이블 중복 검증 (HTML 해시 기반)"""
    errors = []
    html_hashes = {}

    for table_id, table in tables_data.items():
        html = table.get('html', '')
        # 간단한 해시 (길이 + 첫 100자)
        h = f"{len(html)}:{html[:100]}"

        if h in html_hashes and len(html) > 200:  # 작은 테이블 제외
            errors.append(f"중복 의심: {table_id} ↔ {html_hashes[h]}")
        else:
            html_hashes[h] = table_id

    return errors


def run_validation():
    """전체 검증 실행"""
    print("=" * 70)
    print("Part 9 데이터 자동 검증")
    print("=" * 70)

    # 데이터 로드
    try:
        part9_data = load_json('part9.json')
        tables_data = load_json('part9_tables.json')
    except FileNotFoundError as e:
        print(f"ERROR: 파일을 찾을 수 없습니다 - {e}")
        return False

    # 섹션 인덱스 생성
    sections_map = {}
    for section in part9_data.get('sections', []):
        for subsection in section.get('subsections', []):
            sections_map[subsection['id']] = subsection

    print(f"\n로드된 데이터:")
    print(f"  - 섹션 수: {len(sections_map)}")
    print(f"  - 테이블 수: {len(tables_data)}")

    # 검증 실행
    results = {
        'passed': [],
        'failed': []
    }

    print(f"\n{'=' * 70}")
    print("섹션별 검증 결과")
    print("=" * 70)

    for section_id, expected in EXPECTED_DATA.items():
        if section_id not in sections_map:
            results['failed'].append((section_id, ["섹션을 찾을 수 없음"]))
            print(f"\n❌ {section_id}: 섹션을 찾을 수 없음")
            continue

        section = sections_map[section_id]
        errors = validate_section(section, expected, tables_data)

        if errors:
            results['failed'].append((section_id, errors))
            print(f"\n❌ {section_id} ({section.get('title', 'N/A')}):")
            for err in errors:
                print(f"   - {err}")
        else:
            results['passed'].append(section_id)
            print(f"\n✅ {section_id} ({section.get('title', 'N/A')})")

    # 테이블 Notes 검증
    print(f"\n{'=' * 70}")
    print("테이블 Notes 검증")
    print("=" * 70)

    notes_errors = validate_table_notes(tables_data)
    if notes_errors:
        for err in notes_errors:
            print(f"❌ {err}")
    else:
        print("✅ 모든 테이블 Notes 정상")

    # 중복 검증
    print(f"\n{'=' * 70}")
    print("테이블 중복 검증")
    print("=" * 70)

    dup_errors = validate_no_duplicates(tables_data)
    if dup_errors:
        for err in dup_errors:
            print(f"⚠️ {err}")
    else:
        print("✅ 중복 테이블 없음")

    # 최종 결과
    print(f"\n{'=' * 70}")
    print("최종 결과")
    print("=" * 70)

    total = len(EXPECTED_DATA)
    passed = len(results['passed'])
    failed = len(results['failed'])

    print(f"  통과: {passed}/{total}")
    print(f"  실패: {failed}/{total}")

    if failed == 0 and not notes_errors:
        print(f"\n🎉 모든 검증 통과!")
        return True
    else:
        print(f"\n⚠️ 일부 검증 실패")
        return False


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
