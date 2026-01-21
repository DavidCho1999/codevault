"""
Part 10, 11, 12의 Subsection content에서 [ARTICLE:...] 마커를 파싱하여
Article 노드를 DB에 추가하는 스크립트

마커 형식: [ARTICLE:11.1.1.1:Scope]
"""

import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "obc.db"


def parse_articles_from_content(subsection_id: str, content: str) -> list[dict]:
    """Subsection content에서 Article 파싱"""
    if not content:
        return []

    # 마커 패턴: [ARTICLE:ID:Title]
    pattern = r'\[ARTICLE:([^:]+):([^\]]*)\]'

    # 모든 마커 위치 찾기
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


def get_next_seq(conn: sqlite3.Connection) -> int:
    """다음 seq 값 가져오기"""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(seq) FROM nodes")
    result = cursor.fetchone()[0]
    return (result or 0) + 1


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Part 10, 11, 12의 subsection 조회
    cursor.execute("""
        SELECT id, content FROM nodes
        WHERE type IN ('subsection', 'alt_subsection')
        AND (id LIKE '10.%' OR id LIKE '11.%' OR id LIKE '12.%')
        AND content IS NOT NULL
    """)

    subsections = cursor.fetchall()
    print(f"처리할 Subsection: {len(subsections)}개")

    # 이미 존재하는 Article 확인
    cursor.execute("""
        SELECT id FROM nodes
        WHERE type = 'article'
        AND (id LIKE '10.%' OR id LIKE '11.%' OR id LIKE '12.%')
    """)
    existing_articles = set(row[0] for row in cursor.fetchall())
    print(f"기존 Article: {len(existing_articles)}개")

    seq = get_next_seq(conn)
    added = 0
    skipped = 0

    for subsection_id, content in subsections:
        articles = parse_articles_from_content(subsection_id, content)

        for article in articles:
            if article['id'] in existing_articles:
                skipped += 1
                continue

            # Part 번호 추출 (예: 11.1.1.1 → 11)
            part_num = int(article['id'].split('.')[0])

            # Article 노드 추가
            cursor.execute("""
                INSERT INTO nodes (id, type, part, parent_id, title, content, seq, page)
                VALUES (?, 'article', ?, ?, ?, ?, ?, NULL)
            """, (
                article['id'],
                part_num,
                article['parent_id'],
                article['title'],
                article['content'],
                seq
            ))

            seq += 1
            added += 1
            existing_articles.add(article['id'])

    conn.commit()
    print(f"\n=== 결과 ===")
    print(f"추가됨: {added}개")
    print(f"스킵 (이미 존재): {skipped}개")

    # 확인
    cursor.execute("""
        SELECT id, title FROM nodes
        WHERE type = 'article'
        AND (id LIKE '11.%')
        ORDER BY id
        LIMIT 10
    """)
    print(f"\n=== Part 11 Article 샘플 ===")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    conn.close()


if __name__ == "__main__":
    main()
