"""
Tables JSON → SQLite 마이그레이션 스크립트
part9_tables.json → obc.db tables 테이블
"""

import json
import sqlite3
import os
import re

# 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES_JSON = os.path.join(BASE_DIR, 'codevault', 'public', 'data', 'part9_tables.json')
DB_PATH = os.path.join(BASE_DIR, 'data', 'obc.db')


def get_parent_id(table_id: str) -> str:
    """테이블 ID에서 parent_id (Article ID) 추출

    예: "Table 9.5.3.1" → "9.5.3.1"
    예: "Table 9.6.1.3.-A" → "9.6.1.3"  (suffix 제거)
    예: "Table 9.10.17.5A" → "9.10.17.5A" (Article suffix 유지)
    """
    # "Table " 제거
    match = re.match(r'Table\s+([\d.]+[A-Z]?)', table_id)
    if match:
        return match.group(1)

    # 대시 포함 케이스 (9.6.1.3.-A → 9.6.1.3)
    match = re.match(r'Table\s+([\d.]+)\.-[A-Z]', table_id)
    if match:
        return match.group(1)

    return None


def migrate_tables():
    # 1. JSON 로드
    print(f'Loading {TABLES_JSON}...')
    with open(TABLES_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f'Total tables in JSON: {len(data)}')

    # 2. DB 연결
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')

    # 3. 기존 테이블 데이터 삭제
    conn.execute('DELETE FROM tables')
    print('Cleared existing tables data')

    # 4. 테이블 삽입
    inserted = 0
    skipped = 0
    no_parent = []

    for table_id, table_data in data.items():
        parent_id = get_parent_id(table_id)

        # parent_id가 nodes에 존재하는지 확인
        cursor = conn.execute('SELECT id FROM nodes WHERE id = ?', (parent_id,))
        parent_exists = cursor.fetchone() is not None

        # parent가 없으면 subsection 레벨로 시도
        if not parent_exists and parent_id:
            # 9.5.3.1 → 9.5.3 (subsection)
            parts = parent_id.split('.')
            if len(parts) >= 3:
                subsection_id = '.'.join(parts[:3])
                cursor = conn.execute('SELECT id FROM nodes WHERE id = ?', (subsection_id,))
                if cursor.fetchone():
                    parent_id = subsection_id
                    parent_exists = True

        title = table_data.get('title', table_id)
        page = table_data.get('page')
        html = table_data.get('html', '')
        source = table_data.get('source', 'unknown')

        try:
            conn.execute('''
                INSERT INTO tables (id, title, parent_id, page, html, source)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (table_id, title, parent_id, page, html, source))
            inserted += 1
        except sqlite3.IntegrityError as e:
            # FK 제약 실패 시 parent_id를 NULL로
            conn.execute('''
                INSERT INTO tables (id, title, parent_id, page, html, source)
                VALUES (?, ?, NULL, ?, ?, ?)
            ''', (table_id, title, page, html, source))
            no_parent.append((table_id, parent_id))
            inserted += 1

    conn.commit()

    # 5. 결과 출력
    print(f'\n=== Migration Complete ===')
    print(f'Inserted: {inserted}')
    print(f'Skipped:  {skipped}')

    if no_parent:
        print(f'\n=== Tables without parent node ({len(no_parent)}) ===')
        for tid, pid in no_parent[:10]:
            print(f'  {tid} → {pid} (not found)')
        if len(no_parent) > 10:
            print(f'  ... and {len(no_parent) - 10} more')

    # 6. 검증
    print(f'\n=== Verification ===')
    cursor = conn.execute('SELECT COUNT(*) FROM tables')
    print(f'Total tables in DB: {cursor.fetchone()[0]}')

    cursor = conn.execute('SELECT COUNT(*) FROM tables WHERE parent_id IS NOT NULL')
    print(f'With parent_id: {cursor.fetchone()[0]}')

    cursor = conn.execute('SELECT source, COUNT(*) FROM tables GROUP BY source')
    print('\nBy source:')
    for row in cursor:
        print(f'  {row[0]:20}: {row[1]}')

    conn.close()
    print(f'\nDone!')


if __name__ == '__main__':
    migrate_tables()
