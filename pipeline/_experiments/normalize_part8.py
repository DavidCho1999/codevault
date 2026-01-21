"""
Part 8 DB 콘텐츠 정규화 스크립트

Part 8의 raw markdown 형식을 Part 9/11과 동일한 형식으로 변환:
- **8.x.x.x. Title** → [ARTICLE:8.x.x.x:Title]
- **(1)** → (1)
- *term* → term (이탤릭 제거)
- - (a) → (a) (리스트 마커 제거)
- ### Table → Table (마크다운 헤딩 제거)
"""

import sqlite3
import re
from pathlib import Path


def normalize_content(content: str) -> str:
    """Part 8 content를 Part 9/11 형식으로 정규화"""
    if not content:
        return content

    result = content

    # 1. 마크다운 헤딩 제거: ### Table 8.x.x.x → Table 8.x.x.x
    result = re.sub(r'^#{1,4}\s+', '', result, flags=re.MULTILINE)

    # 2. Article 헤더 변환: **8.x.x.x. Title** → [ARTICLE:8.x.x.x:Title]
    result = re.sub(
        r'\*\*(8\.\d+\.\d+\.\d+)\.\s*([^*]+)\*\*',
        r'[ARTICLE:\1:\2]',
        result
    )

    # 3. Bold clause 번호 제거: **(1)** → (1)
    result = re.sub(r'\*\*\((\d+)\)\*\*', r'(\1)', result)

    # 4. 이탤릭 제거: *term* → term
    # 주의: **bold** 패턴과 겹치지 않도록 단일 * 만 처리
    result = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'\1', result)

    # 5. 리스트 마커 제거: - (a) → (a), - (i) → (i), - (1) → (1)
    result = re.sub(r'^- \(([a-z])\)', r'(\1)', result, flags=re.MULTILINE)
    result = re.sub(r'^- \(([ivx]+)\)', r'(\1)', result, flags=re.MULTILINE)
    result = re.sub(r'^- \*\*\((\d+)\)\*\*', r'(\1)', result, flags=re.MULTILINE)
    result = re.sub(r'^- \((\d+)\)', r'(\1)', result, flags=re.MULTILINE)

    # 6. 들여쓰기된 sub-clause 정리: "  - (i)" → "  (i)"
    result = re.sub(r'^\s+- \(([ivx]+)\)', r'  (\1)', result, flags=re.MULTILINE)
    result = re.sub(r'^\s+- \(([a-z])\)', r'  (\1)', result, flags=re.MULTILINE)

    # 7. Article 제목 뒤 공백 정리
    result = re.sub(r'\[ARTICLE:([^:]+):([^\]]+)\s*\]', r'[ARTICLE:\1:\2]', result)

    return result


def normalize_part8_db(db_path: str):
    """Part 8 DB 콘텐츠 정규화"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Part 8 노드 조회
    cursor.execute('SELECT id, content FROM nodes WHERE id LIKE "8.%" AND content IS NOT NULL')
    rows = cursor.fetchall()

    print(f"Part 8 nodes: {len(rows)}")

    normalized_count = 0
    for node_id, content in rows:
        if not content:
            continue

        normalized = normalize_content(content)

        if content != normalized:
            cursor.execute('UPDATE nodes SET content = ? WHERE id = ?', (normalized, node_id))
            normalized_count += 1
            print(f"  [OK] {node_id} normalized")

    conn.commit()
    conn.close()

    print(f"\n총 {normalized_count}개 노드 정규화 완료")

    return normalized_count


def verify_normalization(db_path: str):
    """정규화 결과 검증"""
    print("\n=== 정규화 검증 ===")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT id, content FROM nodes WHERE id LIKE "8.%" AND content IS NOT NULL')
    rows = cursor.fetchall()

    issues = []

    for node_id, content in rows:
        if not content:
            continue

        # 남은 markdown 패턴 체크
        if re.search(r'^#{1,4}\s+', content, re.MULTILINE):
            issues.append(f"{node_id}: 마크다운 헤딩 남음")

        if re.search(r'\*\*8\.\d+\.\d+\.\d+\.', content):
            issues.append(f"{node_id}: Article 헤더 변환 안됨")

        if re.search(r'\*\*\(\d+\)\*\*', content):
            issues.append(f"{node_id}: Bold clause 번호 남음")

        # 이탤릭 체크 (단어 단위, 짧은 것만)
        if re.search(r'(?<!\*)\*[a-zA-Z]{2,20}\*(?!\*)', content):
            issues.append(f"{node_id}: 이탤릭 남음")

        if re.search(r'^- \([a-z]\)', content, re.MULTILINE):
            issues.append(f"{node_id}: 리스트 마커 (a) 남음")

        if re.search(r'^- \(\d+\)', content, re.MULTILINE):
            issues.append(f"{node_id}: 리스트 마커 (1) 남음")

    conn.close()

    if issues:
        print("[WARNING] Remaining issues:")
        for issue in issues[:20]:  # 최대 20개만 출력
            print(f"  - {issue}")
        if len(issues) > 20:
            print(f"  ... and {len(issues) - 20} more")
    else:
        print("[SUCCESS] All patterns normalized!")

    return len(issues) == 0


if __name__ == "__main__":
    db_path = Path(__file__).parent.parent / "obc.db"

    print(f"DB: {db_path}")
    print("\n정규화 시작...")

    normalize_part8_db(str(db_path))

    verify_normalization(str(db_path))

    # 샘플 출력
    print("\n=== 샘플 출력 (8.1.1) ===")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute('SELECT content FROM nodes WHERE id = "8.1.1"')
    row = cursor.fetchone()
    if row and row[0]:
        print(row[0][:500])
    conn.close()
