# OBC PDF 파싱 구조 개선 프로젝트

> SQLite 기반 계층적 데이터 구조로 전환
>
> 최종 목표: Part 9 (324p) → 전체 OBC (2000p) 확장

---

## 왜 이 작업을 하는가?

### 현재 문제
```
part9.json = 플랫한 텍스트 덩어리

문제점:
- Article(9.5.3.1)이 content 안에 섞여있음
- 테이블이 어느 섹션에 속하는지 불명확
- Cross-reference 추적 불가
- 2000페이지로 확장 시 검색 느림
```

### 목표 구조
```
obc.db (SQLite)

장점:
- 모든 요소가 개별 레코드 (검색 가능)
- parent-child 관계 명확
- Cross-reference 자동 추적
- 2000페이지도 빠른 검색
```

---

## Phase 구조

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5
스키마      파서 로직    트리 빌더    Part 9      Next.js
설계                               전체 파싱    연동
```

| Phase | 파일 | 목표 | 예상 시간 |
|-------|------|------|----------|
| 1 | [phase1_schema.md](./phase1_schema.md) | DB 구조 이해 | 1-2시간 |
| 2 | [phase2_parser.md](./phase2_parser.md) | 정규식 패턴 이해 | 2-3시간 |
| 3 | [phase3_tree.md](./phase3_tree.md) | 트리 구축 이해 | 2-3시간 |
| 4 | [phase4_parsing.md](./phase4_parsing.md) | Part 9 파싱 | 4-5시간 |
| 5 | [phase5_nextjs.md](./phase5_nextjs.md) | 웹 연동 | 3-4시간 |

**총 예상 시간: 12-17시간**

---

## ⚠️ 중요: OBC 실제 계층 구조

> **반드시 \`_checklist/OBC_STRUCTURE_RULES.md\` 참고!**

### 4단계 + 변형 (6단계 아님!)

```
Part 9                                    ← Level 0: 최상위
│
├── Section 9.5                           ← Level 1: 대분류 (~41개)
│   │
│   ├── Subsection 9.5.1                  ← Level 2: 중분류 (~274개)
│   │   ├── Article 9.5.1.0A Application  ← 특수: 0A Article
│   │   ├── Article 9.5.1.1               ← Level 3: 조항 (~1,081개)
│   │   │   └── Clause (1), (2)...        ← Level 4: 조항 내용
│   │   │       └── Sub-clause (a), (b)...
│   │   └── Article 9.5.1.1A Floor Areas  ← 특수: Article + A Suffix
│   │
│   ├── Subsection 9.5.3                  ← 일반 Subsection
│   │   ├── Article 9.5.3.1
│   │   ├── Article 9.5.3.2
│   │   └── Article 9.5.3.3
│   │
│   ├── Subsection 9.5.3A Living Rooms    ← 특수: Alternative Subsection (형제!)
│   │   └── Sub-Article 9.5.3A.1          ← 특수: Sub-Article
│   │
│   ├── Subsection 9.5.3B Dining Rooms    ← 특수: Alternative Subsection
│   │   └── Sub-Article 9.5.3B.1
│   │
│   └── ... (9.5.3C ~ 9.5.3F)
```

### ID 패턴 (특수 케이스 포함)

| 타입 | 패턴 | 예시 | 개수 |
|------|------|------|------|
| Section | \`9.X\` | 9.5, 9.10, 9.25 | ~41 |
| Subsection | \`9.X.X\` | 9.5.1, 9.10.17 | ~274 |
| **Alt Subsection** | \`9.X.X[A-Z]\` | 9.5.3A, 9.5.3B | 6 |
| Article | \`9.X.X.X\` | 9.5.1.1, 9.8.6.3 | ~1,081 |
| **Article + Suffix** | \`9.X.X.X[A-Z]\` | 9.5.1.1A, 9.32.3.9B | ~12 |
| **0A Article** | \`9.X.X.X0A\` | 9.33.6.10A | 1 |
| **Sub-Article** | \`9.X.X[A-Z].X\` | 9.5.3A.1, 9.5.3D.6 | ~22 |
| Clause | \`(1)\`, \`(2)\` | (1), (2), (3) | 많음 |
| Sub-clause | \`(a)\`, \`(b)\` | (a), (b), (c) | 많음 |

**핵심:**
- "Sentence" 아님 → **"Clause"**가 올바른 용어
- 9.5.3A는 9.5.3의 **형제**이지 자식이 아님!

---

## 최종 파일 구조

```
upcode-clone/
├── obc.db                          # SQLite 데이터베이스
├── scripts/
│   ├── schema.sql                  # DB 스키마
│   ├── patterns.py                 # 정규식 패턴
│   ├── tree_builder.py             # 트리 빌더
│   ├── parse_part9.py              # Part 9 파서
│   └── test_*.py                   # 테스트 파일들
├── _checklist/
│   ├── OBC_STRUCTURE_RULES.md      # ⚠️ OBC 구조 규칙 (필독!)
│   └── structure/
│       ├── README.md               # 이 파일
│       ├── phase1_schema.md
│       ├── phase2_parser.md
│       ├── phase3_tree.md
│       ├── phase4_parsing.md
│       ├── phase5_nextjs.md
│       └── VALIDATION_REPORT.md
└── codevault/
    └── src/
        └── lib/
            └── db.ts               # DB 연결 모듈
```

---

## 진행 상황

### Phase 1: 스키마 설계 ✅
- [x] OBC 문서 계층 구조 이해 (OBC_STRUCTURE_RULES.md 읽음)
- [x] SQLite 스키마 작성 (schema.sql)
- [x] 예시 데이터로 테스트 (obc.db 생성됨)
- [x] 문서 작성 완료

### Phase 2: 파서 핵심 로직 ✅
- [x] 정규식 패턴 작성 - patterns.py
- [x] 패턴 테스트 통과 - test_patterns.py
- [x] 참조 추출 로직 완성 - extract_references()
- [x] 문서 작성 완료

### Phase 3: 트리 빌더 ✅
- [x] TreeBuilder 클래스 구현 - tree_builder.py
- [x] Alternative Subsection 형제 관계 처리
- [x] 테스트 통과 - test_tree.py (6개 테스트)
- [x] 문서 작성 완료 (2026-01-18)

### Phase 4: Part 9 전체 파싱
- [ ] PDF 파싱 완료
- [ ] SQLite DB 생성
- [ ] 검증 쿼리 통과
- [ ] 기존 데이터와 비교 검증

### Phase 5: Next.js 연동
- [ ] better-sqlite3 설치
- [ ] DB 연결 모듈 작성
- [ ] 컴포넌트 수정
- [ ] 웹에서 정상 표시 확인

---

## 참고 문서

- **OBC 구조 규칙**: \`_checklist/OBC_STRUCTURE_RULES.md\` ⚠️ 필독
- 상세 계획: \`C:\Users\A\.claude\plans\polished-seeking-tarjan.md\`
- 기존 실수 기록: \`CLAUDE.md\`의 실수 기록 섹션
- PDF 파싱 가이드: \`_report/PDF_PARSING_GUIDE.md\`
