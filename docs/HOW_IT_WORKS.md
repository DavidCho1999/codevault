# CodeVault 시스템 완전 가이드

> 비전공자를 위한 전체 흐름 설명
> PDF에서 웹까지, 데이터가 어떻게 흘러가는지

---

## 1. 큰 그림: 전체 흐름

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CodeVault 데이터 파이프라인                        │
└─────────────────────────────────────────────────────────────────────────┘

  [원본 PDF]              [변환]              [저장]              [표시]
      │                     │                   │                   │
      ▼                     ▼                   ▼                   ▼
┌──────────┐         ┌──────────┐         ┌──────────┐         ┌──────────┐
│  301880  │         │  Python  │         │   JSON   │         │  Next.js │
│   .pdf   │ ──────► │ 스크립트  │ ──────► │  + DB    │ ──────► │   웹앱   │
│          │  파싱    │          │  저장    │          │  로드    │          │
└──────────┘         └──────────┘         └──────────┘         └──────────┘
   source/            pipeline/         codevault/public/       codevault/
                                           data/                  src/
```

### 비유로 이해하기

**도서관 책 → 디지털 검색 시스템**

1. **PDF** = 종이책 (Ontario Building Code 원본)
2. **Python 스크립트** = 사서가 책을 읽고 카드 목록 작성
3. **JSON 파일** = 카드 목록 (검색 가능한 형태)
4. **DB (SQLite)** = 도서관 데이터베이스
5. **웹앱** = 온라인 검색 시스템

---

## 2. OBC(Ontario Building Code) 계층 구조

### 실제 Building Code 구조

```
Division B (건물 요구사항)
└── Part 9 - Housing and Small Buildings
    └── Section 9.4 - Design Loads
        └── Subsection 9.4.2 - Specified Loads
            └── Article 9.4.2.1 - Application
                └── Clause (1) - 첫 번째 조항
                    └── Sub-clause (a) - 세부 조항
```

### 각 레벨 설명

| 레벨 | 예시 | 설명 |
|------|------|------|
| **Part** | Part 9 | 대주제 (주거 및 소규모 건물) |
| **Section** | 9.4 | 중주제 (설계 하중) |
| **Subsection** | 9.4.2 | 소주제 (지정 하중) |
| **Article** | 9.4.2.1 | 개별 규정 (적용 범위) |
| **Clause** | (1), (2), (3) | 조항 (구체적 요구사항) |
| **Sub-clause** | (a), (b), (c) | 세부 조항 |

### 특수 케이스 (Part 9 전용)

```
일반 Article:     9.4.2.1
Article Suffix:   9.4.2.1A      ← 9.4.2.1의 확장/대안
Alt Subsection:   9.5.3A        ← 9.5.3의 대안 (A, B, C...)
Sub-Article:      9.5.3A.1      ← Alternative Subsection의 Article
0A Article:       9.33.6.10A    ← 특수 케이스
```

---

## 3. 파일별 역할

### 폴더 구조

```
upcode-clone/
│
├── source/                          [입력: 원본 PDF]
│   └── 2024 Building Code Compendium/
│       ├── 301880.pdf              ← Part 8, 9, 10, 11, 12 포함
│       └── 301881.pdf              ← Appendix, 부가 자료
│
├── pipeline/                        [처리: 변환 스크립트]
│   ├── schema.sql                  ← DB 테이블 구조 정의
│   ├── migrate_json.py             ← JSON → DB 변환
│   ├── migrate_tables.py           ← 테이블 데이터 → DB
│   ├── add_articles_to_db.py       ← Part 10-12 Article 추가
│   ├── parse_part9.py              ← PDF 직접 파싱 (대안)
│   ├── validate_part.py            ← 검증 도구
│   └── auto_screen.py              ← 자동 비교 도구
│
├── data/                            [출력: 생성된 DB]
│   └── obc.db                      ← SQLite 데이터베이스
│
├── codevault/                       [웹앱]
│   ├── public/data/                ← JSON 파일들
│   │   ├── part9.json              ← Part 9 전체 데이터
│   │   ├── part9_tables.json       ← Part 9 테이블들
│   │   ├── part10.json             ← Part 10 데이터
│   │   ├── part11.json             ← Part 11 데이터
│   │   └── part12.json             ← Part 12 데이터
│   │
│   └── src/
│       ├── app/                    ← 페이지 라우팅
│       │   ├── page.tsx            ← 홈페이지
│       │   └── [part]/[section]/   ← 동적 라우팅
│       │
│       ├── components/             ← UI 컴포넌트
│       │   ├── SectionView.tsx     ← 섹션 표시 (핵심!)
│       │   ├── Sidebar.tsx         ← 사이드바 네비게이션
│       │   └── SearchBar.tsx       ← 검색 기능
│       │
│       └── lib/                    ← 유틸리티
│           └── types.ts            ← TypeScript 타입 정의
│
└── docs/                            [문서]
    ├── checklist/                  ← 검증 체크리스트
    └── report/                     ← 작업 보고서
```

---

## 4. 데이터 변환 과정

### Step 1: PDF 파싱 (이미 완료됨)

```
PDF 텍스트 추출
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  "9.4.2.  Specified Loads                                   │
│   9.4.2.1.  Application                                     │
│   (1) Except as provided in Sentences (2) to (6)..."        │
└─────────────────────────────────────────────────────────────┘
     │
     ▼  정규식으로 구조 분석
     │
┌─────────────────────────────────────────────────────────────┐
│  {                                                          │
│    "id": "9.4.2",                                           │
│    "title": "Specified Loads",                              │
│    "subsections": [{                                        │
│      "id": "9.4.2.1",                                       │
│      "title": "Application",                                │
│      "content": "(1) Except as provided..."                 │
│    }]                                                       │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

### Step 2: JSON → DB 변환

```bash
# 실행 명령어
python pipeline/migrate_json.py
python pipeline/migrate_tables.py
python pipeline/add_articles_to_db.py
```

```
part9.json                    obc.db (nodes 테이블)
┌─────────────┐              ┌────────────────────────────────┐
│ sections: [ │              │ id     │ type      │ parent_id │
│   {         │   ──────►    ├────────┼───────────┼───────────┤
│     id: 9.4 │              │ 9      │ part      │ NULL      │
│     ...     │              │ 9.4    │ section   │ 9         │
│   }         │              │ 9.4.2  │ subsection│ 9.4       │
│ ]           │              │ 9.4.2.1│ article   │ 9.4.2     │
└─────────────┘              └────────────────────────────────┘
```

### Step 3: 웹에서 데이터 로드

```typescript
// Next.js에서 JSON 직접 import
import part9Data from '@/public/data/part9.json'

// 또는 DB에서 API로 조회
const response = await fetch('/api/sections/9.4')
```

---

## 5. 웹앱 렌더링 흐름

### 사용자가 "9.4.2" 클릭하면?

```
┌─────────────────────────────────────────────────────────────┐
│  1. URL 변경: /part9/9.4.2                                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Next.js 라우터가 [part]/[section]/page.tsx 로드         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  3. part9.json에서 9.4.2 데이터 찾기                        │
│     {                                                       │
│       id: "9.4.2",                                          │
│       title: "Specified Loads",                             │
│       content: "..."                                        │
│     }                                                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  4. SectionView.tsx가 content를 HTML로 변환                 │
│     - 마크다운 → HTML                                       │
│     - 테이블 렌더링                                         │
│     - 수식 렌더링                                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  5. 브라우저에 표시                                         │
│     ┌──────────────────────────────────┐                    │
│     │ 9.4.2. Specified Loads           │                    │
│     │                                  │                    │
│     │ 9.4.2.1. Application             │                    │
│     │ (1) Except as provided...        │                    │
│     └──────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. 핵심 컴포넌트 설명

### SectionView.tsx - 콘텐츠 렌더러

```
역할: JSON의 content 문자열 → 화면에 보이는 HTML

입력: "(1) Except as provided in Sentence (2)..."

처리:
  1. Article 헤딩 인식 (#### 9.4.2.1.)
  2. Clause 번호 인식 ((1), (2), (3)...)
  3. Sub-clause 인식 ((a), (b), (c)...)
  4. 테이블 HTML 처리 (<table>...</table>)
  5. 수식 처리 (S = CbSs + Sr)
  6. 줄바꿈/들여쓰기 정리

출력: <div><h4>9.4.2.1. Application</h4><p>(1) Except...</p></div>
```

### Sidebar.tsx - 네비게이션

```
역할: Part/Section/Subsection 트리 구조 표시

입력: part9.json의 sections 배열

출력:
  ▼ Part 9 - Housing and Small Buildings
    ▼ 9.4 - Design Loads
      ├── 9.4.1 - Structural Loads
      ├── 9.4.2 - Specified Loads    ← 클릭 가능
      └── 9.4.3 - Additional Loads
```

---

## 7. DB 스키마 (obc.db)

### nodes 테이블 - 모든 계층 저장

```sql
CREATE TABLE nodes (
    id        TEXT PRIMARY KEY,  -- "9.4.2.1"
    type      TEXT,              -- "article", "section", "subsection"
    part      INTEGER,           -- 9
    parent_id TEXT,              -- "9.4.2"
    title     TEXT,              -- "Application"
    content   TEXT,              -- "(1) Except as provided..."
    seq       INTEGER,           -- 정렬 순서
    page      INTEGER            -- PDF 페이지 번호
);
```

### 계층 구조 예시

```
id         │ type       │ parent_id │ title
───────────┼────────────┼───────────┼─────────────────────
9          │ part       │ NULL      │ Housing and Small...
9.4        │ section    │ 9         │ Design Loads
9.4.2      │ subsection │ 9.4       │ Specified Loads
9.4.2.1    │ article    │ 9.4.2     │ Application
9.4.2.1(1) │ clause     │ 9.4.2.1   │ NULL
```

### tables 테이블 - OBC 테이블 저장

```sql
CREATE TABLE tables (
    id        TEXT PRIMARY KEY,  -- "Table 9.4.3.1"
    parent_id TEXT,              -- "9.4.3.1"
    title     TEXT,              -- "Snow Load Factors"
    html      TEXT,              -- "<table>...</table>"
    source    TEXT               -- 출처 정보
);
```

---

## 8. 데이터 흐름 요약

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              데이터 흐름                                 │
└─────────────────────────────────────────────────────────────────────────┘

[PDF] ──► [Python 파싱] ──► [JSON 파일] ──► [Next.js] ──► [브라우저]
                │                              │
                ▼                              │
           [SQLite DB] ◄───────────────────────┘
                                          (향후 API용)

현재 상태:
- Part 9: JSON 직접 사용 (완전)
- Part 10-12: JSON 직접 사용 (Article 마커 방식)
- DB: 검색/검증용 (웹앱은 JSON 우선 사용)
```

---

## 9. 작업별 명령어 모음

### 일상적인 작업

```bash
# 웹앱 실행
cd codevault && npm run dev

# DB 재생성 (JSON 변경 후)
python pipeline/migrate_json.py
python pipeline/migrate_tables.py
python pipeline/add_articles_to_db.py

# 데이터 검증
python pipeline/validate_part.py --part 9
```

### 문제 해결

```bash
# DB 내용 확인
python -c "
import sqlite3
conn = sqlite3.connect('data/obc.db')
cur = conn.cursor()
cur.execute('SELECT part, type, COUNT(*) FROM nodes GROUP BY part, type')
for row in cur.fetchall(): print(row)
"

# JSON 구조 확인
python -c "
import json
d = json.load(open('codevault/public/data/part9.json', encoding='utf-8'))
print(f'Sections: {len(d[\"sections\"])}')
"
```

---

## 10. 자주 묻는 질문

### Q: Part 10-12는 왜 [ARTICLE:...] 마커를 쓰나요?

Part 9는 분량이 많아서 (40 sections, 1000+ articles) 별도 파서로 세밀하게 분리했습니다.
Part 10-12는 분량이 적어서 (4-5 sections씩) 마커 방식으로 충분합니다.

### Q: JSON과 DB 둘 다 왜 필요한가요?

- **JSON**: 웹앱에서 직접 로드 (빠름, 단순)
- **DB**: 복잡한 검색, 통계, 검증용 (향후 API 확장)

### Q: 새 Part를 추가하려면?

1. PDF에서 해당 Part 페이지 범위 확인
2. Python 스크립트로 파싱 → JSON 생성
3. `migrate_json.py` 수정하여 DB에 추가
4. 웹앱에서 해당 Part 라우트 추가

---

## 11. 다음 단계

현재 남은 작업:

1. [ ] Part 12 Article 추가 (DB에 없음)
2. [ ] Part 8 Article 확인 및 추가
3. [ ] 웹앱에서 Part 10-12 네비게이션 확인
4. [ ] 검색 기능 통합 테스트

---

*이 문서는 `docs/HOW_IT_WORKS.md`에 저장됩니다.*
*질문이 있으면 언제든 물어보세요!*
