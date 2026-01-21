# Phase 1: 스키마 설계

> 목표: OBC 문서의 계층 구조를 이해하고, SQLite 스키마로 표현한다.

---

## ⚠️ 먼저 읽기

**`_checklist/OBC_STRUCTURE_RULES.md`를 먼저 읽으세요!**

이전에 작성된 "6단계 계층"은 틀렸습니다. 실제는 **4단계 + 변형**입니다.

---

## 이 단계에서 배울 것

1. OBC 문서의 **실제** 계층 구조
2. 각 레벨(Section, Subsection, Article...)의 특징
3. **특수 패턴** (Alternative Subsection, Article Suffix, 0A Article)
4. SQLite로 이 구조를 어떻게 표현하는지

---

## 1. OBC 문서 실제 계층 구조

### 4단계 + 변형 (6단계 아님!)

```
Part 9                                      ← Level 0: 최상위
│
├── Section 9.5                             ← Level 1: 대분류
│   │
│   ├── Subsection 9.5.1 General            ← Level 2: 중분류
│   │   ├── Article 9.5.1.0A Application    ← 특수: 0A (먼저 나옴!)
│   │   ├── Article 9.5.1.1 Method of...    ← Level 3: 조항
│   │   │   ├── (1) Except as...            ← Level 4: Clause
│   │   │   │   ├── (a) where...            ← Sub-clause
│   │   │   │   └── (b) where...
│   │   │   └── (2) Ceiling heights...
│   │   └── Article 9.5.1.1A Floor Areas    ← 특수: A Suffix
│   │
│   ├── Subsection 9.5.3 Ceiling Heights    ← 일반 Subsection
│   │   ├── Article 9.5.3.1
│   │   ├── Article 9.5.3.2
│   │   └── Article 9.5.3.3
│   │
│   ├── Subsection 9.5.3A Living Rooms      ← 특수: Alternative (9.5.3의 형제!)
│   │   └── Sub-Article 9.5.3A.1
│   │
│   ├── Subsection 9.5.3B Dining Rooms      ← 특수: Alternative
│   │   └── Sub-Article 9.5.3B.1
│   │
│   ├── Subsection 9.5.3C Kitchens
│   ├── Subsection 9.5.3D Bedrooms
│   │   ├── Sub-Article 9.5.3D.1
│   │   ├── Sub-Article 9.5.3D.2
│   │   └── ... (9.5.3D.6까지)
│   │
│   ├── Subsection 9.5.3E Combined Spaces
│   └── Subsection 9.5.3F Bathrooms
```

### 핵심 포인트

1. **"Sentence" 아님** → 올바른 용어는 **"Clause"**
2. **9.5.3A는 9.5.3의 형제**이지 자식이 아님!
3. **0A Article** (9.5.1.0A)은 일반 Article보다 **먼저** 나옴
4. **Article + Suffix** (9.5.1.1A, 9.33.6.10A)는 기본 Article 바로 **뒤에** 나옴

---

## 2. 각 레벨의 특징

| 레벨 | 타입 | ID 패턴 | 제목 유무 | 내용 유무 | 예시 |
|------|------|---------|----------|----------|------|
| 0 | part | `9` | O | X | Part 9 - Housing and Small Buildings |
| 1 | section | `9.5` | O | X | Design of Areas, Spaces and Doorways |
| 2 | subsection | `9.5.3` | O | X | Ceiling Heights |
| 2 | **alt_subsection** | `9.5.3A` | O | X | Living Rooms (9.5.3의 **형제**) |
| 3 | article | `9.5.3.1` | O | X | Ceiling Heights of Rooms or Spaces |
| 3 | **article_suffix** | `9.5.1.1A` | O | X | Floor Areas (9.5.1.1 **뒤에**) |
| 3 | **article_0a** | `9.5.1.0A` | O | X | Application (9.5.1.1보다 **먼저**) |
| 3 | **sub_article** | `9.5.3A.1` | O | X | Areas of Living Rooms |
| 4 | clause | `(1)`, `(2)` | X | O | "Except as provided in..." |
| 5 | subclause | `(a)`, `(b)` | X | O | "where one or more..." |
| 6 | subsubclause | `(i)`, `(ii)` | X | O | "the width of..." |

**핵심:**
- Part ~ Article: 제목만 있고 내용 없음 (컨테이너 역할)
- Clause 이하: 실제 텍스트 내용이 있음

---

## 3. ID 패턴 상세

### 정규식으로 표현

```python
ID_PATTERNS = {
    # 기본 패턴
    'part':           r'^9$',
    'section':        r'^9\.(\d+)$',                    # 9.5
    'subsection':     r'^9\.(\d+)\.(\d+)$',             # 9.5.3
    'article':        r'^9\.(\d+)\.(\d+)\.(\d+)$',      # 9.5.3.1

    # 특수 패턴 (중요!)
    'alt_subsection': r'^9\.(\d+)\.(\d+)([A-Z])$',      # 9.5.3A
    'article_suffix': r'^9\.(\d+)\.(\d+)\.(\d+)([A-Z])$',  # 9.5.1.1A, 9.33.6.10A
    'article_0a':     r'^9\.(\d+)\.(\d+)\.0A$',         # 9.5.1.0A (진짜 0A만!)
    'sub_article':    r'^9\.(\d+)\.(\d+)([A-Z])\.(\d+)$',  # 9.5.3A.1
}
```

### ⚠️ 0A Article vs Article Suffix 구분

| 패턴 | ID 예시 | 의미 | 순서 |
|------|---------|------|------|
| **article_0a** | `9.5.1.0A` | Subsection의 첫 번째 Article | 9.5.1.1보다 **먼저** |
| **article_suffix** | `9.5.1.1A` | 기본 Article의 확장/대안 | 9.5.1.1 **바로 뒤** |
| **article_suffix** | `9.33.6.10A` | Article 10의 확장 (10+A) | 9.33.6.10 **바로 뒤** |

**핵심**:
- `0A`는 Article 번호가 "0A"인 특수 케이스 (가장 먼저 옴)
- `10A`는 Article 번호 "10" + Suffix "A" (10 뒤에 옴)

### ID에서 타입 판단하기

```python
import re

def get_node_type(node_id: str) -> str:
    """ID로 노드 타입 판단 (특수 패턴 포함)"""

    # 특수 패턴 먼저 체크 (더 구체적인 것부터)
    if re.match(r'^9\.\d+\.\d+[A-Z]\.\d+$', node_id):
        return 'sub_article'        # 9.5.3A.1

    if re.match(r'^9\.\d+\.\d+\.0A$', node_id):
        return 'article_0a'         # 9.5.1.0A (진짜 0A)

    if re.match(r'^9\.\d+\.\d+\.\d+[A-Z]$', node_id):
        return 'article_suffix'     # 9.5.1.1A

    if re.match(r'^9\.\d+\.\d+[A-Z]$', node_id):
        return 'alt_subsection'     # 9.5.3A

    # 기본 패턴
    if re.match(r'^9\.\d+\.\d+\.\d+$', node_id):
        return 'article'            # 9.5.3.1

    if re.match(r'^9\.\d+\.\d+$', node_id):
        return 'subsection'         # 9.5.3

    if re.match(r'^9\.\d+$', node_id):
        return 'section'            # 9.5

    if node_id == '9':
        return 'part'

    # Clause 패턴 (Article ID + Clause 번호)
    if re.match(r'^9\.\d+\.\d+\.\d+\.\(\d+\)$', node_id):
        return 'clause'             # 9.5.3.1.(1)

    if re.match(r'^9\.\d+\.\d+\.\d+\.\(\d+\)\([a-z]\)$', node_id):
        return 'subclause'          # 9.5.3.1.(1)(a)

    if re.match(r'^9\.\d+\.\d+\.\d+\.\(\d+\)\([a-z]\)\([ivx]+\)$', node_id):
        return 'subsubclause'       # 9.5.3.1.(1)(a)(i)

    return 'unknown'
```

---

## 4. SQLite 스키마

### nodes 테이블 (핵심)

```sql
CREATE TABLE nodes (
    -- 기본 정보
    id TEXT PRIMARY KEY,        -- "9.5.3.1" 또는 "9.5.3A" 또는 "9.5.3A.1"
    type TEXT NOT NULL,         -- 아래 타입 목록 참조
    part INTEGER NOT NULL,      -- 9 (Part 번호)

    -- 계층 관계
    parent_id TEXT,             -- 부모 노드 ID

    -- 컨텐츠
    title TEXT,                 -- "Ceiling Heights" (Article 이상만)
    content TEXT,               -- 실제 텍스트 (Clause 이하만)

    -- 메타데이터
    page INTEGER,               -- PDF 페이지 번호
    seq INTEGER,                -- 형제 노드 중 순서 (1, 2, 3...)

    -- 외래키
    FOREIGN KEY (parent_id) REFERENCES nodes(id)
);

-- type 컬럼 가능 값:
-- 'part'           : 9
-- 'section'        : 9.X
-- 'subsection'     : 9.X.X
-- 'alt_subsection' : 9.X.X[A-Z]  (Alternative Subsection)
-- 'article'        : 9.X.X.X
-- 'article_suffix' : 9.X.X.X[A-Z]  (예: 9.5.1.1A, 9.33.6.10A)
-- 'article_0a'     : 9.X.X.0A      (예: 9.5.1.0A - 진짜 0A만!)
-- 'sub_article'    : 9.X.X[A-Z].X
-- 'clause'         : Article 내의 (1), (2)...
-- 'subclause'      : Clause 내의 (a), (b)...
-- 'subsubclause'   : Sub-clause 내의 (i), (ii)...
```

### ⚠️ seq 정렬 규칙

형제 노드 간 정렬 시 `seq` 컬럼 사용:

```
9.5의 자식들 (parent_id = '9.5'):
───────────────────────────────────
9.5.1   | seq=1 | subsection
9.5.2   | seq=2 | subsection
9.5.3   | seq=3 | subsection
9.5.3A  | seq=4 | alt_subsection  ← 9.5.3 뒤, 9.5.4 앞
9.5.3B  | seq=5 | alt_subsection
9.5.3C  | seq=6 | alt_subsection
9.5.3D  | seq=7 | alt_subsection
9.5.3E  | seq=8 | alt_subsection
9.5.3F  | seq=9 | alt_subsection
9.5.4   | seq=10 | subsection      ← 9.5.3F 다음
```

**규칙**: PDF 등장 순서대로 seq 할당 (1부터 연속 정수)

### tables 테이블

```sql
CREATE TABLE tables (
    id TEXT PRIMARY KEY,        -- "Table 9.5.3.1"
    title TEXT,                 -- "Room Ceiling Heights"
    parent_id TEXT,             -- "9.5.3.1" - 참조하는 article
    page INTEGER,               -- PDF 페이지 번호
    html TEXT,                  -- 렌더링용 HTML (나중에 채움)
    source TEXT,                -- "manual" | "camelot"

    FOREIGN KEY (parent_id) REFERENCES nodes(id)
);
```

#### ⚠️ 테이블 ID → parent_id 연결 규칙

테이블 ID에서 parent_id를 **자동 추출**할 수 있습니다:

```
Table 9.5.3.1     → parent_id = "9.5.3.1"    (Article)
Table 9.10.17.5   → parent_id = "9.10.17.5"  (Article)
Table 9.10.17.5A  → parent_id = "9.10.17.5A" (Article + Suffix 포함!)
Table 9.25.1.2    → parent_id = "9.25.1.2"   (Article)
```

**규칙**: `Table X.X.X.X[A-Z]?` → `parent_id = X.X.X.X[A-Z]?`

```python
import re

def get_table_parent_id(table_id: str) -> str:
    """테이블 ID에서 parent_id (Article ID) 추출

    예: "Table 9.5.3.1" → "9.5.3.1"
    예: "Table 9.10.17.5A" → "9.10.17.5A"  (Suffix 포함!)
    """
    match = re.match(r'Table\s+(9\.\d+\.\d+\.\d+[A-Z]?)', table_id)
    if match:
        return match.group(1)
    return None
```

#### 테이블 워크플로우 (2단계)

```
1단계: Structure (지금)
───────────────────────
- tables 테이블 스키마 정의 ✅
- parent_id 연결 규칙 정의 ✅
- html 컬럼은 비워둠 (NULL)

2단계: Content (나중에)
───────────────────────
- Camelot으로 1차 추출
- 수동 검증/수정 (merge, 누락 셀)
- html 컬럼에 저장
```

**핵심**: 구조(연결)와 내용(HTML)을 분리해서 관리

### refs 테이블 (Cross-reference)

```sql
CREATE TABLE refs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,    -- "9.5.3.1" - 참조하는 노드
    target_id TEXT NOT NULL,    -- "9.5.3.2" or "Table 9.5.3.1"
    target_type TEXT,           -- "clause", "table", "article"

    FOREIGN KEY (source_id) REFERENCES nodes(id)
);
```

### search_index (전문 검색)

```sql
CREATE VIRTUAL TABLE search_index USING fts5(
    node_id,
    title,
    content,
    tokenize='porter unicode61'
);

-- 동기화 트리거 (nodes 변경 시 자동 업데이트)
CREATE TRIGGER nodes_insert AFTER INSERT ON nodes BEGIN
    INSERT INTO search_index(node_id, title, content)
    VALUES (new.id, new.title, new.content);
END;

CREATE TRIGGER nodes_update AFTER UPDATE ON nodes BEGIN
    UPDATE search_index
    SET title = new.title, content = new.content
    WHERE node_id = new.id;
END;

CREATE TRIGGER nodes_delete AFTER DELETE ON nodes BEGIN
    DELETE FROM search_index WHERE node_id = old.id;
END;
```

### 인덱스

```sql
CREATE INDEX idx_nodes_parent ON nodes(parent_id);
CREATE INDEX idx_nodes_type ON nodes(type);
CREATE INDEX idx_nodes_part ON nodes(part);
CREATE INDEX idx_tables_parent ON tables(parent_id);
CREATE INDEX idx_refs_source ON refs(source_id);
CREATE INDEX idx_refs_target ON refs(target_id);
```

---

## 5. 예시 데이터

### 일반 구조

```sql
-- Part
INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
VALUES ('9', 'part', 9, NULL, 'Housing and Small Buildings', NULL, 711, 1);

-- Section
INSERT INTO nodes VALUES
('9.5', 'section', 9, '9', 'Design of Areas, Spaces and Doorways', NULL, 750, 5);

-- Subsection
INSERT INTO nodes VALUES
('9.5.1', 'subsection', 9, '9.5', 'General', NULL, 750, 1);

-- Article
INSERT INTO nodes VALUES
('9.5.1.1', 'article', 9, '9.5.1', 'Method of Measurement', NULL, 750, 2);
```

### 특수 패턴 예시

```sql
-- 0A Article (일반 Article보다 먼저!)
INSERT INTO nodes VALUES
('9.5.1.0A', 'article_0a', 9, '9.5.1', 'Application', NULL, 750, 1);

-- Article + Suffix (기본 Article 바로 뒤)
INSERT INTO nodes VALUES
('9.5.1.1A', 'article_suffix', 9, '9.5.1', 'Floor Areas', NULL, 750, 3);

-- Alternative Subsection (9.5.3의 형제로!)
INSERT INTO nodes VALUES
('9.5.3A', 'alt_subsection', 9, '9.5', 'Living Rooms or Spaces Within Dwelling Units', NULL, 752, 4);

-- Sub-Article (Alternative Subsection의 자식)
INSERT INTO nodes VALUES
('9.5.3A.1', 'sub_article', 9, '9.5.3A', 'Areas of Living Rooms', NULL, 752, 1);
```

### Clause 예시

```sql
-- Clause (Article의 자식)
INSERT INTO nodes VALUES
('9.5.3.1.(1)', 'clause', 9, '9.5.3.1', NULL,
 'Except as provided in Sentence (2), the minimum height of ceilings shall conform to Table 9.5.3.1.',
 752, 1);

INSERT INTO nodes VALUES
('9.5.3.1.(2)', 'clause', 9, '9.5.3.1', NULL,
 'Ceiling heights shall be reduced by the thickness of any flooring to be installed over the structural floor.',
 752, 2);

-- Sub-clause (Clause의 자식)
INSERT INTO nodes VALUES
('9.5.3.1.(1)(a)', 'subclause', 9, '9.5.3.1.(1)', NULL,
 'where one or more habitable rooms have a floor area less than 10 m²',
 752, 1);

-- Sub-sub-clause (Sub-clause의 자식)
INSERT INTO nodes VALUES
('9.5.3.1.(1)(a)(i)', 'subsubclause', 9, '9.5.3.1.(1)(a)', NULL,
 'the width of the room shall be measured...',
 752, 1);
```

### 테이블 예시

```sql
-- 테이블 (parent_id = Article ID)
INSERT INTO tables (id, title, parent_id, page, html, source)
VALUES (
    'Table 9.5.3.1',
    'Room Ceiling Heights',
    '9.5.3.1',                    -- ← Article ID로 연결
    752,
    NULL,                         -- html은 나중에 채움
    'pending'                     -- source: pending | camelot | manual
);

INSERT INTO tables (id, title, parent_id, page, html, source)
VALUES (
    'Table 9.10.17.5',
    'Fire Blocks',
    '9.10.17.5',
    NULL,
    NULL,
    'pending'
);

-- 테이블 참조 (어떤 Clause가 테이블을 참조하는지)
INSERT INTO refs (source_id, target_id, target_type)
VALUES ('9.5.3.1.(1)', 'Table 9.5.3.1', 'table');
-- "...shall conform to Table 9.5.3.1"
```

### parent_id 관계 정리

| 노드 | parent_id | 설명 |
|------|-----------|------|
| 9.5.3 | 9.5 | 일반 Subsection |
| **9.5.3A** | **9.5** | Alternative Subsection (9.5.3이 아님!) |
| 9.5.3.1 | 9.5.3 | 일반 Article |
| **9.5.3A.1** | **9.5.3A** | Sub-Article |
| 9.5.1.1 | 9.5.1 | 일반 Article |
| **9.5.1.0A** | **9.5.1** | 0A Article (9.5.1.1보다 먼저!) |
| **9.5.1.1A** | **9.5.1** | Article + Suffix (9.5.1.1 바로 뒤) |
| 9.5.3.1.(1) | 9.5.3.1 | Clause |
| 9.5.3.1.(1)(a) | 9.5.3.1.(1) | Sub-clause |

#### ⚠️ article_suffix의 parent_id 설명

`9.5.1.1A`의 parent는 `9.5.1.1`이 아니라 **`9.5.1`**입니다!

```
9.5.1 (Subsection)
├── 9.5.1.0A (article_0a)   ← seq=1, 먼저
├── 9.5.1.1  (article)      ← seq=2
├── 9.5.1.1A (article_suffix) ← seq=3, 9.5.1.1 바로 뒤
└── 9.5.1.2  (article)      ← seq=4
```

- `9.5.1.1A`는 `9.5.1.1`의 **자식**이 아니라 **형제**
- 둘 다 `9.5.1` (Subsection)의 자식
- 순서만 9.5.1.1 바로 뒤인 것

---

## 6. 검증 쿼리

### 기본 조회

```sql
-- 모든 Section 목록
SELECT id, title FROM nodes WHERE type = 'section' ORDER BY seq;

-- 9.5의 모든 직접 자식 (Subsection + Alt Subsection)
SELECT id, type, title FROM nodes
WHERE parent_id = '9.5'
ORDER BY seq;

-- 예상 결과:
-- 9.5.1 | subsection | General
-- 9.5.2 | subsection | Barrier-Free Design
-- 9.5.3 | subsection | Ceiling Heights
-- 9.5.3A | alt_subsection | Living Rooms...  ← 형제로 나옴!
-- 9.5.3B | alt_subsection | Dining Rooms...
-- ...
```

### 특수 패턴 조회

```sql
-- 모든 Alternative Subsection
SELECT id, title FROM nodes WHERE type = 'alt_subsection';

-- 모든 Article + Suffix
SELECT id, title FROM nodes WHERE type = 'article_suffix';

-- 모든 0A Article
SELECT id, title FROM nodes WHERE type = 'article_0a';

-- 9.5.3A의 자식들 (Sub-Article)
SELECT id, title FROM nodes WHERE parent_id = '9.5.3A';
```

### Clause 조회

```sql
-- 특정 Article의 모든 Clause
SELECT id, content FROM nodes
WHERE parent_id = '9.5.3.1' AND type = 'clause'
ORDER BY seq;

-- 특정 Clause의 Sub-clause
SELECT id, content FROM nodes
WHERE parent_id = '9.5.3.1.(1)' AND type = 'subclause'
ORDER BY seq;

-- Clause 계층 전체 조회 (재귀)
WITH RECURSIVE clause_tree AS (
    SELECT id, parent_id, type, content, 0 as depth
    FROM nodes WHERE id = '9.5.3.1.(1)'

    UNION ALL

    SELECT n.id, n.parent_id, n.type, n.content, ct.depth + 1
    FROM nodes n
    JOIN clause_tree ct ON n.parent_id = ct.id
)
SELECT * FROM clause_tree ORDER BY depth, id;
```

### 테이블 조회

```sql
-- 모든 테이블 목록
SELECT id, title, parent_id, source FROM tables;

-- 특정 Article의 테이블
SELECT t.id, t.title
FROM tables t
WHERE t.parent_id = '9.5.3.1';

-- html이 아직 없는 테이블 (작업 필요)
SELECT id, title FROM tables WHERE html IS NULL;

-- 테이블을 참조하는 Clause 찾기
SELECT r.source_id, r.target_id
FROM refs r
WHERE r.target_type = 'table';

-- Article과 테이블 함께 조회
SELECT
    n.id as article_id,
    n.title as article_title,
    t.id as table_id,
    t.title as table_title
FROM nodes n
LEFT JOIN tables t ON t.parent_id = n.id
WHERE n.type = 'article' AND t.id IS NOT NULL
ORDER BY n.id;
```

### 계층 조회

```sql
-- 특정 노드의 전체 경로
WITH RECURSIVE path AS (
    SELECT id, parent_id, title, type, 0 as depth
    FROM nodes WHERE id = '9.5.3A.1'

    UNION ALL

    SELECT n.id, n.parent_id, n.title, n.type, p.depth + 1
    FROM nodes n
    JOIN path p ON n.id = p.parent_id
)
SELECT * FROM path ORDER BY depth DESC;

-- 예상 결과:
-- 9       | part
-- 9.5     | section
-- 9.5.3A  | alt_subsection  ← 9.5.3이 아님!
-- 9.5.3A.1| sub_article
```

---

## 7. 실습

### schema.sql 파일 생성

```bash
cd scripts
# schema.sql 파일 생성 후 위의 CREATE TABLE 문들 넣기
```

### 테스트 실행

```bash
# 1. DB 생성
sqlite3 ../obc.db < schema.sql

# 2. 예시 데이터 삽입
sqlite3 ../obc.db < examples.sql

# 3. 검증
sqlite3 ../obc.db "SELECT id, type, parent_id FROM nodes WHERE id LIKE '9.5.3%';"
```

---

## 체크리스트

- [x] `OBC_STRUCTURE_RULES.md` 읽음
- [x] **4단계 + 변형** 구조 이해함 (6단계 아님!)
- [x] Alternative Subsection이 **형제**임을 이해함
- [x] 특수 패턴 (0A, Suffix, Sub-Article) 이해함
- [x] **0A vs Suffix 차이** 이해함 (0A=먼저, Suffix=뒤에)
- [x] "Sentence" 아니고 **"Clause"**임을 이해함
- [x] **Clause ID 형식** 이해함 (9.5.3.1.(1), 9.5.3.1.(1)(a))
- [x] nodes, tables, refs 테이블 역할 이해함
- [x] **테이블 ID → parent_id 연결 규칙** 이해함 (Suffix 포함!)
- [x] **seq 정렬 규칙** 이해함
- [x] **search_index 동기화 트리거** 이해함
- [x] schema.sql 파일 생성함
- [x] examples.sql로 테스트 데이터 삽입함
- [x] 검증 쿼리 실행해봄

---

## 다음 단계

Phase 1 완료 후 → [Phase 2: 파서 핵심 로직](./phase2_parser.md)

Phase 2에서는 PDF 텍스트에서 이 구조를 어떻게 감지하는지 배웁니다.
