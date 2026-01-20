# OBC Part 9 구조 규칙 (Building Code Specialist Reference)

> PDF 분석 결과 기반 정확한 OBC 계층 구조
>
> Claude가 파싱/렌더링 시 반드시 참고해야 함

---

## 핵심 요약

**제가 틀린 것:**
```
6단계: Part → Section → Subsection → Article → Sentence → Clause → Subclause
```

**실제 OBC 구조:**
```
4단계 + 변형:
  Level 1: Section (9.X)
  Level 2: Subsection (9.X.X) 또는 Alternative Subsection (9.X.X[A-Z])
  Level 3: Article (9.X.X.X) 또는 Sub-Article (9.X.X[A-Z].X)
  Level 4: Clause (1), (2), (3)... → Sub-clause (a), (b), (c)...
```

---

## 1. 실제 계층 구조

### Level 1: Section (9.X)

```
패턴: 9.X (X = 1-41)
예시: 9.1, 9.5, 9.10, 9.25, 9.33, 9.41
개수: 약 41개
역할: 대분류 (General, Materials, Structure, Design, Finishes...)
```

### Level 2: Subsection (9.X.X)

```
패턴: 9.X.X
예시: 9.4.2, 9.5.1, 9.8.6, 9.10.17
개수: 약 274개
역할: 중분류 (Ceiling Heights, Fire Stops, etc.)
```

### Level 2 변형: Alternative Subsection (9.X.X[A-Z])

```
패턴: 9.X.X[A-Z] (숫자 뒤에 바로 대문자)
예시: 9.5.3A, 9.5.3B, 9.5.3C, 9.5.3D, 9.5.3E, 9.5.3F
개수: 6개 (모두 9.5.3 아래)
역할: 방 종류별 대안 섹션
  - 9.5.3A: Living Rooms
  - 9.5.3B: Dining Rooms
  - 9.5.3C: Kitchens
  - 9.5.3D: Bedrooms
  - 9.5.3E: Combined Spaces
  - 9.5.3F: Bathrooms
```

### Level 3: Article (9.X.X.X)

```
패턴: 9.X.X.X
예시: 9.4.2.1, 9.5.1.1, 9.8.6.3
개수: 약 1,081개
역할: 실제 요구사항 조항 (MAIN CONTENT)
```

### Level 3 변형: Article with Suffix (9.X.X.X[A-Z])

```
패턴: 9.X.X.X[A-Z]
예시:
  - 9.5.1.1A (Floor Areas)
  - 9.10.14.3A (Inadequate Firefighting Facilities)
  - 9.25.3.3A (Vapour Barriers Used as Air Barriers)
  - 9.31.4.1A (Laundry Fixtures)
  - 9.32.3.9B, 9.32.3.9C
개수: 약 12개
역할: 기본 Article의 확장/대안 조항
```

### Level 3 특수: 0A Article (9.X.X.0A)

```
패턴: 9.X.X.0A (Article 번호가 "0A")
예시: 9.5.1.0A (Application)
개수: 1개 발견
역할: Subsection의 첫 번째 도입/적용 조항
위치: 9.X.X.1보다 **먼저** 나옴!

⚠️ 주의: 9.33.6.10A는 0A가 아님! (10 + A = article_suffix)
```

### Level 3: Sub-Article (9.X.X[A-Z].X)

```
패턴: 9.X.X[A-Z].X
예시:
  - 9.5.3A.1 (Areas of Living Rooms)
  - 9.5.3D.1 (Areas of Bedrooms)
  - 9.5.3D.2 (Areas of Master Bedrooms)
  - 9.5.3D.3 (Areas of Combination Bedrooms)
  - 9.5.3F.2 (Doors to Rooms Containing Water Closets)
개수: 약 22개
역할: Alternative Subsection 아래의 Article
```

### Level 4: Clause & Sub-clause

```
Clause: (1), (2), (3)...
Sub-clause: (a), (b), (c)...
Sub-sub-clause: (i), (ii), (iii)... (로마숫자)

※ 이전에 "Sentence"라고 불렀던 것이 실제로는 "Clause"
```

---

## 2. 실제 트리 예시 (9.5)

```
9.5 Design of Areas, Spaces and Doorways (SECTION)
│
├── 9.5.1 General (SUBSECTION)
│   ├── 9.5.1.0A Application (0A ARTICLE - 특수!)
│   ├── 9.5.1.1 Method of Measurement (ARTICLE)
│   ├── 9.5.1.1A Floor Areas (ARTICLE + A SUFFIX)
│   ├── 9.5.1.2 Combination Rooms
│   └── 9.5.1.3 Lesser Areas and Dimensions
│
├── 9.5.2 Barrier-Free Design (SUBSECTION)
│   ├── 9.5.2.1 General
│   ├── 9.5.2.2 Protection on Floor Areas
│   ├── 9.5.2.3 Reserved
│   └── 9.5.2.4 Stud Wall Reinforcement
│
├── 9.5.3 Ceiling Heights (SUBSECTION)
│   ├── 9.5.3.1 Ceiling Heights of Rooms
│   ├── 9.5.3.2 Mezzanines
│   └── 9.5.3.3 Storage Garages
│
├── 9.5.3A Living Rooms (ALTERNATIVE SUBSECTION)
│   └── 9.5.3A.1 Areas of Living Rooms (SUB-ARTICLE)
│
├── 9.5.3B Dining Rooms (ALTERNATIVE SUBSECTION)
│   └── 9.5.3B.1 Area of Dining Rooms
│
├── 9.5.3C Kitchens (ALTERNATIVE SUBSECTION)
│   └── 9.5.3C.1 Kitchen Areas
│
├── 9.5.3D Bedrooms (ALTERNATIVE SUBSECTION)
│   ├── 9.5.3D.1 Areas of Bedrooms
│   ├── 9.5.3D.2 Areas of Master Bedrooms
│   ├── 9.5.3D.3 Areas of Combination Bedrooms
│   ├── 9.5.3D.4 Areas of Other Sleeping Rooms
│   ├── 9.5.3D.5 Recreational Camps
│   └── 9.5.3D.6 Camps for Housing Workers
│
├── 9.5.3E Combined Spaces (ALTERNATIVE SUBSECTION)
│   └── 9.5.3E.1 Combined Living, Dining, Bedroom
│
└── 9.5.3F Bathrooms (ALTERNATIVE SUBSECTION)
    ├── 9.5.3F.1 Space to Accommodate Fixtures
    └── 9.5.3F.2 Doors to Rooms Containing Water Closets
```

---

## 3. ID 패턴 정규식

```python
# Section (9.X)
SECTION = r'^9\.(\d+)(?!\.\d)'
# 매치: 9.5, 9.10, 9.25
# 비매치: 9.5.1, 9.5.1.1

# Subsection (9.X.X)
SUBSECTION = r'^9\.(\d+)\.(\d+)(?![A-Z\d])'
# 매치: 9.5.1, 9.10.17
# 비매치: 9.5.1A, 9.5.1.1

# Alternative Subsection (9.X.X[A-Z])
ALT_SUBSECTION = r'^9\.(\d+)\.(\d+)([A-Z])(?!\.\d)'
# 매치: 9.5.3A, 9.5.3B
# 비매치: 9.5.3, 9.5.3A.1

# Article (9.X.X.X)
ARTICLE = r'^9\.(\d+)\.(\d+)\.(\d+)(?![A-Z0-9])'
# 매치: 9.5.1.1, 9.10.17.9
# 비매치: 9.5.1.1A, 9.5.3A.1

# Article with Suffix (9.X.X.X[A-Z])
ARTICLE_SUFFIX = r'^9\.(\d+)\.(\d+)\.(\d+)([A-Z])(?!\d)'
# 매치: 9.5.1.1A, 9.32.3.9B
# 비매치: 9.5.3A.1

# 0A Article (9.X.X.0A)
ARTICLE_0A = r'^9\.(\d+)\.(\d+)\.0A'
# 매치: 9.5.1.0A (진짜 0A만!)
# 비매치: 9.33.6.10A (이건 article_suffix)

# Sub-Article (9.X.X[A-Z].X)
SUB_ARTICLE = r'^9\.(\d+)\.(\d+)([A-Z])\.(\d+)'
# 매치: 9.5.3A.1, 9.5.3D.6
```

---

## 4. 패턴별 개수 통계

| 패턴 | 개수 | 비율 |
|------|------|------|
| Section (9.X) | ~41 | - |
| Subsection (9.X.X) | ~274 | 97% |
| Alternative Subsection (9.X.X[A-Z]) | 6 | 2% |
| Article (9.X.X.X) | ~1,081 | 98% |
| Article + Suffix (9.X.X.X[A-Z]) | 12 | 1% |
| 0A Article | 1 | <1% |
| Sub-Article (9.X.X[A-Z].X) | ~22 | 2% |

**99% 이상은 기본 패턴** (9.X.X, 9.X.X.X)
**특수 패턴은 주로 9.5.3에 집중**

---

## 5. 파싱 시 주의사항

### 순서 문제
```
잘못된 순서:
9.5.1.1
9.5.1.1A  ← 이게 9.5.1.1 바로 뒤에 와야 함!
9.5.1.2

올바른 순서:
9.5.1.1 Method of Measurement
9.5.1.1A Floor Areas  ← A suffix는 기본 Article 바로 뒤
9.5.1.2 Combination Rooms
```

### 0A 특수 케이스
```
9.5.1.0A Application    ← 이게 먼저! (진짜 0A)
9.5.1.1 Method of...    ← 그 다음 일반 Article

⚠️ 9.33.6.10A는 0A가 아님:
9.33.6.10 ...           ← 일반 Article
9.33.6.10A Supply...    ← Article Suffix (10 + A)
9.33.6.11 ...           ← 다음 Article
```

### Alternative Subsection 처리
```
9.5.3 (일반 Subsection) → 9.5.3.1, 9.5.3.2, 9.5.3.3
9.5.3A (대안 Subsection) → 9.5.3A.1
9.5.3B (대안 Subsection) → 9.5.3B.1
...

※ 9.5.3A는 9.5.3의 "자식"이 아니라 "형제"!
```

---

## 6. SQLite 스키마 수정 필요

```sql
-- 기존 스키마 (틀림)
type TEXT  -- 'section', 'subsection', 'article', 'sentence'...

-- 수정된 스키마
type TEXT  -- 다음 값들:
           -- 'section'          : 9.X
           -- 'subsection'       : 9.X.X
           -- 'alt_subsection'   : 9.X.X[A-Z]
           -- 'article'          : 9.X.X.X
           -- 'article_suffix'   : 9.X.X.X[A-Z]
           -- 'article_0a'       : 9.X.X.0A      (예: 9.5.1.0A)
           -- 'sub_article'      : 9.X.X[A-Z].X
           -- 'clause'           : (1), (2)...
           -- 'subclause'        : (a), (b)...
```

---

## 7. 체크리스트

파싱 전 확인 (Phase 2에서 구현):
- [ ] 9.5.3A-F Alternative Subsection 처리 로직 있음
- [ ] 9.X.X.XA 같은 Suffix Article 처리 로직 있음
- [ ] 0A Article (9.5.1.0A) 처리 로직 있음
- [ ] 정규식이 모든 패턴 커버함

검증 시 확인 (Phase 4에서 검증):
- [ ] 9.5.1.1A가 9.5.1.1 바로 뒤에 있음
- [ ] 9.5.3A가 9.5.3 형제로 처리됨 (자식 아님)
- [ ] 9.5.3D.1~6 모두 파싱됨

---

## 8. 이전 문서 수정 필요

다음 파일들의 "6단계 계층" 설명 수정 필요:
- `_checklist/structure/README.md`
- `_checklist/structure/phase1_schema.md`
- `_checklist/structure/phase2_parser.md`
- `_checklist/structure/phase3_tree.md`

**수정 내용:**
1. "6단계 계층" → "4단계 + 변형"
2. "Sentence" → "Clause"
3. Alternative Subsection 패턴 추가
4. Article Suffix 패턴 추가
