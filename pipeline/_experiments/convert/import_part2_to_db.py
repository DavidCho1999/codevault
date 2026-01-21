#!/usr/bin/env python3
"""
Part 2 JSON → DB 임포트 스크립트
Part 2: Objectives (Division A)
"""

import json
import sqlite3
import os

# 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
JSON_PATH = os.path.join(BASE_DIR, 'codevault', 'public', 'data', 'part2.json')
DB_PATH = os.path.join(BASE_DIR, 'data', 'obc.db')


def import_part2():
    print("=== Part 2 DB 임포트 ===\n")

    # 1. JSON 로드
    print(f"Loading {JSON_PATH}...")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. DB 연결
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 3. 기존 Part 2 데이터 삭제
    cursor.execute("DELETE FROM search_index WHERE node_id LIKE '2.%' OR node_id = '2'")
    cursor.execute("DELETE FROM nodes WHERE id LIKE '2.%' OR id = '2'")
    print("Deleted existing Part 2 data")

    inserted_count = 0

    # 4. Part 노드 삽입
    part_id = data.get('id', '2')
    part_title = data.get('title', 'Objectives')

    cursor.execute('''
        INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
        VALUES (?, 'part', 2, NULL, ?, NULL, NULL, 2)
    ''', (part_id, part_title))
    inserted_count += 1
    print(f"[+] Part: {part_id} - {part_title}")

    # 5. 각 Section/Subsection 처리
    for sec_seq, section in enumerate(data.get('sections', []), start=1):
        sec_id = section.get('id')
        sec_title = section.get('title', '')

        # Section 삽입
        cursor.execute('''
            INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
            VALUES (?, 'section', 2, '2', ?, NULL, NULL, ?)
        ''', (sec_id, sec_title, sec_seq))
        inserted_count += 1
        print(f"  [+] Section: {sec_id} - {sec_title}")

        # Subsections 처리
        for sub_seq, subsection in enumerate(section.get('subsections', []), start=1):
            sub_id = subsection.get('id')
            sub_title = subsection.get('title', '')
            sub_content = subsection.get('content', '')

            # Subsection 삽입
            cursor.execute('''
                INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
                VALUES (?, 'subsection', 2, ?, ?, ?, NULL, ?)
            ''', (sub_id, sec_id, sub_title, sub_content, sub_seq))
            inserted_count += 1
            print(f"    [+] Subsection: {sub_id} - {sub_title} ({len(sub_content)} chars)")

    # 6. 커밋
    conn.commit()

    # 7. 검증
    print(f"\n=== 결과 ===")
    print(f"Inserted: {inserted_count} nodes")

    # 노드 개수 확인
    cursor.execute("SELECT type, COUNT(*) FROM nodes WHERE part = 2 GROUP BY type ORDER BY type")
    print("\n노드 타입별 개수:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    # FTS 인덱스 업데이트
    print("\n=== FTS 인덱스 업데이트 ===")
    cursor.execute("""
        INSERT INTO search_index (node_id, title, content)
        SELECT id, title, content FROM nodes WHERE part = 2 AND (content IS NOT NULL OR title IS NOT NULL)
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM search_index WHERE node_id LIKE '2.%' OR node_id = '2'")
    print(f"Part 2 FTS 인덱스: {cursor.fetchone()[0]}개")

    conn.close()
    print(f"\nDB 임포트 완료: {DB_PATH}")


if __name__ == "__main__":
    import_part2()
