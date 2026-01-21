# Division 컬럼 추가 마이그레이션 플랜

> 작성일: 2026-01-20
> 목표: DB에 `code`, `division` 컬럼을 추가하여 여러 Building Code와 Division을 지원

---

## 1. 배경

### 1.1 현재 문제

```
현재 DB:
├── Part 2  → Division A "Objectives" (잘못 들어감)
├── Part 8  → Division B ✓
├── Part 9  → Division B ✓
├── Part 10 → Division B ✓
├── Part 11 → Division B ✓
└── Part 12 → Division B ✓
```

- `division` 컬럼이 없어서 Division A Part 2와 Division B Part 2 구분 불가
- ID `2.1.1`이 중복될 수 있음 (PRIMARY KEY 충돌)

### 1.2 OBC 구조

| Division | Part 범위 | 내용 |
|----------|----------|------|
| **A** | Part 1, 2, 3 | Compliance, Objectives, Functional Statements |
| **B** | Part 1~12 | Acceptable Solutions (기술 요구사항) |
| **C** | Part 1, 2 | Administrative Provisions |

**핵심**: Division A/B/C 모두 Part 1, 2, 3이 있음 → ID 충돌!

### 1.3 미래 확장

Ontario Building Code 외에도:
- British Columbia Building Code (BCBC)
- Alberta Building Code
- National Building Code of Canada (NBC)

→ `code` (또는 `jurisdiction`) 컬럼도 필요!

---

## 2. 목표 구조

### 2.1 새 스키마

```sql
CREATE TABLE nodes (
    -- 복합 Primary Key
    code TEXT NOT NULL DEFAULT 'OBC',   -- 'OBC', 'BCBC', 'NBC' 등
    division TEXT NOT NULL DEFAULT 'B', -- 'A', 'B', 'C'
    id TEXT NOT NULL,                   -- '9.5.3.1' 등

    -- 기존 컬럼
    type TEXT NOT NULL,
    part INTEGER NOT NULL,
    parent_id TEXT,
    title TEXT,
    content TEXT,
    page INTEGER,
    seq INTEGER,

    PRIMARY KEY (code, division, id),
    FOREIGN KEY (parent_id) REFERENCES nodes(id)
);
```

### 2.2 URL 구조

```
/                    → 홈페이지 (지역 선택 카드)
/OBC                 → Ontario Building Code (Division 선택)
/OBC/B               → Division B 메인 (Part 목록, 현재 사이드바)
/OBC/B/9.1           → 실제 콘텐츠

/BCBC                → BC Building Code (미래)
/BCBC/B/9.1          → BC 콘텐츠
```

**사용자 플로우**:
```
홈페이지 → 지역 카드 클릭 → Division 선택 → Part/Section 탐색
   /     →     /OBC        →    /OBC/B     →   /OBC/B/9.1
```

**하위 호환**:
- `/code/9.1` → `/OBC/B/9.1`로 리다이렉트 (기존 링크 유지)

### 2.3 사이드바 구조

```
Ontario Building Code (OBC)
├── Division A - Compliance, Objectives...
│   ├── Part 1 - Compliance
│   ├── Part 2 - Objectives
│   └── Part 3 - Functional Statements
├── Division B - Acceptable Solutions
│   ├── Part 1 - General
│   ├── Part 2 - Farm Buildings
│   ├── ...
│   └── Part 12 - Resource Conservation
└── Division C - Administrative
    └── (추후 추가)

BC Building Code (BCBC)  ← 미래
└── ...
```

---

## 3. 단계별 작업

### Phase 1: 준비 (10분)

#### 1.1 백업

```bash
# 필수! 문제 발생 시 복구용
cp data/obc.db data/obc_backup_$(date +%Y%m%d_%H%M%S).db
cp -r codevault/public/data codevault/public/data_backup
```

#### 1.2 현재 상태 확인

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/obc.db')
cursor = conn.cursor()

# 각 Part별 노드 수
cursor.execute('SELECT part, COUNT(*) FROM nodes GROUP BY part ORDER BY part')
print('Part별 노드 수:')
for row in cursor.fetchall():
    print(f'  Part {row[0]}: {row[1]}개')

# Part 2 샘플 (Division A인지 확인)
cursor.execute('SELECT id, title FROM nodes WHERE part = 2 LIMIT 5')
print('\\nPart 2 샘플:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')
"
```

**확인 사항**:
- [ ] Part 2 내용이 "Objectives"인가? (= Division A)
- [ ] Part 8~12 노드 수 정상인가?

---

### Phase 2: DB 마이그레이션 (30분)

#### 2.1 마이그레이션 스크립트 생성

파일: `pipeline/migrate_add_division.py`

```python
"""
Division 및 Code 컬럼 추가 마이그레이션

변경 사항:
1. code 컬럼 추가 (기본값: 'OBC')
2. division 컬럼 추가 (기본값: 'B')
3. PRIMARY KEY를 (code, division, id)로 변경
4. 현재 Part 2는 Division A로 마킹 또는 삭제
"""
import sqlite3
import shutil
from datetime import datetime

DB_PATH = 'data/obc.db'

def backup_db():
    """백업 생성"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'data/obc_backup_{timestamp}.db'
    shutil.copy(DB_PATH, backup_path)
    print(f'백업 생성: {backup_path}')
    return backup_path

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print('1. 새 테이블 생성...')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nodes_new (
            code TEXT NOT NULL DEFAULT 'OBC',
            division TEXT NOT NULL DEFAULT 'B',
            id TEXT NOT NULL,
            type TEXT NOT NULL,
            part INTEGER NOT NULL,
            parent_id TEXT,
            title TEXT,
            content TEXT,
            page INTEGER,
            seq INTEGER,
            PRIMARY KEY (code, division, id)
        )
    ''')

    print('2. 기존 데이터 마이그레이션...')

    # Part 2는 Division A (현재는 삭제 - 나중에 Division A 추가 시 재파싱)
    # Part 8~12는 Division B
    cursor.execute('''
        INSERT INTO nodes_new (code, division, id, type, part, parent_id, title, content, page, seq)
        SELECT 'OBC', 'B', id, type, part, parent_id, title, content, page, seq
        FROM nodes
        WHERE part != 2
    ''')

    migrated = cursor.rowcount
    print(f'   Division B로 마이그레이션: {migrated}개 노드')

    # Part 2 삭제됨 (Division A는 나중에 추가)
    cursor.execute('SELECT COUNT(*) FROM nodes WHERE part = 2')
    deleted = cursor.fetchone()[0]
    print(f'   Part 2 (Division A) 제외: {deleted}개 노드')

    print('3. 테이블 교체...')
    cursor.execute('DROP TABLE nodes')
    cursor.execute('ALTER TABLE nodes_new RENAME TO nodes')

    print('4. 인덱스 생성...')
    cursor.execute('CREATE INDEX idx_nodes_code_division ON nodes(code, division)')
    cursor.execute('CREATE INDEX idx_nodes_part ON nodes(part)')
    cursor.execute('CREATE INDEX idx_nodes_parent ON nodes(parent_id)')

    print('5. FTS 인덱스 재구성...')
    # search_index 테이블도 업데이트 필요
    cursor.execute('DROP TABLE IF EXISTS search_index')
    cursor.execute('''
        CREATE VIRTUAL TABLE search_index USING fts5(
            code,
            division,
            node_id,
            title,
            content,
            tokenize='porter unicode61'
        )
    ''')
    cursor.execute('''
        INSERT INTO search_index (code, division, node_id, title, content)
        SELECT code, division, id, title, content FROM nodes WHERE content IS NOT NULL
    ''')

    conn.commit()

    # 결과 확인
    cursor.execute('SELECT code, division, part, COUNT(*) FROM nodes GROUP BY code, division, part')
    print('\n결과:')
    for row in cursor.fetchall():
        print(f'  {row[0]} / Division {row[1]} / Part {row[2]}: {row[3]}개')

    conn.close()
    print('\n마이그레이션 완료!')

if __name__ == '__main__':
    backup_db()
    migrate()
```

#### 2.2 실행

```bash
cd /c/Users/A/Desktop/lab/upcode-clone
python pipeline/migrate_add_division.py
```

#### 2.3 검증

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/obc.db')
cursor = conn.cursor()

# 스키마 확인
cursor.execute('PRAGMA table_info(nodes)')
print('컬럼 목록:')
for col in cursor.fetchall():
    print(f'  {col[1]} ({col[2]})')

# 데이터 확인
cursor.execute('SELECT code, division, COUNT(*) FROM nodes GROUP BY code, division')
print('\\n데이터 분포:')
for row in cursor.fetchall():
    print(f'  {row[0]} / Division {row[1]}: {row[2]}개')
"
```

**확인 사항**:
- [ ] `code`, `division` 컬럼 존재
- [ ] Division B 데이터만 존재 (Part 2 제외됨)
- [ ] 총 노드 수 = 이전 노드 수 - Part 2 노드 수

---

### Phase 3: 백엔드 수정 (1시간)

#### 3.1 타입 정의 수정

파일: `codevault/src/lib/db.ts`

```typescript
export interface DbNode {
  code: string;      // 추가
  division: string;  // 추가
  id: string;
  type: "part" | "section" | "subsection" | ...;
  parent_id: string | null;
  title: string;
  page: number;
  content: string | null;
  seq: number;
}
```

#### 3.2 쿼리 함수 수정

모든 쿼리에 `code`, `division` 조건 추가:

```typescript
// Before
export function getNodeById(id: string): DbNode | null {
  const stmt = db.prepare("SELECT * FROM nodes WHERE id = ?");
  return stmt.get(id) as DbNode | null;
}

// After
export function getNodeById(
  id: string,
  code: string = 'OBC',
  division: string = 'B'
): DbNode | null {
  const stmt = db.prepare(
    "SELECT * FROM nodes WHERE code = ? AND division = ? AND id = ?"
  );
  return stmt.get(code, division, id) as DbNode | null;
}
```

#### 3.3 수정할 함수 목록

| 함수 | 변경 내용 |
|------|----------|
| `getNodeById()` | code, division 파라미터 추가 |
| `getChildNodes()` | code, division 파라미터 추가 |
| `searchNodes()` | code, division 필터 추가 |
| `getSectionsByPart()` | code, division 파라미터 추가 |
| `getPartFullContent()` | code, division 파라미터 추가 |
| `getToc()` | code, division별 그룹핑 |

---

### Phase 4: 프론트엔드 수정 (1시간)

#### 4.1 URL 라우팅

파일 이동:
```
codevault/src/app/code/[...section]/page.tsx
→ codevault/src/app/code/[[...path]]/page.tsx
```

URL 파싱 로직:

```typescript
// /code/OBC/B/9.1 → code='OBC', division='B', section='9.1'
// /code/B/9.1     → code='OBC' (기본), division='B', section='9.1'
// /code/9.1       → code='OBC', division='B' (기본), section='9.1'

function parseUrl(path: string[]): { code: string; division: string; section: string } {
  // 3개: [code, division, section] → /code/OBC/B/9.1
  if (path.length >= 3 && ['A', 'B', 'C'].includes(path[1])) {
    return {
      code: path[0],
      division: path[1],
      section: path.slice(2).join('.')
    };
  }

  // 2개: [division, section] → /code/B/9.1
  if (path.length >= 2 && ['A', 'B', 'C'].includes(path[0])) {
    return {
      code: 'OBC',
      division: path[0],
      section: path.slice(1).join('.')
    };
  }

  // 1개 이상: [section...] → /code/9.1 (기본값)
  return {
    code: 'OBC',
    division: 'B',
    section: path.join('.')
  };
}
```

#### 4.2 사이드바 수정

파일: `codevault/src/components/layout/Sidebar.tsx`

```typescript
// Division별 Part 그룹핑
interface DivisionGroup {
  division: string;
  label: string;
  parts: TocItem[];
}

const divisions: DivisionGroup[] = [
  {
    division: 'A',
    label: 'Division A - Compliance, Objectives and Functional Statements',
    parts: toc.filter(item => /* Division A Parts */)
  },
  {
    division: 'B',
    label: 'Division B - Acceptable Solutions',
    parts: toc.filter(item => /* Division B Parts */)
  },
];
```

#### 4.3 검색 수정

- 검색 결과에 Division 표시
- 검색 필터에 Division 옵션 추가 (선택사항)

---

### Phase 5: 검증 (30분)

#### 5.1 DB 검증

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/obc.db')
cursor = conn.cursor()

# 1. NULL 체크
cursor.execute('SELECT COUNT(*) FROM nodes WHERE code IS NULL OR division IS NULL')
null_count = cursor.fetchone()[0]
print(f'NULL 값: {null_count}개 (0이어야 함)')

# 2. 데이터 무결성
cursor.execute('SELECT code, division, part, COUNT(*) FROM nodes GROUP BY code, division, part')
print('\\n데이터 분포:')
for row in cursor.fetchall():
    print(f'  {row[0]} / Div {row[1]} / Part {row[2]}: {row[3]}개')

# 3. FTS 인덱스
cursor.execute('SELECT COUNT(*) FROM search_index')
fts_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM nodes WHERE content IS NOT NULL')
content_count = cursor.fetchone()[0]
print(f'\\nFTS 인덱스: {fts_count}개 (content 있는 노드: {content_count}개)')
"
```

#### 5.2 웹 검증

```bash
cd codevault && npm run dev
```

**체크리스트**:
- [ ] `/code/9.1` 접속 → Part 9 정상 표시
- [ ] `/code/B/9.1` 접속 → 동일하게 작동
- [ ] `/code/OBC/B/9.1` 접속 → 동일하게 작동
- [ ] 사이드바 Division 구분 표시
- [ ] 검색 작동

#### 5.3 Playwright 자동 검증

```bash
# mcp__playwright 사용
browser_navigate url=http://localhost:3000/code/9.1
browser_snapshot
# 'Part 9', 'Housing' 등 확인
```

---

### Phase 6: 후속 작업

마이그레이션 완료 후:

1. **Division B Part 추가**
   ```bash
   /add-part 1   # Division B Part 1 - General
   /add-part 2   # Division B Part 2 - Farm Buildings
   /add-part 3   # Division B Part 3 - Fire Protection
   # ... Part 4~7
   ```

2. **Division A 추가** (선택)
   ```bash
   # Division A Part 1, 2, 3 파싱 및 추가
   # division='A' 파라미터로 추가
   ```

3. **다른 Code 추가** (미래)
   ```bash
   # BC Building Code 추가 시
   # code='BCBC', division='B' 파라미터로 추가
   ```

---

## 4. 주의사항

### 4.1 SQLite 제약

```
SQLite는 ALTER TABLE로 PRIMARY KEY를 변경할 수 없음
→ 테이블 재생성 필수 (DROP → CREATE)
→ 데이터 손실 위험 → 반드시 백업!
```

### 4.2 parent_id 참조

```
현재: parent_id는 id만 참조
가정: parent_id는 같은 code, division 내에서만 참조

예: OBC/B/9.1.1의 parent_id = '9.1' (같은 OBC/B 내)
    OBC/A/2.1.1의 parent_id = '2.1' (같은 OBC/A 내)
```

### 4.3 기존 URL 하위 호환

```
/code/9.1 → /code/OBC/B/9.1 로 동작해야 함
→ page.tsx에서 기본값 처리 필수
```

### 4.4 현재 Part 2 데이터

```
지금 DB의 Part 2 = Division A "Objectives"
Division B Part 2 = "Farm Buildings" (완전히 다른 내용!)

→ 마이그레이션에서 Part 2 제외 (Division A는 나중에 추가)
```

### 4.5 FTS 인덱스

```
search_index 테이블도 code, division 컬럼 추가 필요
→ 검색 시 code, division 필터링 가능하도록
```

### 4.6 JSON 파일

```
codevault/public/data/part*.json 파일들은 당장 수정 불필요
→ DB가 primary source, JSON은 백업/참고용
→ 필요 시 나중에 division 필드 추가
```

---

## 5. 롤백 계획

문제 발생 시:

```bash
# 1. 백업에서 복구
cp data/obc_backup_YYYYMMDD_HHMMSS.db data/obc.db

# 2. 코드 변경 취소 (git)
git checkout -- codevault/src/lib/db.ts
git checkout -- codevault/src/app/code/
git checkout -- codevault/src/components/layout/Sidebar.tsx

# 3. 서버 재시작
cd codevault && npm run dev
```

---

## 6. 체크리스트

```markdown
### Phase 1: 준비
- [ ] DB 백업 완료
- [ ] 현재 데이터 개수 확인
- [ ] Part 2가 Division A인지 확인

### Phase 2: DB 마이그레이션
- [ ] 마이그레이션 스크립트 생성
- [ ] 스크립트 실행
- [ ] code, division 컬럼 확인
- [ ] 데이터 개수 확인 (Part 2 제외)
- [ ] FTS 인덱스 확인

### Phase 3: 백엔드
- [ ] DbNode 타입에 code, division 추가
- [ ] getNodeById() 수정
- [ ] getChildNodes() 수정
- [ ] getSectionsByPart() 수정
- [ ] getPartFullContent() 수정
- [ ] getToc() 수정
- [ ] searchNodes() 수정

### Phase 4: 프론트엔드
- [ ] URL 파싱 로직 수정
- [ ] Sidebar Division 그룹 표시
- [ ] 기본값 (OBC, B) 동작 확인
- [ ] 검색 결과 Division 표시

### Phase 5: 검증
- [ ] DB NULL 체크
- [ ] /code/9.1 접속 확인
- [ ] /code/B/9.1 접속 확인
- [ ] 사이드바 확인
- [ ] 검색 확인

### Phase 6: 후속 작업
- [ ] Division B Part 1~7 추가
- [ ] (선택) Division A 추가
```

---

## 7. 파일 목록

### 새로 만들 파일

| 파일 | 설명 |
|------|------|
| `pipeline/migrate_add_division.py` | DB 마이그레이션 스크립트 |

### 수정할 파일

| 파일 | 변경 내용 |
|------|----------|
| `codevault/src/lib/db.ts` | code, division 파라미터 추가 |
| `codevault/src/lib/types.ts` | DbNode 타입 수정 |
| `codevault/src/app/code/[...section]/page.tsx` | URL 파싱 변경 |
| `codevault/src/components/layout/Sidebar.tsx` | Division 그룹 표시 |

---

## 8. 예상 소요 시간

| Phase | 작업 | 시간 |
|-------|------|------|
| 1 | 준비 (백업, 확인) | 10분 |
| 2 | DB 마이그레이션 | 30분 |
| 3 | 백엔드 수정 | 1시간 |
| 4 | 프론트엔드 수정 | 1시간 |
| 5 | 검증 | 30분 |
| **합계** | | **3시간 10분** |

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-01-20 | 초안 작성, `code` 컬럼 추가 (미래 확장성) |
