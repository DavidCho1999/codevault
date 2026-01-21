#!/usr/bin/env python3
"""
Part 6 파싱 이슈 수정 스크립트
- MD_LINK: [text](#page-xxx) → text
- ESCAPED_PAREN: \(4\) → (4)
- SEPARATED_SEE_NOTE: (See Note...) 별도 줄 → 이전 줄에 합치기
"""

import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "obc.db"


def fix_md_links(content: str) -> str:
    """마크다운 링크 제거: [text](#page-xxx) → text"""
    # [Sentence](#page-579-2) → Sentence
    # [Article 6.3.1.3.,](#page-579-3) → Article 6.3.1.3.,
    pattern = r'\[([^\]]+)\]\(#page-\d+[^)]*\)'
    return re.sub(pattern, r'\1', content)


def fix_escaped_parens(content: str) -> str:
    """이스케이프 괄호 제거"""
    # \( → (
    content = content.replace('\\(', '(')
    # \) → )
    content = content.replace('\\)', ')')
    return content


def fix_separated_see_note(content: str) -> str:
    """(See Note...) 별도 줄을 이전 줄에 합치기"""
    # 패턴: 줄끝 + 줄바꿈(1개 이상) + (See Note...)
    # 결과: 줄끝 + 공백 + (See Note...)
    pattern = r'(\S)\n+\s*(\(See\s+Note\s+[^)]+\))'
    content = re.sub(pattern, r'\1 \2', content, flags=re.IGNORECASE)

    # (See also ...) 패턴도 처리
    pattern2 = r'(\S)\n+\s*(\(See\s+also\s+[^)]+\))'
    content = re.sub(pattern2, r'\1 \2', content, flags=re.IGNORECASE)

    return content


def fix_part6():
    """Part 6 모든 노드 수정"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Part 6 노드들 가져오기
    cursor.execute("SELECT id, content FROM nodes WHERE id LIKE '6.%' AND content IS NOT NULL")
    rows = cursor.fetchall()

    fixed_count = 0

    for node_id, content in rows:
        if not content:
            continue

        original = content

        # 수정 적용
        content = fix_md_links(content)
        content = fix_escaped_parens(content)
        content = fix_separated_see_note(content)

        # 변경된 경우만 업데이트
        if content != original:
            cursor.execute("UPDATE nodes SET content = ? WHERE id = ?", (content, node_id))
            fixed_count += 1
            print(f"[FIXED] {node_id}")

    conn.commit()
    conn.close()

    print(f"\n총 {fixed_count}개 노드 수정됨")


if __name__ == '__main__':
    fix_part6()
