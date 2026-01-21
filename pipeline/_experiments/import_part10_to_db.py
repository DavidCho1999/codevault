# -*- coding: utf-8 -*-
"""
Part 10 JSON을 SQLite DB에 삽입
"""

import json
import sqlite3
from pathlib import Path

JSON_FILE = Path("codevault/public/data/part10.json")
DB_FILE = Path("obc.db")

def import_part10_to_db():
    """Part 10 데이터를 DB에 삽입"""

    # JSON 로드
    print("Loading Part 10 JSON...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # DB 연결
    print(f"Connecting to {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 기존 Part 10 데이터 삭제 (있으면)
    print("Removing existing Part 10 data...")
    cursor.execute("DELETE FROM nodes WHERE id LIKE '10.%'")
    cursor.execute("DELETE FROM search_index WHERE node_id LIKE '10.%'")

    # Part 번호
    part_num = int(data["id"])  # 10

    seq = 0

    for section in data["sections"]:
        section_id = section["id"]
        section_title = section["title"]
        section_page = section.get("page", 1131)

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

            # articles 배열의 콘텐츠를 합쳐서 subsection.content 생성
            articles = subsection.get("articles", [])
            if articles:
                content_parts = []
                for article in articles:
                    art_id = article["id"]
                    art_title = article.get("title", "")
                    art_content = article.get("content", "")
                    # [ARTICLE:id:title] 마커 추가
                    content_parts.append(f"[ARTICLE:{art_id}:{art_title}]")
                    content_parts.append(art_content)
                sub_content = "\n".join(content_parts)
            else:
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
    cursor.execute("SELECT COUNT(*) FROM nodes WHERE id LIKE '10.%'")
    node_count = cursor.fetchone()[0]
    print(f"\nInserted {node_count} nodes for Part 10")

    # 확인
    cursor.execute("SELECT id, type, title FROM nodes WHERE id LIKE '10.%' ORDER BY seq")
    rows = cursor.fetchall()
    print("\n=== Part 10 Nodes ===")
    for row in rows:
        print(f"  {row[0]}: [{row[1]}] {row[2]}")

    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    import_part10_to_db()
