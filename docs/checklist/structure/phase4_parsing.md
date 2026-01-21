# Phase 4: Part 9 전체 파싱

> 목표: Part 9 전체 PDF를 파싱하여 SQLite DB에 저장한다.

---

## ⚠️ 먼저 읽기

**`_checklist/OBC_STRUCTURE_RULES.md`를 먼저 읽으세요!**

이 문서의 코드는 **4단계 + 변형** 구조를 기반으로 합니다:
- Alternative Subsection (9.5.3A)
- Article Suffix (9.5.1.1A)
- 0A Article (9.33.6.10A)
- Sub-Article (9.5.3A.1)

---

## 이 단계에서 배울 것

1. PyMuPDF로 PDF 텍스트 추출하는 방법
2. 텍스트 정렬 문제와 해결법
3. 전체 파싱 파이프라인 (특수 패턴 포함)
4. SQLite에 데이터 저장하는 방법
5. 파싱 결과 검증 방법

---

## 1. PDF 텍스트 추출

### PyMuPDF (fitz) 기본 사용법

```python
import fitz  # PyMuPDF

# PDF 열기
doc = fitz.open("source/2024 Building Code Compendium/301880.pdf")

# 페이지 수
print(f"총 페이지: {len(doc)}")

# 특정 페이지 텍스트 추출
page = doc[714]  # 0-indexed, Part 9 시작 부근
text = page.get_text()
print(text)
```

### 텍스트 순서 문제

**문제:** `get_text()`가 PDF 내부 순서대로 반환 → 시각적 순서와 다를 수 있음

```python
# 잘못된 순서 예시
"9.5.3.1.  Title"
"9.5.3.3.  Another Title"  # 9.5.3.2보다 먼저 나옴!
"9.5.3.2.  Missing Title"
```

### 해결: 좌표 기반 정렬

```python
def extract_text_sorted(page) -> str:
    """페이지 텍스트를 y좌표 → x좌표 순으로 정렬"""
    blocks = page.get_text("blocks")
    # blocks = [(x0, y0, x1, y1, text, block_no, block_type), ...]

    # y좌표(위→아래), x좌표(왼→오른) 순 정렬
    sorted_blocks = sorted(blocks, key=lambda b: (b[1], b[0]))

    # 텍스트만 추출
    lines = []
    for block in sorted_blocks:
        text = block[4].strip()
        if text:
            lines.append(text)

    return '\n'.join(lines)
```

---

## 2. Part 9 페이지 범위

### PDF 구조 (301880.pdf)

```
페이지 711-1034: Part 9 - Housing and Small Buildings
  - 711-714: 9.1 General
  - 715-720: 9.2 Definitions
  - ...
  - 1030-1034: 9.41 Additional Requirements
```

### 범위 설정

```python
PART9_START = 710  # 0-indexed
PART9_END = 1034   # exclusive
```

---

## 3. 전체 파싱 파이프라인

### parse_part9.py

```python
#!/usr/bin/env python3
"""
Part 9 전체 PDF를 파싱하여 SQLite DB에 저장
- 4단계 + 변형 구조 지원
- Alternative Subsection, Article Suffix, 0A Article, Sub-Article 처리
"""

import fitz
import sqlite3
import re
from pathlib import Path
from tree_builder import TreeBuilder
from patterns import detect_type, PATTERNS

# === 설정 ===
PDF_PATH = Path("source/2024 Building Code Compendium/301880.pdf")
DB_PATH = Path("obc.db")
PART9_START = 710  # 0-indexed
PART9_END = 1034


def extract_text_sorted(page) -> str:
    """페이지 텍스트를 좌표 순으로 정렬하여 추출"""
    blocks = page.get_text("blocks")
    sorted_blocks = sorted(blocks, key=lambda b: (b[1], b[0]))

    lines = []
    for block in sorted_blocks:
        if block[6] == 0:  # 텍스트 블록만 (이미지 제외)
            text = block[4].strip()
            if text:
                lines.append(text)

    return '\n'.join(lines)


def clean_text(text: str) -> str:
    """텍스트 정리"""
    # 페이지 번호 제거
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)

    # 헤더/푸터 제거
    text = re.sub(r'^.*Building Code.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^.*Division [ABC].*$', '', text, flags=re.MULTILINE)

    # 연속 빈 줄 정리
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def parse_page(builder: TreeBuilder, text: str, page_num: int):
    """한 페이지 파싱 (특수 패턴 포함)"""
    lines = text.split('\n')
    current_content = []
    current_type = None
    current_data = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        result = detect_type(line)

        if result:
            # 이전에 쌓인 content 처리
            if current_type == 'clause' and current_content:
                full_content = ' '.join(current_content)
                parent = builder.context_stack[-1] if builder.context_stack else None
                if parent and '(' not in parent:  # Article 아래
                    clause_id = f"{parent}.({current_data['num']})"
                    builder.add_node('clause', clause_id, content=full_content, page=page_num)
                current_content = []

            node_type, data = result
            current_type = node_type
            current_data = data

            # === 기본 타입 ===
            if node_type == 'section':
                builder.add_node('section', data['id'], title=data['title'], page=page_num)

            elif node_type == 'subsection':
                builder.add_node('subsection', data['id'], title=data['title'], page=page_num)

            elif node_type == 'article':
                builder.add_node('article', data['id'], title=data['title'], page=page_num)

            # === 특수 타입 (중요!) ===
            elif node_type == 'alt_subsection':
                # 9.5.3A → parent는 9.5 (Section)
                builder.add_node('alt_subsection', data['id'], title=data['title'], page=page_num)

            elif node_type == 'article_suffix':
                # 9.5.1.1A → parent는 9.5.1 (Subsection)
                builder.add_node('article_suffix', data['id'], title=data['title'], page=page_num)

            elif node_type == 'article_0a':
                # 9.33.6.10A → parent는 해당 Subsection
                builder.add_node('article_0a', data['id'], title=data['title'], page=page_num)

            elif node_type == 'sub_article':
                # 9.5.3A.1 → parent는 9.5.3A (Alt Subsection)
                builder.add_node('sub_article', data['id'], title=data['title'], page=page_num)

            # === Clause 레벨 ===
            elif node_type == 'clause':
                current_content = [data['content']]

            elif node_type in ('subclause', 'subsubclause'):
                # Subclause/Subsubclause 처리
                pass

        else:
            # 이전 Clause의 연속
            if current_type == 'clause':
                current_content.append(line)

    # 마지막 content 처리
    if current_type == 'clause' and current_content:
        full_content = ' '.join(current_content)
        parent = builder.context_stack[-1] if builder.context_stack else None
        if parent and '(' not in parent:
            clause_id = f"{parent}.({current_data['num']})"
            builder.add_node('clause', clause_id, content=full_content, page=page_num)


def save_to_db(builder: TreeBuilder, db_path: Path):
    """트리를 SQLite에 저장"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 기존 데이터 삭제
    cursor.execute("DELETE FROM nodes WHERE part = 9")
    cursor.execute("DELETE FROM refs WHERE source_id LIKE '9.%'")

    # nodes 저장
    for node_id, node in builder.to_dict().items():
        cursor.execute('''
            INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            node['id'],
            node['type'],
            node['part'],
            node['parent_id'],
            node['title'],
            node['content'],
            node['page'],
            node['seq']
        ))

        # refs 저장
        refs = node.get('refs', {})
        for ref_type, ref_list in refs.items():
            for ref in ref_list:
                target_type = ref_type.rstrip('s')  # 'tables' -> 'table'
                cursor.execute('''
                    INSERT INTO refs (source_id, target_id, target_type)
                    VALUES (?, ?, ?)
                ''', (node_id, ref, target_type))

    # 검색 인덱스 업데이트
    cursor.execute("DELETE FROM search_index WHERE node_id LIKE '9.%'")
    cursor.execute('''
        INSERT INTO search_index (node_id, title, content)
        SELECT id, title, content FROM nodes
        WHERE part = 9 AND (title IS NOT NULL OR content IS NOT NULL)
    ''')

    conn.commit()
    conn.close()
    print(f"[OK] Saved to {db_path}")


def main():
    print("=== Part 9 PDF 파싱 시작 ===\n")

    # PDF 열기
    doc = fitz.open(PDF_PATH)
    print(f"PDF loaded: {PDF_PATH}")
    print(f"Total pages: {len(doc)}")
    print(f"Part 9 range: {PART9_START + 1} - {PART9_END}\n")

    # TreeBuilder 초기화
    builder = TreeBuilder(part_num=9)

    # Part 노드 추가
    builder.add_node('part', '9', title='Housing and Small Buildings', page=PART9_START + 1)

    # Section 노드들 추가 (TOC에서 가져오거나 하드코딩)
    # 간단히 하드코딩 예시
    sections = [
        ('9.1', 'General'),
        ('9.2', 'Definitions'),
        ('9.3', 'Materials, Systems and Equipment'),
        ('9.4', 'Structural Requirements'),
        ('9.5', 'Design of Areas, Spaces and Doorways'),
        # ... 나머지 섹션들
    ]
    for sec_id, sec_title in sections:
        builder.add_node('section', sec_id, title=sec_title)

    # 페이지별 파싱
    for page_idx in range(PART9_START, PART9_END):
        page = doc[page_idx]
        text = extract_text_sorted(page)
        text = clean_text(text)

        if text:
            parse_page(builder, text, page_idx + 1)

        # 진행률 표시
        if (page_idx - PART9_START) % 50 == 0:
            print(f"  Processed page {page_idx + 1}...")

    doc.close()

    # 결과 출력
    nodes = builder.to_dict()
    print(f"\n=== 파싱 결과 ===")
    print(f"Total nodes: {len(nodes)}")

    # 타입별 개수
    type_counts = {}
    for node in nodes.values():
        t = node['type']
        type_counts[t] = type_counts.get(t, 0) + 1

    for t, count in sorted(type_counts.items()):
        print(f"  {t}: {count}")

    # DB 저장
    save_to_db(builder, DB_PATH)

    print("\n=== 완료 ===")


if __name__ == '__main__':
    main()
```

---

## 4. 실행 및 검증

### 실행

```bash
cd scripts
python parse_part9.py
```

예상 출력:
```
=== Part 9 PDF 파싱 시작 ===

PDF loaded: source/2024 Building Code Compendium/301880.pdf
Total pages: 1260
Part 9 range: 711 - 1034

  Processed page 711...
  Processed page 761...
  Processed page 811...
  ...

=== 파싱 결과 ===
Total nodes: ~3000
  part: 1
  section: ~41
  subsection: ~274
  alt_subsection: 6
  article: ~1081
  article_suffix: ~12
  article_0a: 1
  sub_article: ~22
  clause: ~2000+

[OK] Saved to obc.db

=== 완료 ===
```

### 검증 쿼리

```bash
sqlite3 obc.db
```

```sql
-- 타입별 개수
SELECT type, COUNT(*) as count
FROM nodes
WHERE part = 9
GROUP BY type
ORDER BY count DESC;

-- 예상 결과 (4단계 + 변형):
-- clause          | 2000+
-- article         | 1000+
-- subsection      | 270+
-- section         | 41
-- sub_article     | 22
-- article_suffix  | 12
-- alt_subsection  | 6
-- article_0a      | 1
-- part            | 1

-- 특정 Article 확인
SELECT id, content
FROM nodes
WHERE parent_id = '9.5.3.1'
ORDER BY seq;

-- 테이블 참조 확인
SELECT source_id, target_id
FROM refs
WHERE target_type = 'table'
LIMIT 10;

-- 검색 테스트
SELECT node_id, snippet(search_index, 2, '[', ']', '...', 20)
FROM search_index
WHERE search_index MATCH 'ceiling height'
LIMIT 5;
```

---

## 5. 특수 패턴 검증 (중요!)

### Alternative Subsection 검증

```sql
-- 9.5.3A-F가 9.5의 자식인지 확인 (9.5.3의 자식이면 틀린 것!)
SELECT id, parent_id, title
FROM nodes
WHERE type = 'alt_subsection';

-- 예상:
-- 9.5.3A | 9.5 | Living Rooms...    ← parent가 9.5여야 함!
-- 9.5.3B | 9.5 | Dining Rooms...
-- 9.5.3C | 9.5 | Kitchens
-- 9.5.3D | 9.5 | Bedrooms
-- 9.5.3E | 9.5 | Combined Spaces
-- 9.5.3F | 9.5 | Bathrooms
```

### Article Suffix 검증

```sql
-- 9.5.1.1A가 9.5.1의 자식인지 확인
SELECT id, parent_id, title
FROM nodes
WHERE type = 'article_suffix';

-- 예상:
-- 9.5.1.1A | 9.5.1 | Floor Areas
-- 9.10.14.3A | 9.10.14 | Inadequate Firefighting...
```

### Sub-Article 검증

```sql
-- 9.5.3A.1이 9.5.3A의 자식인지 확인
SELECT id, parent_id, title
FROM nodes
WHERE type = 'sub_article';

-- 예상:
-- 9.5.3A.1 | 9.5.3A | Areas of Living Rooms
-- 9.5.3D.1 | 9.5.3D | Areas of Bedrooms
-- ...
```

---

## 6. 검증 체크리스트

### 수량 검증

| 항목 | 예상 범위 | 실제 |
|------|----------|------|
| section | 40-42 | |
| subsection | 270-280 | |
| **alt_subsection** | 6 | |
| article | 1000-1100 | |
| **article_suffix** | 10-15 | |
| **article_0a** | 1 | |
| **sub_article** | 20-25 | |
| clause | 2000-2500 | |

### 샘플 검증

```sql
-- 9.5.3.1의 구조가 맞는지
SELECT id, type, seq FROM nodes
WHERE id LIKE '9.5.3.1%'
ORDER BY id;

-- 예상:
-- 9.5.3.1 | article | 1
-- 9.5.3.1.(1) | clause | 1
-- 9.5.3.1.(2) | clause | 2
-- 9.5.3.1.(3) | clause | 3
-- 9.5.3.1.(4) | clause | 4
```

### 참조 검증

```sql
-- 9.5.3.1.(1)의 참조
SELECT * FROM refs WHERE source_id = '9.5.3.1.(1)';

-- 예상:
-- 9.5.3.1.(1) | 9.5.3.1.(2) | clause
-- 9.5.3.1.(1) | 9.5.3.1.(3) | clause
-- 9.5.3.1.(1) | Table 9.5.3.1 | table
```

### ⚠️ 특수 패턴 필수 검증

```sql
-- 1. Alternative Subsection parent 확인
SELECT COUNT(*) FROM nodes
WHERE type = 'alt_subsection'
  AND parent_id LIKE '%.%' AND parent_id NOT LIKE '%.%.%';
-- 예상: 6 (모두 Section 아래)

-- 2. Sub-Article parent 확인
SELECT COUNT(*) FROM nodes
WHERE type = 'sub_article'
  AND parent_id LIKE '%.%.%[A-Z]';
-- 예상: ~22 (모두 Alt Subsection 아래)

-- 3. 잘못된 parent 없는지 확인
SELECT id, parent_id FROM nodes
WHERE type = 'alt_subsection'
  AND parent_id LIKE '%.%.%';
-- 예상: 결과 0개 (있으면 버그!)
```

---

## 7. 문제 해결

### 흔한 문제들

| 문제 | 증상 | 해결 |
|------|------|------|
| 텍스트 순서 뒤섞임 | Article 번호가 순서대로 안 나옴 | y좌표 정렬 확인 |
| Clause 잘림 | 내용이 중간에 끊김 | 여러 줄 연결 로직 |
| 참조 못 찾음 | refs 테이블이 비어있음 | 정규식 패턴 확인 |
| 중복 노드 | 같은 ID가 여러 번 | ID 생성 로직 확인 |
| Alt Subsection parent 틀림 | 9.5.3A parent가 9.5.3 | TreeBuilder 로직 수정 |

### 디버깅 팁

```python
# 특정 페이지만 파싱해서 확인
page = doc[714]
text = extract_text_sorted(page)
print(text)

# 특정 줄 감지 테스트
from patterns import detect_type
result = detect_type("9.5.3A.  Living Rooms")
print(result)  # 예상: ('alt_subsection', {'id': '9.5.3A', ...})

# 특수 패턴 감지 테스트
test_lines = [
    "9.5.3A.  Living Rooms",           # alt_subsection
    "9.5.3A.1.  Areas of Living Rooms", # sub_article
    "9.5.1.1A.  Floor Areas",           # article_suffix
    "9.33.6.10A.  Application",         # article_0a (희귀)
]
for line in test_lines:
    result = detect_type(line)
    print(f"{line[:30]:30} → {result}")
```

---

## 체크리스트

- [ ] `OBC_STRUCTURE_RULES.md` 읽음
- [ ] PyMuPDF로 텍스트 추출 이해함
- [ ] 좌표 기반 정렬 이해함
- [ ] parse_part9.py 작성함 (특수 패턴 포함)
- [ ] 파싱 실행 완료
- [ ] 수량 검증 통과
- [ ] 샘플 검증 통과
- [ ] 참조 검증 통과
- [ ] **특수 패턴 검증 통과** (alt_subsection, article_suffix, sub_article)

---

## 다음 단계

Phase 4 완료 후 → [Phase 5: Next.js 연동](./phase5_nextjs.md)

Phase 5에서는 SQLite 데이터를 웹에서 표시합니다.
