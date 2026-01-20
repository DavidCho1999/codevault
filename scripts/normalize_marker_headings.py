"""
Marker 출력 MD 파일의 OBC 헤딩 레벨 정규화 스크립트

규칙:
- 9.X.       → ## (Section)
- 9.X.X.     → ### (Subsection)
- 9.X.X.X.   → #### (Article)

테이블 헤딩 정규화:
- ### **Table X.X.X.X.-Y Caption** Forming Part of...
  → ### Table X.X.X.X.-Y
    **Caption**
    *Forming Part of...*
"""

import re
import sys
from pathlib import Path


def normalize_obc_headings(md_content: str, parts: list = None) -> str:
    """OBC 섹션 번호 기반으로 헤딩 레벨 정규화

    Args:
        md_content: 마크다운 내용
        parts: 처리할 Part 번호 리스트 (기본값: [9, 10, 11, 12])
    """
    if parts is None:
        parts = [9, 10, 11, 12]

    # Part 번호를 정규식 패턴으로 변환: (9|10|11|12)
    part_pattern = '(' + '|'.join(str(p) for p in parts) + ')'

    lines = md_content.split('\n')
    result = []

    for line in lines:
        # <span> 태그 제거한 버전으로 패턴 매칭
        clean_line = re.sub(r'<[^>]+>', '', line)

        # Article: X.X.X.X. 또는 X.X.XA.X. 또는 X.X.X.XA.
        if re.match(rf'^#+\s*{part_pattern}\.\d+\.\d+[A-Z]?\.\d+', clean_line):
            line = re.sub(r'^#+', '####', line)
        # Subsection: X.X.X. 또는 X.X.XA. (뒤에 숫자 없음)
        elif re.match(rf'^#+\s*{part_pattern}\.\d+\.\d+[A-Z]?\.(?!\d)', clean_line):
            line = re.sub(r'^#+', '###', line)
        # Section: X.X. 또는 Section X.X. (뒤에 숫자 없음)
        elif re.match(rf'^#+\s*(Section\s+)?{part_pattern}\.\d+\.(?!\d)', clean_line):
            line = re.sub(r'^#+', '##', line)

        result.append(line)

    return '\n'.join(result)


def normalize_table_headings(md_content: str) -> str:
    """테이블 헤딩 형식 정규화

    변환 전: ### **Table 11.2.1.1.-A Construction Index** Forming Part of Sentence 11.2.1.1.(1)
    변환 후:
        ### Table 11.2.1.1.-A
        **Construction Index**
        *Forming Part of Sentence 11.2.1.1.(1)*
    """
    lines = md_content.split('\n')
    result = []

    # 패턴: ### **Table X.X.X.X.-Y Caption** Forming Part of...
    # 또는: ### **Table X.X.X.X.-Y(N)(M) Caption** Forming Part of...
    table_pattern = re.compile(
        r'^(#+)\s*\*\*Table\s+'           # ### **Table
        r'([\d.]+-[A-Z](?:/[A-Z])?'       # 11.2.1.1.-A 또는 11.5.1.1.-D/E
        r'(?:\(\d+\))*'                   # 선택적 (1)(4) 등
        r'(?:\s*\(Cont\'d\))?)'           # 선택적 (Cont'd)
        r'\s+(.+?)\*\*'                   # Caption**
        r'\s*(Forming Part of .+)?$'      # Forming Part of... (선택적)
    )

    for line in lines:
        match = table_pattern.match(line)
        if match:
            heading_level = match.group(1)  # ###
            table_id = match.group(2)       # 11.2.1.1.-A (전체 ID 포함)
            caption = match.group(3).strip()  # Construction Index
            forming_part = match.group(4)   # Forming Part of...

            # 새 형식으로 변환
            result.append(f"{heading_level} Table {table_id}")
            result.append(f"**{caption}**")
            if forming_part:
                result.append(f"*{forming_part.strip()}*")
            result.append("")  # 빈 줄 추가
        else:
            result.append(line)

    return '\n'.join(result)


def analyze_changes(original: str, normalized: str) -> dict:
    """변경 사항 분석"""
    orig_lines = original.split('\n')
    norm_lines = normalized.split('\n')

    changes = {
        'total_lines': len(orig_lines),
        'changed': 0,
        'examples': []
    }

    for i, (orig, norm) in enumerate(zip(orig_lines, norm_lines)):
        if orig != norm:
            changes['changed'] += 1
            if len(changes['examples']) < 10:  # 예시 10개만
                changes['examples'].append({
                    'line': i + 1,
                    'before': orig[:80],
                    'after': norm[:80]
                })

    return changes


def main():
    input_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output_marker/301880_full.md")

    if not input_file.exists():
        print(f"파일 없음: {input_file}")
        return

    print(f"처리 중: {input_file}")

    # 읽기
    content = input_file.read_text(encoding='utf-8')

    # 1단계: OBC 섹션 헤딩 정규화
    normalized = normalize_obc_headings(content)

    # 2단계: 테이블 헤딩 정규화
    normalized = normalize_table_headings(normalized)

    # 분석
    changes = analyze_changes(content, normalized)

    print(f"\n=== 분석 결과 ===")
    print(f"전체 라인: {changes['total_lines']}")
    print(f"변경된 라인: {changes['changed']}")

    print(f"\n=== 변경 예시 (최대 10개) ===")
    for ex in changes['examples']:
        print(f"Line {ex['line']}:")
        print(f"  Before: {ex['before']}")
        print(f"  After:  {ex['after']}")
        print()

    # 저장
    output_file = input_file.with_stem(input_file.stem + "_normalized")
    output_file.write_text(normalized, encoding='utf-8')
    print(f"\n저장됨: {output_file}")


if __name__ == "__main__":
    main()
