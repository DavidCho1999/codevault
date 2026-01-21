#!/usr/bin/env python3
"""
Part 6 JSON → DB 임포트 스크립트
Part 6: Heating, Ventilating and Air-Conditioning
"""

import json
import sqlite3
import os
import re

# 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, 'codevault', 'public', 'data', 'part6.json')
DB_PATH = os.path.join(BASE_DIR, 'data', 'obc.db')


def get_next_seq(conn: sqlite3.Connection) -> int:
    """다음 seq 값 가져오기"""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(seq) FROM nodes")
    result = cursor.fetchone()[0]
    return (result or 0) + 1


def parse_articles_from_content(subsection_id: str, content: str) -> list[dict]:
    """Subsection content에서 Article 파싱"""
    if not content:
        return []

    # 마커 패턴: [ARTICLE:ID:Title]
    pattern = r'\[ARTICLE:([^:]+):([^\]]*)\]'
    matches = list(re.finditer(pattern, content))

    if not matches:
        return []

    articles = []
    for i, match in enumerate(matches):
        article_id = match.group(1).strip()
        article_title = match.group(2).strip()

        # content 범위: 현재 마커 끝 ~ 다음 마커 시작 (또는 끝)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        article_content = content[start:end].strip()

        articles.append({
            'id': article_id,
            'title': article_title,
            'content': article_content,
            'parent_id': subsection_id
        })

    return articles


def import_part6():
    print("=== Part 6 DB 임포트 ===\n")

    # 1. JSON 로드
    print(f"Loading {JSON_PATH}...")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. DB 연결
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    seq = get_next_seq(conn)
    inserted_parts = 0
    inserted_sections = 0
    inserted_subsections = 0
    inserted_articles = 0
    updated_count = 0

    # 3. Part 노드 확인/생성
    cursor.execute("SELECT id FROM nodes WHERE id = '6'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
            VALUES ('6', 'part', 6, NULL, 'Heating, Ventilating and Air-Conditioning', NULL, NULL, ?)
        ''', (seq,))
        seq += 1
        inserted_parts += 1
        print("[+] Part 6 inserted")

    # 4. 각 Section/Subsection 처리
    for section in data.get('sections', []):
        sec_id = section.get('id')
        sec_title = section.get('title', '')

        # Section 존재 확인
        cursor.execute("SELECT id FROM nodes WHERE id = ?", (sec_id,))
        if cursor.fetchone():
            cursor.execute(
                "UPDATE nodes SET title = ? WHERE id = ?",
                (sec_title, sec_id)
            )
            updated_count += 1
        else:
            # Section 삽입
            cursor.execute('''
                INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
                VALUES (?, 'section', 6, '6', ?, NULL, NULL, ?)
            ''', (sec_id, sec_title, seq))
            seq += 1
            inserted_sections += 1
            print(f"[+] Section: {sec_id} - {sec_title}")

        # Subsections 처리
        for sub_seq, subsection in enumerate(section.get('subsections', []), start=1):
            sub_id = subsection.get('id')
            sub_title = subsection.get('title', '')
            sub_content = subsection.get('content', '')

            # Alternative Subsection 타입 결정 (예: 6.1.1A)
            sub_type = 'alt_subsection' if sub_id[-1].isalpha() and sub_id[-2].isdigit() else 'subsection'

            # Subsection 존재 확인
            cursor.execute("SELECT id, content FROM nodes WHERE id = ?", (sub_id,))
            existing = cursor.fetchone()

            if existing:
                old_len = len(existing[1] or '')
                new_len = len(sub_content)
                cursor.execute(
                    "UPDATE nodes SET title = ?, content = ?, type = ? WHERE id = ?",
                    (sub_title, sub_content, sub_type, sub_id)
                )
                updated_count += 1
                if old_len != new_len:
                    print(f"[U] {sub_id}: {old_len} → {new_len} chars")
            else:
                cursor.execute('''
                    INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
                    VALUES (?, ?, 6, ?, ?, ?, NULL, ?)
                ''', (sub_id, sub_type, sec_id, sub_title, sub_content, seq))
                seq += 1
                inserted_subsections += 1
                print(f"[+] {sub_type}: {sub_id} ({len(sub_content)} chars)")

            # Articles 추가/업데이트
            articles = parse_articles_from_content(sub_id, sub_content)
            for article in articles:
                cursor.execute("SELECT id, content FROM nodes WHERE id = ?", (article['id'],))
                existing = cursor.fetchone()
                if existing:
                    # 기존 Article 업데이트
                    old_len = len(existing[1] or '')
                    new_len = len(article['content'])
                    cursor.execute(
                        "UPDATE nodes SET title = ?, content = ? WHERE id = ?",
                        (article['title'], article['content'], article['id'])
                    )
                    updated_count += 1
                    if old_len != new_len:
                        print(f"[U] Article {article['id']}: {old_len} → {new_len} chars")
                else:
                    cursor.execute('''
                        INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
                        VALUES (?, 'article', 6, ?, ?, ?, NULL, ?)
                    ''', (
                        article['id'],
                        article['parent_id'],
                        article['title'],
                        article['content'],
                        seq
                    ))
                    seq += 1
                    inserted_articles += 1

    # 5. 커밋
    conn.commit()

    # 6. 결과 출력
    print(f"\n=== 결과 ===")
    print(f"Parts: {inserted_parts}")
    print(f"Sections: {inserted_sections}")
    print(f"Subsections: {inserted_subsections}")
    print(f"Articles: {inserted_articles}")
    print(f"Updated: {updated_count}")

    # 7. HTML 테이블 개수 확인
    cursor.execute("""
        SELECT id,
               (LENGTH(content) - LENGTH(REPLACE(content, '<table', ''))) / 6 as table_count
        FROM nodes
        WHERE id LIKE '6.%' AND type = 'subsection'
        ORDER BY id
    """)
    print("\n=== Subsection별 <table> 개수 ===")
    total_tables = 0
    for row in cursor.fetchall():
        if row[1] > 0:
            print(f"  {row[0]}: {row[1]} tables")
            total_tables += row[1]
    print(f"\n총 테이블: {total_tables}개")

    # 8. FTS 인덱스 업데이트
    print("\n=== FTS 인덱스 업데이트 ===")
    cursor.execute("DELETE FROM search_index WHERE node_id LIKE '6.%'")
    cursor.execute("""
        INSERT INTO search_index (node_id, title, content)
        SELECT id, title, content FROM nodes WHERE id LIKE '6.%' AND content IS NOT NULL
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM search_index WHERE node_id LIKE '6.%'")
    print(f"Part 6 FTS 인덱스: {cursor.fetchone()[0]}개")

    # 9. 샘플 확인
    print("\n=== Article 샘플 ===")
    cursor.execute("""
        SELECT id, title FROM nodes
        WHERE type = 'article' AND id LIKE '6.%'
        ORDER BY id LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    conn.close()
    print(f"\nDB 임포트 완료: {DB_PATH}")


if __name__ == "__main__":
    import_part6()
