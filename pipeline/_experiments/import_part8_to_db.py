# -*- coding: utf-8 -*-
"""
Part 8 JSON을 SQLite DB에 삽입
Part 8: Sewage Systems (301880.pdf pages 680-709)
"""

import json
import sqlite3
from pathlib import Path

JSON_FILE = Path("codevault/public/data/part8.json")
DB_FILE = Path("obc.db")


def import_part8_to_db():
    """Part 8 데이터를 DB에 삽입"""

    # JSON 로드
    print("Loading Part 8 JSON...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # DB 연결
    print(f"Connecting to {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 기존 Part 8 데이터 삭제 (있으면)
    print("Removing existing Part 8 data...")
    cursor.execute("DELETE FROM nodes WHERE id LIKE '8.%'")
    cursor.execute("DELETE FROM search_index WHERE node_id LIKE '8.%'")

    # Part 번호
    part_num = int(data["id"])  # 8

    seq = 0

    for section in data["sections"]:
        section_id = section["id"]
        section_title = section["title"]
        section_page = section.get("page", 680)  # Part 8 시작 페이지

        # Section 노드 삽입 (part 필드 포함)
        cursor.execute("""
            INSERT INTO nodes (id, type, part, parent_id, title, page, content, seq)
            VALUES (?, 'section', ?, NULL, ?, ?, NULL, ?)
        """, (section_id, part_num, section_title, section_page, seq))
        seq += 1

        for subsection in section.get("subsections", []):
            sub_id = subsection["id"]
            sub_title = subsection["title"]
            sub_page = subsection.get("page", section_page)

            # Part 8에는 articles 배열 없음 - content 직접 사용
            sub_content = subsection.get("content", "")

            # Subsection 노드 삽입 (part 필드 포함)
            cursor.execute("""
                INSERT INTO nodes (id, type, part, parent_id, title, page, content, seq)
                VALUES (?, 'subsection', ?, ?, ?, ?, ?, ?)
            """, (sub_id, part_num, section_id, sub_title, sub_page, sub_content, seq))
            seq += 1

            # FTS5 인덱스에 추가
            if sub_content:
                cursor.execute("""
                    INSERT INTO search_index (node_id, title, content)
                    VALUES (?, ?, ?)
                """, (sub_id, sub_title, sub_content))

    conn.commit()

    # 통계 출력
    cursor.execute("SELECT COUNT(*) FROM nodes WHERE id LIKE '8.%'")
    node_count = cursor.fetchone()[0]
    print(f"\nInserted {node_count} nodes for Part 8")

    # 확인
    cursor.execute("SELECT id, type, title FROM nodes WHERE id LIKE '8.%' ORDER BY seq")
    rows = cursor.fetchall()
    print("\n=== Part 8 Nodes ===")
    for row in rows:
        print(f"  {row[0]}: [{row[1]}] {row[2]}")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    import_part8_to_db()
