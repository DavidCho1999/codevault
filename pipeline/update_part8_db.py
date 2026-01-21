#!/usr/bin/env python3
"""
Part 8 JSON → DB 업데이트 스크립트
기존 Part 8 subsection content를 새 JSON으로 교체
"""

import json
import sqlite3
import os

# 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, 'codevault', 'public', 'data', 'part8.json')
DB_PATH = os.path.join(BASE_DIR, 'data', 'obc.db')


def update_part8():
    print("=== Part 8 DB 업데이트 ===\n")

    # 1. JSON 로드
    print(f"Loading {JSON_PATH}...")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. DB 연결
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updated_count = 0
    inserted_count = 0

    # 3. 각 Section/Subsection 처리
    for section in data.get('sections', []):
        sec_id = section.get('id')
        sec_title = section.get('title', '')

        # Section 존재 확인 및 업데이트
        cursor.execute("SELECT id FROM nodes WHERE id = ?", (sec_id,))
        if cursor.fetchone():
            cursor.execute(
                "UPDATE nodes SET title = ? WHERE id = ?",
                (sec_title, sec_id)
            )
        else:
            # Section 삽입
            cursor.execute('''
                INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
                VALUES (?, 'section', 8, '8', ?, NULL, NULL, ?)
            ''', (sec_id, sec_title, int(sec_id.split('.')[1])))
            inserted_count += 1
            print(f"[+] Section inserted: {sec_id}")

        # Subsections 처리
        for sub_seq, subsection in enumerate(section.get('subsections', []), start=1):
            sub_id = subsection.get('id')
            sub_title = subsection.get('title', '')
            sub_content = subsection.get('content', '')

            # Subsection 존재 확인
            cursor.execute("SELECT id, content FROM nodes WHERE id = ?", (sub_id,))
            existing = cursor.fetchone()

            if existing:
                old_len = len(existing[1] or '')
                new_len = len(sub_content)
                # Content 업데이트
                cursor.execute(
                    "UPDATE nodes SET title = ?, content = ? WHERE id = ?",
                    (sub_title, sub_content, sub_id)
                )
                updated_count += 1
                print(f"[U] {sub_id}: {old_len} → {new_len} chars")
            else:
                # Subsection 삽입
                cursor.execute('''
                    INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
                    VALUES (?, 'subsection', 8, ?, ?, ?, NULL, ?)
                ''', (sub_id, sec_id, sub_title, sub_content, sub_seq))
                inserted_count += 1
                print(f"[+] {sub_id}: {len(sub_content)} chars")

    # 4. 커밋
    conn.commit()

    # 5. 검증
    print(f"\n=== 결과 ===")
    print(f"Updated: {updated_count}")
    print(f"Inserted: {inserted_count}")

    # HTML 테이블 개수 확인
    cursor.execute("""
        SELECT id,
               (LENGTH(content) - LENGTH(REPLACE(content, '<table', ''))) / 6 as table_count
        FROM nodes
        WHERE id LIKE '8.%' AND type = 'subsection'
        ORDER BY id
    """)
    print("\n=== Subsection별 <table> 개수 ===")
    total_tables = 0
    for row in cursor.fetchall():
        if row[1] > 0:
            print(f"  {row[0]}: {row[1]} tables")
            total_tables += row[1]
    print(f"\n총 테이블: {total_tables}개")

    # FTS 인덱스 업데이트
    print("\n=== FTS 인덱스 업데이트 ===")
    # Part 8 기존 인덱스 삭제 후 재삽입
    cursor.execute("DELETE FROM search_index WHERE node_id LIKE '8.%'")
    cursor.execute("""
        INSERT INTO search_index (node_id, title, content)
        SELECT id, title, content FROM nodes WHERE id LIKE '8.%' AND content IS NOT NULL
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM search_index WHERE node_id LIKE '8.%'")
    print(f"Part 8 FTS 인덱스: {cursor.fetchone()[0]}개")

    conn.close()
    print(f"\nDB 업데이트 완료: {DB_PATH}")


if __name__ == "__main__":
    update_part8()
