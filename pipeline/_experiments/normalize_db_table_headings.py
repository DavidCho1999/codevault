"""
DB의 nodes 테이블에서 테이블 헤딩을 정규화하는 스크립트

변환 전: ### **Table 11.2.1.1.-A Construction Index** Forming Part of Sentence 11.2.1.1.(1)
또는:    ### Table 11.2.1.1.-A Construction Index Forming Part of Sentence 11.2.1.1.(1)

변환 후:
    ### Table 11.2.1.1.-A
    **Construction Index**
    *Forming Part of Sentence 11.2.1.1.(1)*
"""

import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "obc.db"


def normalize_table_heading(content: str) -> str:
    """테이블 헤딩 정규화"""
    if not content:
        return content

    lines = content.split('\n')
    result = []

    # 패턴 1: ### **Table X.X.X.X.-Y Caption** Forming Part of...
    # 패턴 2: ### Table X.X.X.X.-Y Caption Forming Part of... (볼드 없음)
    # 패턴 3: Table X.X.X.X.-Y Caption</h4> (HTML 태그 포함)
    table_pattern_bold = re.compile(
        r'^(#+)\s*\*\*Table\s+'           # ### **Table
        r'([\d.]+-[A-Z](?:/[A-Z])?'       # 11.2.1.1.-A 또는 11.5.1.1.-D/E
        r'(?:\(\d+\))*'                   # 선택적 (1)(4) 등
        r'(?:\s*\(Cont\'d\))?)'           # 선택적 (Cont'd)
        r'\s+(.+?)\*\*'                   # Caption**
        r'\s*(Forming Part of .+)?$'      # Forming Part of... (선택적)
    )

    table_pattern_plain = re.compile(
        r'^(#+)\s*Table\s+'               # ### Table
        r'([\d.]+-[A-Z](?:/[A-Z])?'       # 11.2.1.1.-A 또는 11.5.1.1.-D/E
        r'(?:\(\d+\))*'                   # 선택적 (1)(4) 등
        r'(?:\s*\(Cont\'d\))?)'           # 선택적 (Cont'd)
        r'\s+(.+?)'                       # Caption (Forming Part of 전까지)
        r'\s+(Forming Part of .+)$'       # Forming Part of...
    )

    # 패턴 3: HTML 태그 포함 (<h4 class="table-title">Table ... Caption</h4>)
    table_pattern_html = re.compile(
        r'^<h[45][^>]*>Table\s+'          # <h4 class="...">Table
        r'([\d.]+-[A-Z](?:/[A-Z])?'       # 11.2.1.1.-A 또는 11.5.1.1.-D/E
        r'(?:\(\d+\))*'                   # 선택적 (1)(4) 등
        r'(?:\s*\(Cont\'d\))?)'           # 선택적 (Cont'd)
        r'\s+(.+?)</h[45]>$'              # Caption</h4> 또는 </h5>
    )

    i = 0
    while i < len(lines):
        line = lines[i]

        # 패턴 1: 볼드 포함
        match = table_pattern_bold.match(line)
        if match:
            heading_level = match.group(1)
            table_id = match.group(2)
            caption = match.group(3).strip()
            forming_part = match.group(4)

            result.append(f"{heading_level} Table {table_id}")
            result.append(f"**{caption}**")
            if forming_part:
                result.append(f"*{forming_part.strip()}*")
            result.append("")
            i += 1
            continue

        # 패턴 2: 볼드 없음
        match = table_pattern_plain.match(line)
        if match:
            heading_level = match.group(1)
            table_id = match.group(2)
            caption = match.group(3).strip()
            forming_part = match.group(4)

            result.append(f"{heading_level} Table {table_id}")
            result.append(f"**{caption}**")
            if forming_part:
                result.append(f"*{forming_part.strip()}*")
            result.append("")
            i += 1
            continue

        # 패턴 3: HTML 태그 포함 (Table ... Caption</h4>)
        match = table_pattern_html.match(line)
        if match:
            table_id = match.group(1)
            caption = match.group(2).strip()

            # 다음 몇 줄 내에서 "Forming Part of..."를 찾음 (빈 줄 건너뜀)
            forming_part = ""
            skip_count = 0
            for j in range(i + 1, min(i + 4, len(lines))):
                next_line = lines[j].strip()
                if not next_line:
                    skip_count += 1
                    continue
                if next_line.startswith("Forming Part of"):
                    forming_part = next_line
                    skip_count += 1
                    break
                else:
                    break  # "Forming Part of"가 아닌 다른 내용이 나오면 중단

            result.append(f"### Table {table_id}")
            result.append(f"**{caption}**")
            if forming_part:
                result.append(f"*{forming_part}*")
            result.append("")
            i += 1 + skip_count
            continue

        result.append(line)
        i += 1

    return '\n'.join(result)


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Part 10, 11, 12의 content 가져오기
    cursor.execute("""
        SELECT id, content FROM nodes
        WHERE (id LIKE '10.%' OR id LIKE '11.%' OR id LIKE '12.%')
        AND content IS NOT NULL
        AND content LIKE '%Table %'
    """)

    rows = cursor.fetchall()
    print(f"처리할 노드: {len(rows)}개")

    updated = 0
    for node_id, content in rows:
        normalized = normalize_table_heading(content)
        if normalized != content:
            cursor.execute("""
                UPDATE nodes SET content = ? WHERE id = ?
            """, (normalized, node_id))
            updated += 1
            print(f"  업데이트: {node_id}")

    conn.commit()
    print(f"\n=== 결과 ===")
    print(f"업데이트된 노드: {updated}개")

    # 샘플 확인
    cursor.execute("""
        SELECT id, substr(content, 1, 500) FROM nodes
        WHERE id = '11.5.1'
    """)
    row = cursor.fetchone()
    if row:
        print(f"\n=== 샘플: {row[0]} ===")
        print(row[1])

    conn.close()


if __name__ == "__main__":
    main()
