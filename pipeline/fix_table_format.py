#!/usr/bin/env python3
"""
글로벌 테이블 형식 수정 스크립트

모든 테이블의 형식을 Part 11 스타일로 통일:
- Title + Forming Part를 한 줄로
- Notes to Table에 <h5> 태그
- Notes 항목에 - 대시 추가

Usage:
    python fix_table_format.py --part 8
    python fix_table_format.py --part 8 --dry-run  # 미리보기
"""

import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "codevault" / "public" / "data"


def fix_table_titles(content: str) -> str:
    """테이블 제목을 한 줄로 통일"""

    # 패턴 1: #### Table ... + 다음 줄에 *Forming Part...*
    # → #### Table ... Forming Part... (한 줄로)
    pattern1 = r'(#### Table \d+\.\d+\.\d+\.\d+\.?-?[A-Z]?[^\n]*)\n+\*([Ff]orming [Pp]art[^\*]+)\*'
    content = re.sub(pattern1, r'\1 \2', content)

    # 패턴 2a: <h4 class="table-title">Table X.X.X.X Title Forming Part...</h4> (한 줄에 모두 있음)
    # → #### Table X.X.X.X Title Forming Part...
    pattern2a = r'<h4[^>]*>Table (\d+\.\d+\.\d+\.\d+\.?-?[A-Z]?)\s+([^<]+)</h4>'
    content = re.sub(pattern2a, r'#### Table \1 \2', content)

    # 패턴 2b: <h4 class="table-title">Table ...</h4> + <p...>Forming Part...</p> (두 줄)
    # → #### Table ... Forming Part... (Markdown으로 변환)
    pattern2b = r'<h4[^>]*>Table (\d+\.\d+\.\d+\.\d+\.?-?[A-Z]?)\s*([^<]*)</h4>\s*(?:<p[^>]*><em>)?([Ff]orming [Pp]art[^<\n]*)(?:</em></p>)?'
    content = re.sub(pattern2b, r'#### Table \1 \2 \3', content)

    # 패턴 3: ### Table ... (제목만) + 다음 줄에 **제목** + 다음 줄에 *Forming...*
    pattern3 = r'### Table (\d+\.\d+\.\d+\.\d+\.?-?[A-Z]?)\n+\*\*([^\*]+)\*\*\n+\*([Ff]orming [Pp]art[^\*]+)\*'
    content = re.sub(pattern3, r'#### Table \1 \2 \3', content)

    # 패턴 4: ### Table ... (제목만) + 다음 줄에 **제목**
    pattern4 = r'### Table (\d+\.\d+\.\d+\.\d+\.?-?[A-Z]?)\n+\*\*([^\*]+)\*\*'
    content = re.sub(pattern4, r'#### Table \1 \2', content)

    # 패턴 5: ### **Table ... 제목** Forming Part...
    pattern5 = r'### \*\*Table (\d+\.\d+\.\d+\.\d+\.?-?[A-Z]?)\s+([^\*]+)\*\*\s*([Ff]orming [Pp]art[^\n]*)'
    content = re.sub(pattern5, r'#### Table \1 \2 \3', content)

    # 패턴 6: **Table ... 제목** Forming Part... (### 없음)
    pattern6 = r'\*\*Table (\d+\.\d+\.\d+\.\d+\.?-?[A-Z]?)\s+([^\*]+)\*\*\s*([Ff]orming [Pp]art[^\n]*)'
    content = re.sub(pattern6, r'#### Table \1 \2 \3', content)

    # 패턴 7: **Table ... 제목** (Forming Part 없음, ### 없음)
    pattern7 = r'\*\*Table (\d+\.\d+\.\d+\.\d+\.?-?[A-Z]?)\s+([^\*\n]+)\*\*'
    content = re.sub(pattern7, r'#### Table \1 \2', content)

    # 패턴 8: Table 제목이 두 줄에 걸쳐 있는 경우 (Forming Part가 별도 줄)
    pattern8 = r'(#### Table \d+\.\d+\.\d+\.\d+\.?-?[A-Z]?[^\n]*)\n+([Ff]orming [Pp]art of [Ss]entences?\s+[\d.,()and\s]+)'
    content = re.sub(pattern8, r'\1 \2', content)

    return content


def fix_notes_format(content: str) -> str:
    """Notes to Table 형식 수정"""

    # 먼저 기존에 잘못된 중복 태그 제거
    # 예: <h5 class=...><h5 class=...>Notes → <h5 class=...>Notes
    content = re.sub(
        r'(<h5 class="table-notes-title">)\s*<h5 class="table-notes-title">',
        r'\1',
        content
    )
    # 예: Notes to Table X:</h5></h5> → Notes to Table X:</h5>
    content = re.sub(r'(Notes to Table [\d.]+\.?-?[A-Z]?:)</h5></h5>', r'\1</h5>', content)

    # 이미 <h5>로 감싸진 Notes는 건너뛰기 위해 임시 마커 사용
    content = re.sub(
        r'<h5 class="table-notes-title">(Notes to Table [\d.]+\.?-?[A-Z]?:)</h5>',
        r'__NOTES_TAGGED__\1__END_NOTES__',
        content
    )

    # 패턴 1: **Notes to Table...:** → <h5 class="table-notes-title">Notes to Table...:</h5>
    pattern1 = r'\*\*Notes to Table (\d+\.\d+\.\d+\.\d+\.?-?[A-Z]?):\*\*'
    content = re.sub(pattern1, r'<h5 class="table-notes-title">Notes to Table \1:</h5>', content)

    # 패턴 2: Notes to Table...: (태그 없음, 볼드 없음) → <h5>...</h5>
    # 마커가 없는 것만 매칭
    pattern2 = r'(?<!__NOTES_TAGGED__)Notes to Table (\d+\.\d+\.\d+\.\d+\.?-?[A-Z]?):'
    content = re.sub(pattern2, r'<h5 class="table-notes-title">Notes to Table \1:</h5>', content)

    # 임시 마커 복원
    content = re.sub(
        r'__NOTES_TAGGED__(Notes to Table [\d.]+\.?-?[A-Z]?:)__END_NOTES__',
        r'<h5 class="table-notes-title">\1</h5>',
        content
    )

    # Notes 항목에 - 추가 (Note 번호가 연속일 때만)
    # 문제: Article Sentence (2), (3)...와 Table Note (1), (2)...를 구분해야 함
    # 해결: Notes 헤더 다음에 오는 연속된 Note 번호만 처리
    #       Note (1) → (2) → (3)이면 Notes 영역
    #       Note (1) → (2) 후 다시 (2)가 나오면 → Article 본문 시작
    lines = content.split('\n')
    in_notes = False
    last_note_num = 0
    result_lines = []

    for line in lines:
        if 'table-notes-title' in line or line.strip().startswith('Notes to Table'):
            in_notes = True
            last_note_num = 0
            result_lines.append(line)
            continue

        if in_notes:
            stripped = line.strip()

            # Notes 종료 조건 1: 명시적 경계
            if stripped.startswith('#### Table') or stripped.startswith('[ARTICLE:') or stripped.startswith('### '):
                in_notes = False
                last_note_num = 0
                result_lines.append(line)
                continue

            # Notes 종료 조건 2: 빈 줄 다음 일반 텍스트 (Table 번호나 Note 패턴 아님)
            # 이건 복잡하므로 아래에서 처리

            # (숫자) 패턴 확인
            note_match = re.match(r'^-?\s*\((\d+)\)', stripped)
            if note_match:
                current_num = int(note_match.group(1))

                # Notes 종료 조건 3: 번호가 다시 작아지면 (또는 같으면) Notes 종료
                # 예: Note (1), (2) 후 다시 (2)가 나오면 → Article Sentence 시작
                if current_num <= last_note_num and last_note_num > 0:
                    in_notes = False
                    last_note_num = 0
                    result_lines.append(line)
                    continue

                # 유효한 Notes 항목
                last_note_num = current_num

                # - 추가 (이미 없는 경우만)
                if not stripped.startswith('-'):
                    line = line.replace(stripped, f'- {stripped}', 1)

        result_lines.append(line)

    return '\n'.join(result_lines)


def fix_part_json(part_num: int, dry_run: bool = False):
    """Part JSON 파일의 테이블 형식 수정"""

    json_path = DATA_DIR / f"part{part_num}.json"

    if not json_path.exists():
        print(f"[ERROR] File not found: {json_path}")
        return

    print(f"\n{'='*60}")
    print(f"[FIX] part{part_num}.json")
    print(f"{'='*60}\n")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    fix_count = 0

    for section in data.get("sections", []):
        for subsection in section.get("subsections", []):
            original_content = subsection.get("content", "")

            # 수정 적용
            fixed_content = fix_table_titles(original_content)
            fixed_content = fix_notes_format(fixed_content)

            if fixed_content != original_content:
                fix_count += 1
                print(f"[FIXED] {subsection['id']}")

                if dry_run:
                    # 변경 부분 미리보기
                    print("  Before:")
                    for line in original_content.split('\n')[:5]:
                        if 'Table' in line:
                            print(f"    {line[:80]}...")
                    print("  After:")
                    for line in fixed_content.split('\n')[:5]:
                        if 'Table' in line:
                            print(f"    {line[:80]}...")
                else:
                    subsection["content"] = fixed_content

    if not dry_run and fix_count > 0:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n[SAVED] {json_path}")

    print(f"\n[TOTAL] {fix_count} subsections fixed")

    if dry_run:
        print("\n[DRY RUN] No changes saved. Remove --dry-run to apply.")


def main():
    part_num = 8
    dry_run = False

    args = sys.argv[1:]
    if '--part' in args:
        idx = args.index('--part')
        part_num = int(args[idx + 1])
    if '--dry-run' in args:
        dry_run = True

    fix_part_json(part_num, dry_run)


if __name__ == "__main__":
    main()
