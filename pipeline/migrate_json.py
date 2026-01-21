"""
JSON → SQLite 마이그레이션 스크립트
현재 구조: Part → Section → Subsection (content 포함)
"""

import json
import sqlite3
import os

# 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, 'codevault', 'public', 'data', 'part9.json')
DB_PATH = os.path.join(BASE_DIR, 'data', 'obc.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'pipeline', 'schema.sql')


def migrate():
    # 1. JSON 로드
    print(f'Loading {JSON_PATH}...')
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. DB 초기화
    print(f'Initializing {DB_PATH}...')
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')

    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())

    # 3. Part 삽입
    part_id = str(data.get('id', '9'))
    part_title = data.get('title', 'Housing and Small Buildings')

    conn.execute('''
        INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
        VALUES (?, 'part', 9, NULL, ?, NULL, 711, 1)
    ''', (part_id, part_title))
    print(f'[+] Part: {part_id} - {part_title}')

    # 4. Sections 삽입
    sections = data.get('sections', [])
    section_count = 0
    subsection_count = 0
    article_count = 0

    for sec_seq, section in enumerate(sections, start=1):
        sec_id = section.get('id')
        sec_title = section.get('title', '')
        sec_page = section.get('page')

        conn.execute('''
            INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
            VALUES (?, 'section', 9, ?, ?, NULL, ?, ?)
        ''', (sec_id, part_id, sec_title, sec_page, sec_seq))
        section_count += 1

        # 5. Subsections 삽입
        subsections = section.get('subsections', [])
        for sub_seq, subsection in enumerate(subsections, start=1):
            sub_id = subsection.get('id')
            sub_title = subsection.get('title', '')
            sub_page = subsection.get('page')
            sub_content = subsection.get('content', '')

            # type 결정: Alternative Subsection 체크
            if sub_id and len(sub_id.split('.')) == 3:
                last_part = sub_id.split('.')[-1]
                if last_part and last_part[-1].isalpha() and last_part[:-1].isdigit():
                    sub_type = 'alt_subsection'
                else:
                    sub_type = 'subsection'
            else:
                sub_type = 'subsection'

            conn.execute('''
                INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
                VALUES (?, ?, 9, ?, ?, ?, ?, ?)
            ''', (sub_id, sub_type, sec_id, sub_title, sub_content, sub_page, sub_seq))
            subsection_count += 1

            # 6. Articles 삽입 (있으면)
            articles = subsection.get('articles', [])
            for art_seq, article in enumerate(articles, start=1):
                art_id = article.get('id')
                art_title = article.get('title', '')
                art_page = article.get('page')
                art_content = article.get('content', '')

                # type 결정
                art_type = get_article_type(art_id)

                conn.execute('''
                    INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
                    VALUES (?, ?, 9, ?, ?, ?, ?, ?)
                ''', (art_id, art_type, sub_id, art_title, art_content, art_page, art_seq))
                article_count += 1

    conn.commit()

    # 7. 결과 출력
    print(f'\n=== Migration Complete ===')
    print(f'Sections:    {section_count}')
    print(f'Subsections: {subsection_count}')
    print(f'Articles:    {article_count}')

    # 검증
    print(f'\n=== Verification ===')
    cursor = conn.execute('SELECT type, COUNT(*) FROM nodes GROUP BY type ORDER BY COUNT(*) DESC')
    for row in cursor:
        print(f'  {row[0]:16}: {row[1]}')

    # FTS 검증
    cursor = conn.execute('SELECT COUNT(*) FROM search_index')
    print(f'\nFTS5 index entries: {cursor.fetchone()[0]}')

    conn.close()
    print(f'\nDB saved: {DB_PATH}')


def get_article_type(art_id: str) -> str:
    """Article ID로 타입 결정"""
    if not art_id:
        return 'article'

    parts = art_id.split('.')
    if len(parts) < 4:
        return 'article'

    last = parts[-1]

    # 0A Article: 9.X.X.0A
    if last == '0A':
        return 'article_0a'

    # Sub-Article: 9.X.XA.1 (3번째가 숫자+문자, 4번째가 숫자)
    third = parts[2] if len(parts) > 2 else ''
    if third and third[-1].isalpha() and third[:-1].isdigit() and last.isdigit():
        return 'sub_article'

    # Article Suffix: 9.X.X.1A (마지막이 숫자+문자)
    if last and last[-1].isalpha() and last[:-1].isdigit():
        return 'article_suffix'

    return 'article'


if __name__ == '__main__':
    migrate()
