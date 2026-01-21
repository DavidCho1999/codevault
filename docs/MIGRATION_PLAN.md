# Marker 기반 통합 마이그레이션 계획

> 모든 Part를 marker 변환 결과 기반으로 통일하는 계획
> Part 10, 11, 12 방식으로 Part 8, 9도 변환

---

## 1. 현재 상태 비교

### 두 가지 파싱 방식

```
┌─────────────────────────────────────────────────────────────────────────┐
│  방식 A: PyMuPDF/Camelot 직접 파싱 (현재 Part 9)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PDF ──► PyMuPDF ──► 텍스트 블록 ──► 정규식 파싱 ──► JSON               │
│                          │                                              │
│                     좌표 기반 정렬                                       │
│                                                                         │
│  장점: 페이지/좌표 정보 보존                                             │
│  단점: 복잡, 테이블 처리 어려움, 수식 누락                               │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  방식 B: Marker 변환 (현재 Part 10, 11, 12)                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PDF ──► Marker ──► Markdown ──► 정규식 파싱 ──► JSON                   │
│                         │                                               │
│                   깔끔한 마크다운                                        │
│                                                                         │
│  장점: 테이블 자동 변환, 수식 보존, 깔끔한 구조                          │
│  단점: 페이지 정보 손실                                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 현재 Part별 상태

| Part | 파싱 방식 | JSON 크기 | 상태 |
|------|----------|----------|------|
| Part 8 | PyMuPDF | 152KB | Article 없음 |
| Part 9 | PyMuPDF + Camelot | 715KB | 완전 (1023 articles) |
| Part 10 | **Marker** | 13KB | 완전 |
| Part 11 | **Marker** | 219KB | 완전 |
| Part 12 | **Marker** | 8KB | 완전 |

### Marker 출력 현황

```
data/marker/
├── 301880_full.md           (5.3MB) ← 전체 PDF!
├── 301880_full_normalized.md
├── chunk_01/ ~ chunk_13/    ← 청크별 변환
├── part8.md                 (157KB)
└── part910_tables/
```

---

## 2. 목표: 통일된 구조

### JSON 구조 (Part 10, 11, 12 방식)

```json
{
  "id": "9",
  "title": "Housing and Small Buildings",
  "sections": [
    {
      "id": "9.4",
      "title": "Design Loads",
      "subsections": [
        {
          "id": "9.4.2",
          "title": "Specified Loads",
          "content": "[ARTICLE:9.4.2.1:Application]\n\n(1) Except as provided...\n\n[ARTICLE:9.4.2.2:Snow Loads]\n\n(1) The specified..."
        }
      ]
    }
  ]
}
```

### 핵심 포인트

1. **`[ARTICLE:ID:Title]` 마커** - Article 경계 표시
2. **content 안에 모든 내용** - Article이 별도 노드가 아님
3. **테이블은 HTML로 포함** - `<table>...</table>`
4. **수식은 텍스트로 유지** - `S = CbSs + Sr`

---

## 3. 마이그레이션 단계

### Phase 1: Marker 출력 분리 (Part별 .md 파일)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  입력: data/marker/301880_full.md (전체 PDF)                            │
│                                                                         │
│  처리: Part 경계 찾아서 분리                                            │
│        - "Part 8" ~ "Part 9" 시작 전 → part8.md                         │
│        - "Part 9" ~ "Part 10" 시작 전 → part9.md                        │
│        - ...                                                            │
│                                                                         │
│  출력:                                                                  │
│    data/marker/parts/                                                   │
│    ├── part8.md                                                         │
│    ├── part9.md    ← 새로 생성!                                         │
│    ├── part10.md                                                        │
│    ├── part11.md                                                        │
│    └── part12.md                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

**스크립트**: `pipeline/split_marker_by_part.py`

```python
# 의사 코드
def split_by_part(full_md_path):
    content = read_file(full_md_path)

    # Part 경계 패턴
    part_pattern = r'^## Part (\d+)'

    # 각 Part 추출
    for part_num in [8, 9, 10, 11, 12]:
        start = find_part_start(content, part_num)
        end = find_part_start(content, part_num + 1)
        part_content = content[start:end]
        save_file(f'part{part_num}.md', part_content)
```

---

### Phase 2: Markdown → JSON 변환

```
┌─────────────────────────────────────────────────────────────────────────┐
│  입력: data/marker/parts/part9.md                                       │
│                                                                         │
│  처리:                                                                  │
│    1. Section 헤딩 찾기 (## 9.4 Design Loads)                           │
│    2. Subsection 헤딩 찾기 (### 9.4.2 Specified Loads)                  │
│    3. Article 헤딩 찾기 (#### 9.4.2.1 Application)                      │
│    4. Article 앞에 [ARTICLE:ID:Title] 마커 삽입                         │
│    5. JSON 구조로 조합                                                  │
│                                                                         │
│  출력: codevault/public/data/part9_marker.json                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**스크립트**: `pipeline/parse_marker_to_json.py`

```python
# 의사 코드
def parse_part(md_path, part_num):
    content = read_file(md_path)

    sections = []
    for section_match in find_sections(content):
        section = {
            'id': section_match.id,      # "9.4"
            'title': section_match.title, # "Design Loads"
            'subsections': []
        }

        for subsection in find_subsections(section_match.content):
            # Article 앞에 마커 삽입
            marked_content = insert_article_markers(subsection.content)

            section['subsections'].append({
                'id': subsection.id,
                'title': subsection.title,
                'content': marked_content
            })

        sections.append(section)

    return {'id': str(part_num), 'title': PART_TITLES[part_num], 'sections': sections}
```

---

### Phase 3: 테이블 처리

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Marker 출력의 테이블                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  | Column 1 | Column 2 | Column 3 |                                     │
│  |----------|----------|----------|                                     │
│  | Value 1  | Value 2  | Value 3  |                                     │
│                                                                         │
│  → HTML 변환:                                                           │
│                                                                         │
│  <table class="obc-table">                                              │
│    <thead><tr><th>Column 1</th>...</tr></thead>                         │
│    <tbody><tr><td>Value 1</td>...</tr></tbody>                          │
│  </table>                                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**스크립트**: `pipeline/convert_tables.py`

---

### Phase 4: 검증 & 교체

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1. 검증                                                                │
│     - Article 개수 비교 (기존 vs 새것)                                   │
│     - 테이블 개수 비교                                                  │
│     - 샘플 content 비교                                                 │
│                                                                         │
│  2. 백업                                                                │
│     codevault/public/data/part9.json                                    │
│       → codevault/public/data/_archive/part9_pymupdf.json               │
│                                                                         │
│  3. 교체                                                                │
│     codevault/public/data/part9_marker.json                             │
│       → codevault/public/data/part9.json                                │
│                                                                         │
│  4. 웹 테스트                                                           │
│     - 각 Section 로드 확인                                              │
│     - 테이블 렌더링 확인                                                │
│     - 검색 기능 확인                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 실행 계획

### 단계별 체크리스트

```
Phase 1: Marker 분리 - SKIPPED (기존 JSON 직접 변환)
[x] 기존 JSON 구조 분석
[x] Part 8, 9 형식이 Part 10,11,12와 다름 확인
    - Part 8,9: "9.1.1.1.  Application" (공백 2개, 마크다운 없음)
    - Part 10,11,12: "#### 10.1.1.1. Scope" (#### 마크다운 헤딩)

Phase 2: Part 8 변환 - COMPLETED (2026-01-20)
[x] convert_part_format.py 작성 (범용 스크립트)
[x] Part 8 변환 실행 (70 Articles, 4 Tables 변환)
[x] 원본 백업: _archive/part8_original.json
[x] 웹에서 Part 8 확인 ✓

Phase 3: Part 9 변환 - COMPLETED (2026-01-20)
[x] Part 9 변환 실행 (419 Articles, 102 Tables 변환)
[x] 원본 백업: _archive/part9_original.json
[x] 웹에서 Part 9 확인 ✓
    - Article 헤딩 정상 표시
    - 수식 및 where 블록 정상 표시
    - 테이블 정상 렌더링

Phase 4: 전체 통합 - PENDING
[ ] DB 마이그레이션 (migrate_json.py 실행)
[ ] 웹 전체 테스트
[ ] 검색 기능 테스트
```

---

## 5. 파일 구조 (마이그레이션 후)

```
upcode-clone/
├── data/
│   ├── marker/                      # Marker 원본 출력
│   │   ├── 301880_full.md          # 전체 PDF
│   │   └── parts/                  # Part별 분리
│   │       ├── part8.md
│   │       ├── part9.md
│   │       ├── part10.md
│   │       ├── part11.md
│   │       └── part12.md
│   └── obc.db                      # SQLite DB
│
├── codevault/public/data/
│   ├── part8.json                  # Marker 기반 (새)
│   ├── part9.json                  # Marker 기반 (새)
│   ├── part10.json                 # Marker 기반 (기존)
│   ├── part11.json                 # Marker 기반 (기존)
│   ├── part12.json                 # Marker 기반 (기존)
│   └── _archive/                   # 이전 버전 백업
│       └── part9_pymupdf.json
│
└── pipeline/
    ├── split_marker_by_part.py     # Phase 1
    ├── parse_marker_to_json.py     # Phase 2
    ├── convert_tables.py           # Phase 3
    └── validate_migration.py       # Phase 4
```

---

## 6. 예상 이점

### Before (혼합 방식)

```
Part 8:  PyMuPDF → Article 없음, 불완전
Part 9:  PyMuPDF + Camelot → 복잡, 테이블 문제 많음
Part 10: Marker → 깔끔
Part 11: Marker → 깔끔
Part 12: Marker → 깔끔
```

### After (통일된 방식)

```
Part 8:  Marker → 깔끔, 일관됨
Part 9:  Marker → 깔끔, 테이블 자동 변환
Part 10: Marker → 깔끔 (기존 유지)
Part 11: Marker → 깔끔 (기존 유지)
Part 12: Marker → 깔끔 (기존 유지)
```

### 구체적 이점

| 항목 | Before | After |
|------|--------|-------|
| 파싱 스크립트 | 5개+ (Part별 다름) | 1개 (통일) |
| 테이블 처리 | 수동 오버라이드 필요 | 자동 변환 |
| 수식 처리 | 이미지로 누락 | 텍스트 보존 |
| 유지보수 | 복잡 | 단순 |
| 새 Part 추가 | 새 파서 필요 | 같은 파서 사용 |

---

## 7. 리스크 및 대응

### 리스크 1: Part 9 Article 누락

```
원인: Marker가 일부 Article 헤딩을 인식 못함
대응:
  1. 기존 Part 9 Article 목록과 비교
  2. 누락된 Article 수동 추가
  3. 패턴 개선
```

### 리스크 2: 테이블 구조 손실

```
원인: 복잡한 rowspan/colspan 테이블
대응:
  1. 기존 테이블 오버라이드 유지
  2. 문제 테이블만 수동 수정
```

### 리스크 3: 웹 렌더링 깨짐

```
원인: JSON 구조 변경으로 SectionView.tsx 호환 문제
대응:
  1. Part 10, 11, 12와 동일한 구조 유지
  2. 점진적 교체 (Part 8 먼저 테스트)
```

---

## 8. 다음 단계

**바로 시작할 수 있는 작업:**

1. `301880_full.md`에서 Part 경계 확인
2. Part 9 마크다운 구조 샘플 분석
3. `split_marker_by_part.py` 작성

**질문:**
- Phase 1부터 시작할까요?
- 아니면 먼저 Part 8로 테스트해볼까요? (Part 8은 작아서 빠름)

---

*이 문서는 `docs/MIGRATION_PLAN.md`에 저장됩니다.*
