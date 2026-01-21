#!/usr/bin/env python3
"""
자동 스크리닝 스크립트
- PDF 원본과 DB content를 heuristic으로 비교
- "의심스러운" Article만 필터링하여 수동 확인 대상 추출
"""

import fitz
import sqlite3
import re
from pathlib import Path
from collections import defaultdict

# 설정
PDF_PATH = Path(__file__).parent.parent / "source/2024 Building Code Compendium/301880.pdf"
DB_PATH = Path(__file__).parent.parent / "data" / "obc.db"
PART9_START = 710  # 0-indexed

def get_db_articles():
    """DB에서 모든 Article 조회"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        SELECT id, title, content, page, type FROM nodes
        WHERE part = 9
          AND type IN ('article', 'article_suffix', 'article_0a', 'sub_article')
        ORDER BY id
    ''')
    articles = cur.fetchall()
    conn.close()
    return articles

def extract_pdf_text(page_num):
    """PDF 페이지에서 텍스트 추출 (0-indexed)"""
    doc = fitz.open(PDF_PATH)
    if page_num < len(doc):
        text = doc[page_num].get_text()
        doc.close()
        return text
    doc.close()
    return ""

def check_article(article_id, title, content, page, article_type):
    """단일 Article 검증 - 의심스러운 케이스 탐지"""
    issues = []

    # 1. Content 없음 (Reserved 아닌데)
    if not content and title and 'Reserved' not in title:
        issues.append("NO_CONTENT")

    if not content:
        return issues

    # 2. Content가 너무 짧음 (참조 아닌데)
    if len(content) < 30:
        if not re.search(r'See (Article|Section|Subsection|Note)', content):
            issues.append("VERY_SHORT")

    # 3. Clause 패턴 확인 - (1)로 시작해야 함
    if not content.strip().startswith('(1)'):
        # 예외: 짧은 참조 Article
        if len(content) > 50:
            issues.append("NO_CLAUSE_START")

    # 4. Clause 연속성 - (1) 다음에 (2)가 있으면 순서 확인
    clause_nums = re.findall(r'\((\d+)\)', content)
    if clause_nums:
        nums = [int(n) for n in clause_nums]
        # 중복 제거하고 순서 확인
        seen = []
        for n in nums:
            if n not in seen:
                seen.append(n)
        # (1)부터 시작하고 연속적이어야 함
        if seen and seen[0] != 1:
            issues.append("CLAUSE_NOT_START_1")
        # 큰 갭 확인 (1 다음에 5가 오면 의심)
        for i in range(1, len(seen)):
            if seen[i] - seen[i-1] > 2:
                issues.append(f"CLAUSE_GAP_{seen[i-1]}_to_{seen[i]}")
                break

    # 5. 잘린 문장 - 문장이 중간에 끝남
    if content and not content.rstrip().endswith(('.', ')', '"', ':')):
        last_word = content.rstrip().split()[-1] if content.split() else ""
        if len(last_word) > 2 and not last_word[-1].isdigit():
            issues.append("TRUNCATED_END")

    # 6. 수식 있는데 where 없음 (긴 content에서만)
    if len(content) > 200:
        has_formula = re.search(r'[A-Z][a-z]?\s*=\s*[A-Za-z0-9+\-*/()]+', content)
        has_where = 'where' in content.lower()
        if has_formula and not has_where:
            # formula 뒤에 설명이 없으면 의심
            issues.append("FORMULA_NO_WHERE")

    return issues

def screen_all():
    """전체 스크리닝 실행"""
    articles = get_db_articles()

    # 결과 저장
    suspicious = defaultdict(list)
    stats = defaultdict(int)

    print("=== 자동 스크리닝 시작 ===\n")

    for article_id, title, content, page, article_type in articles:
        issues = check_article(article_id, title, content, page, article_type)

        if issues:
            suspicious[article_id] = {
                'title': title,
                'page': page,
                'content_len': len(content) if content else 0,
                'issues': issues
            }
            for issue in issues:
                issue_type = issue.split('_')[0] if '_' in issue else issue
                stats[issue_type] += 1

    # 결과 출력
    print(f"총 Article 수: {len(articles)}")
    print(f"의심스러운 Article 수: {len(suspicious)}")
    print(f"통과율: {(len(articles) - len(suspicious)) / len(articles) * 100:.1f}%\n")

    print("=== 이슈 유형별 통계 ===")
    for issue_type, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {issue_type}: {count}")

    print("\n=== 의심스러운 Article 목록 ===")
    # 심각도 순으로 정렬 (이슈 개수)
    sorted_suspicious = sorted(suspicious.items(), key=lambda x: -len(x[1]['issues']))

    for article_id, info in sorted_suspicious[:30]:  # 상위 30개만
        issues_str = ", ".join(info['issues'])
        print(f"  {article_id:15} | p{info['page']:4} | {info['content_len']:5} chars | {issues_str}")

    if len(suspicious) > 30:
        print(f"  ... 그 외 {len(suspicious) - 30}개")

    # 상세 확인 필요 목록 저장
    output_path = Path(__file__).parent / "suspicious_articles.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 수동 확인 필요 Article 목록\n")
        f.write(f"# 생성일: auto_screen.py\n")
        f.write(f"# 총 {len(suspicious)}개\n\n")

        for article_id, info in sorted_suspicious:
            f.write(f"{article_id}\n")
            f.write(f"  Title: {info['title']}\n")
            f.write(f"  Page: {info['page']}\n")
            f.write(f"  Content Length: {info['content_len']}\n")
            f.write(f"  Issues: {', '.join(info['issues'])}\n\n")

    print(f"\n상세 목록 저장됨: {output_path}")

    return suspicious

def verify_sample(article_id):
    """단일 Article PDF 대조 확인"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT title, content, page FROM nodes WHERE id = ?', (article_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        print(f"Article {article_id} not found")
        return

    title, content, page = row

    print(f"=== {article_id} ===")
    print(f"Title: {title}")
    print(f"Page: {page}")
    print(f"Content ({len(content) if content else 0} chars):")
    print(content[:500] if content else "None")
    print("\n" + "="*50)
    print("PDF Text (same page):")

    pdf_text = extract_pdf_text(page - 1)  # 0-indexed
    # Article ID 주변 텍스트 찾기
    idx = pdf_text.find(article_id)
    if idx != -1:
        print(pdf_text[max(0, idx-50):idx+500])
    else:
        print(pdf_text[:500])

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # 특정 Article 검증
        verify_sample(sys.argv[1])
    else:
        # 전체 스크리닝
        screen_all()
