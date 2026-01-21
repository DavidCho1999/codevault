# Add New Part to OBC Database

새로운 Part(예: Part 7, 8, 10, 12)를 OBC 데이터베이스에 추가하는 워크플로우

## ⚠️ Division 규칙

**Division B만 파싱** (Division A 무시)

| Division | Parts | 파싱 여부 |
|----------|-------|----------|
| Division A | 1-3 | ❌ 무시 (Compliance, Objectives) |
| Division B | 3-12 | ✅ 파싱 (기술 요구사항) |
| Division C | - | ❌ 무시 (Administrative) |

PDF에서 "Division B - Part X" 섹션만 추출할 것!

## 사용법
```
/add-part <part_number>
```

예시:
- `/add-part 8`
- `/add-part 12`

## Marker 출력 위치
**이미 파싱 완료됨**: `data\marker`
- `301880_full.md` - Part 8, 9 전체
- `301880_full_normalized.md` - 정규화된 버전
- `chunk_01` ~ `chunk_13` - 청크별 출력
- `part910_tables/` - 테이블 이미지

## Instructions

### Step 1: 현재 상태 확인

1. 기존 파싱된 데이터 확인
```bash
ls -la codevault/public/data/part*.json
```

2. DB에 이미 있는 Part 확인
```bash
python -c "
import sqlite3
conn = sqlite3.connect('obc.db')
cursor = conn.cursor()
cursor.execute('SELECT DISTINCT SUBSTR(id, 1, INSTR(id, \".\")-1) as part FROM nodes')
parts = [r[0] for r in cursor.fetchall()]
print('Existing parts in DB:', sorted(set(parts)))
"
```

3. Marker 출력 확인
```bash
ls -la output_marker/
```

### Step 2: Marker 출력을 JSON으로 변환

Marker 출력(MD)을 JSON으로 변환:
```bash
python scripts_temp/convert/convert_part$ARGUMENTS_to_json.py output_marker/part$ARGUMENTS.md
```

또는 전체 파일에서 추출:
```bash
python scripts_temp/convert/convert_part$ARGUMENTS_to_json.py output_marker/301880_full_normalized.md
```

#### 변환 스크립트 필수 처리 항목

| Marker 출력 | 변환 후 | 설명 |
|------------|--------|------|
| `### Table 8.x.x.x.-A` | `Table 8.x.x.x.-A` | 마크다운 헤딩 제거 |
| `#### 8.x.x.x. Title` | `8.x.x.x.  Title` | Article 헤딩 plain text |
| `![](_page_xxx.jpeg)` | (제거, 줄바꿈 유지) | 이미지 태그 |

**주의: 이미지 태그 제거 시 줄바꿈 삭제하면 안 됨!**
```python
# 잘못된 예 - 줄바꿈까지 삭제하여 다음 섹션이 이전 줄에 연결됨
md_content = re.sub(r'!\[\]\([^)]+\)\n*', '', md_content)

# 올바른 예 - 줄바꿈 유지
md_content = re.sub(r'!\[\]\([^)]+\)', '', md_content)
```

**변환 스크립트 템플릿:** `scripts_temp/convert/convert_part12_to_json.py` 참고

### Step 3: 콘텐츠 정규화 ⚠️ 중요

Marker 출력의 raw markdown을 렌더링 가능한 형식으로 변환:

```bash
python scripts_temp/normalize_part$ARGUMENTS.py
```

**정규화 대상:**
| Before (raw markdown) | After (normalized) | 설명 |
|----------------------|-------------------|------|
| `**12.x.x.x. Title**` | `[ARTICLE:12.x.x.x:Title]` | Article 헤더 |
| `### Table 8.x.x.x.-A` | `Table 8.x.x.x.-A` | 테이블 헤딩 |
| `#### **Notes to Table...**` | `Notes to Table...` | 테이블 노트 |
| `**(1)**` | `(1)` | Bold clause |
| `*term*` (이탤릭) | `term` | 이탤릭 제거 |
| `- (a)` (리스트 마커) | `(a)` | 리스트 마커 제거 |
| `- (1)` (리스트 마커) | `(1)` | 리스트 마커 제거 |

**마크다운 테이블 처리:** ⚠️ 중요

마크다운 테이블을 **인라인 HTML**로 변환 (Part 10/11 방식):
```python
# convert_part10_to_plaintext.py의 convert_markdown_table_to_html() 사용
| col1 | col2 |  →  <table class="obc-table"><thead>...</table>
```

복잡한 테이블 (rowspan/colspan)은 수동으로 HTML 작성 필요.

**정규화 스크립트 템플릿:** `scripts_temp/convert/convert_part10_to_plaintext.py`

정규화 스크립트가 없으면 생성:
```python
# scripts_temp/normalize_part{N}.py
import json
import re

def normalize_content(content: str) -> str:
    if not content:
        return content
    result = content
    # 1. 마크다운 헤딩 제거: ### Table → Table
    result = re.sub(r'^#{1,4}\s+', '', result, flags=re.MULTILINE)
    # 2. Article 헤더: **N.x.x.x. Title** → [ARTICLE:N.x.x.x:Title]
    result = re.sub(r'\*\*({N}\.\d+\.\d+\.\d+)\.\s*([^*]+)\*\*', r'[ARTICLE:\1:\2]', result)
    # 3. Bold clause: **(1)** → (1)
    result = re.sub(r'\*\*\((\d+)\)\*\*', r'(\1)', result)
    # 4. 이탤릭: *term* → term
    result = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'\1', result)
    # 5. 리스트 마커: - (a) → (a), - (1) → (1)
    result = re.sub(r'^- \(([a-z])\)', r'(\1)', result, flags=re.MULTILINE)
    result = re.sub(r'^- \((\d+)\)', r'(\1)', result, flags=re.MULTILINE)
    return result
```

### Step 4: 검증 (Phase 2 스크립트)

파싱 결과 검증:
```bash
python scripts/validate_part.py codevault/public/data/part$ARGUMENTS.json
```

**통과 기준:**
- ❌ Errors: 0개
- ⚠️ Warnings: Empty content 외에 중요한 것 없음

에러가 있으면 수정 후 다시 검증.

### Step 5: DB 임포트

검증 통과 후 DB에 임포트:
```bash
python scripts_temp/import_part$ARGUMENTS_to_db.py
```

임포트 스크립트가 없으면 `scripts_temp/import_part12_to_db.py` 복사해서 수정.

### Step 5.5: 테이블 HTML 변환 ⚠️ 필수

DB 임포트 후, 마크다운 테이블을 인라인 HTML로 변환:
```bash
python scripts_temp/convert_tables_to_html.py $ARGUMENTS
```

변환 결과 확인:
```bash
python -c "
import sqlite3
conn = sqlite3.connect('obc.db')
cursor = conn.cursor()
cursor.execute('SELECT id FROM nodes WHERE id LIKE \"$ARGUMENTS.%\" AND content LIKE \"%<table class=\\\"obc-table\\\">%\"')
print('HTML 테이블 있는 노드:', [r[0] for r in cursor.fetchall()])
"
```

### Step 6: 서버 재시작 및 렌더링 확인

```bash
# 서버 재시작 (DB 캐시 클리어)
cd codevault && npm run dev
```

브라우저에서 확인:
1. `http://localhost:3001/code/$ARGUMENTS.1` 접속

2. **경고 배너 없어야 함:**
   - ❌ "RAW_MARKDOWN_HEADING: 마크다운 헤딩(###)이 렌더링 안됨"
   - ❌ "RAW_BOLD: **볼드** 마크다운이 렌더링 안됨"
   - ❌ "RAW_ITALIC: *이탤릭* 마크다운이 렌더링 안됨"

3. **렌더링 확인:**
   - ✅ Article 헤딩이 bold로 표시됨 (예: **8.1.1.1. Scope**)
   - ✅ 테이블이 정상 렌더링됨 (HTML 테이블로 표시)
   - ✅ 중복 헤딩 없음 (Subsection title이 2번 표시 안됨)
   - ✅ `[SUBSECTION:...]`, `[ARTICLE:...]` 마커 없음

4. **Playwright 자동 검증 (권장):**
```
mcp__playwright__browser_navigate url=http://localhost:3001/code/$ARGUMENTS.1
mcp__playwright__browser_snapshot
```
스냅샷에서 `RAW_`, `###`, `**`, `[SUBSECTION:` 등 확인

5. **curl 검증 시 주의:**
```bash
# ❌ 잘못된 방법 - <script> 태그 내 React hydration 데이터 포함
curl http://localhost:3001/code/$ARGUMENTS.1 | grep "SUBSECTION"

# ✅ 올바른 방법 - <script> 태그 제외
curl http://localhost:3001/code/$ARGUMENTS.1 | grep -v '<script' | grep "SUBSECTION"
```
React Server Components는 hydration 데이터를 `<script>` 태그에 포함하므로,
실제 렌더링된 HTML만 확인하려면 `<script>` 제외 필수

### Step 7: 최종 검증

DB에서 다시 검증:
```bash
python scripts/validate_part.py obc.db --db --part $ARGUMENTS
```

## 체크리스트

```markdown
## Part $ARGUMENTS 추가 체크리스트

### Parsing
- [ ] PDF 페이지 범위 확인
- [ ] Marker로 파싱 완료
- [ ] JSON 변환 완료

### Normalization ⚠️ 중요
- [ ] 마크다운 헤딩 제거 (`###`, `####` → plain text)
- [ ] `**Article.Title**` → `[ARTICLE:...]` 또는 plain text 변환
- [ ] `**(1)**` → `(1)` 변환 확인
- [ ] `*italic*` 제거 확인
- [ ] `- (a)` 리스트 마커 제거 확인
- [ ] **테이블 Bold 제거**: `**Table 8.x.x.x**` → `Table 8.x.x.x`
- [ ] **Notes Bold 제거**: `**Notes to Table...**` → `Notes to Table...`

### Tables ⚠️ 중요
- [ ] 마크다운 테이블 → 인라인 HTML 변환 (`convert_markdown_table_to_html()`)
- [ ] 복잡한 테이블 (rowspan/colspan) 수동 HTML 작성
- [ ] 테이블 헤딩과 Notes가 렌더링되는지 확인

### Validation
- [ ] `validate_part.py` 실행
- [ ] Errors 0개 확인
- [ ] 중요 Warnings 해결
- [ ] `<sup>` 태그 Warning 확인 (각주 표시, 무시 가능)

### Import & Table Conversion
- [ ] DB 임포트 완료
- [ ] **테이블 HTML 변환** (`convert_tables_to_html.py $ARGUMENTS`)
- [ ] Sidebar에 Part 추가 (Sidebar.tsx 수정)
- [ ] 서버 재시작

### Manual Review (Playwright 권장)
- [ ] 첫 섹션 ($ARGUMENTS.1) 확인
- [ ] 테이블 많은 섹션 확인
- [ ] 경고 배너 없음 확인 (RAW_MARKDOWN_*, RAW_BOLD, etc.)
- [ ] Article 헤딩이 bold로 표시됨
- [ ] 테이블 정상 렌더링 (HTML 테이블로 표시)
- [ ] `[SUBSECTION:...]`, `[ARTICLE:...]` 마커 없음
- [ ] 중복 헤딩 없음
- [ ] **curl 검증 시**: `grep -v '<script'` 사용하여 hydration 데이터 제외

### Documentation
- [ ] 발견한 이슈 CLAUDE.md에 기록
- [ ] 새 패턴 발견 시 validate_part.py 업데이트
```

## 문제 발생 시

### 정규화 누락 (RAW_MARKDOWN_CONTENT) ⚠️ 흔한 실수
- 증상: 웹에서 `**bold**`, `*italic*`, `- list` 마커가 그대로 보임
- 원인: Step 3 정규화 단계 건너뜀
- 해결: `scripts_temp/normalize_part{N}.py` 실행 후 DB 재임포트
- 예방: Part 9/11과 새 Part의 content 형식 비교 필수

### 마크다운 헤딩 잔류 (RAW_MARKDOWN_HEADING)
- 증상: `### Table 8.2.1.3.-A`가 그대로 표시됨
- 원인: Marker 출력에 `###`, `####` 등이 남아있음
- 해결: 변환/정규화 스크립트에서 `^#{1,4}\s+` 패턴 제거
- 예방: 변환 스크립트에 마크다운 헤딩 제거 로직 포함

### 마크다운 테이블 미렌더링
- 증상: `| col1 | col2 |` 형태가 텍스트로 표시됨
- 원인: Marker 출력의 마크다운 테이블이 변환 안 됨
- 해결:
  1. 변환 스크립트에서 마크다운 테이블 → HTML 변환
  2. 또는 `part{N}_tables.json`에 테이블 데이터 추가
- 예방: Part 9 테이블 형식 참고 (flat text 또는 HTML)

### [SUBSECTION:...] 마커 표시 ✅ 해결됨
- 증상: `[SUBSECTION:8.1.2:Application]`이 텍스트로 표시됨
- 원인 1: page.tsx가 subsection 타입에도 `[ARTICLE:]` 마커 추가
- 원인 2: SectionView.tsx가 마커에서 content 수집을 멈추지 않음
- 해결: 2026-01-20 코드 수정 완료
  - `page.tsx:75-88`: subsection 타입 체크 추가
  - `SectionView.tsx:609-612, 860`: 마커 체크 조건 추가
- 참고: curl로 확인 시 `<script>` 태그 제외 필수 (위 Step 6 참조)

### 이미지 태그로 인한 섹션 누락
- 증상: 특정 Subsection (예: 8.7.4)이 JSON/DB에서 누락됨
- 원인: 이미지 태그 제거 시 줄바꿈까지 삭제하여 다음 헤딩이 이전 줄에 연결
- 해결: `!\[\]\([^)]+\)\n*` → `!\[\]\([^)]+\)` (줄바꿈 유지)
- 예방: 변환 후 모든 Subsection이 있는지 확인

### 테이블 HTML 미변환
- 증상: `| col1 | col2 |` 형태가 텍스트로 표시됨
- 원인: 마크다운 테이블이 HTML로 변환 안 됨
- 해결: `convert_part10_to_plaintext.py`의 `convert_markdown_table_to_html()` 사용
- 예방: Step 3에서 테이블 변환 포함 확인

### Flat Table (FLAT_TABLE)
- 원인: PDF 페이지 분리로 테이블 구조 손실
- 해결: 수동으로 HTML `<table>` 변환 필요

### 테이블 헤딩 불일치 (TABLE_MISMATCH)
- 원인: 테이블 ID가 content에서 참조되지만 실제 HTML 없음
- 해결: 해당 테이블을 인라인 HTML로 추가

### 테이블 Bold 잔류 (Table 헤딩)
- 증상: `**Table 8.x.x.x**`가 그대로 표시됨
- 원인: normalize 스크립트에서 테이블 헤딩 처리 누락
- 해결:
  ```python
  # 테이블 제목 bold 제거
  result = re.sub(r'\*\*Table\s+(\d+\.\d+\.\d+\.\d+[^*]*)\*\*', r'Table \1', result)
  # Notes bold 제거
  result = re.sub(r'\*\*Notes to Table[^*]+\*\*', lambda m: m.group(0).replace('**', ''), result)
  ```

### Sidebar에 Part 없음
- 증상: 사이드바에 새 Part가 표시 안 됨
- 원인: Sidebar.tsx에 Part 추가 안 함
- 해결: `codevault/src/components/layout/Sidebar.tsx`에 Part 추가

## 관련 파일

### 파싱 & 변환
- `scripts/validate_part.py` - 파싱 검증 스크립트
- `scripts_temp/convert/convert_part*_to_json.py` - Marker → JSON 변환
- `scripts_temp/normalize_part*.py` - 콘텐츠 정규화 (bold, italic 제거)
- `scripts_temp/import_part*_to_db.py` - DB 임포트
- `scripts_temp/convert_tables_to_html.py` - **마크다운 테이블 → HTML 변환**

### 테이블 데이터
- 모든 Part: content에 인라인 HTML로 포함 (`<table class="obc-table">`)
- 참고: Part 9는 레거시로 `part9_tables.json` 사용 (새 Part에서는 사용 안 함)

### 렌더링
- `codevault/src/app/code/[...section]/page.tsx` - 마커 생성 (subsection 타입 체크)
- `codevault/src/components/code/SectionView.tsx` - 렌더링 (마커 처리)
- `codevault/src/components/layout/Sidebar.tsx` - 사이드바 (Part 추가 필요)

### 문서
- `CLAUDE.md` - 프로젝트 규칙 및 실수 기록
- `_checklist/OBC_STRUCTURE_RULES.md` - OBC 계층 구조 규칙

---

## 테이블 렌더링 규칙 (절대 변경 금지!)

### 테이블 제목 형식 - 반드시 3줄!

**웹에서 렌더링되는 형태:**
```
Table 8.2.1.3.-A                    ← Line 1: 테이블 번호 (볼드, 검정)
Residential Occupancy               ← Line 2: 캡션/제목 (볼드, 검정)
Forming Part of Sentence 8.2.1.3.(1) ← Line 3: Forming Part (작은 글씨, 회색)
```

**데이터 형식 (JSON/Markdown):** 한 줄로 저장
```markdown
#### Table 8.2.1.3.-A Residential Occupancy Forming Part of Sentence 8.2.1.3.(1)
```

**렌더링 코드 위치:** `SectionView.tsx:461-468`
```typescript
// 1. 헤더 추가 - 3줄 형식 (Table번호 / Caption / Forming Part)
tableElements.push(
  <div key="header" className="text-center mb-4">
    <p className="text-sm font-bold text-black dark:text-gray-200">Table {tableId}</p>
    {caption && <p className="text-sm font-bold text-black dark:text-gray-200">{caption}</p>}
    {formingPart && <p className="text-xs text-gray-600 dark:text-gray-400">{formingPart}</p>}
  </div>
);
```

⚠️ **절대 1줄로 합치지 말 것!** 사용자가 3줄 형식을 명시적으로 요청함.

### 테이블 Border 스타일

**HTML 테이블 클래스:**
```html
<table class="obc-table">
```

**CSS 정의:** `globals.css`
```css
.obc-table {
  border-collapse: collapse;
  width: 100%;
}
.obc-table th, .obc-table td {
  border: 1px solid #d1d5db;
  padding: 8px 12px;
  text-align: left;
}
.obc-table th {
  background-color: #f9fafb;
  font-weight: 600;
}
```

### Notes to Table 형식

**HTML 형식:**
```html
<h5 class="table-notes-title">Notes to Table 8.2.1.3.-A:</h5>

- (1) Note text here...
- (2) Another note...
```

**렌더링 규칙:**
- Notes 헤더: `<h5 class="table-notes-title">` 사용
- Notes 항목: `- (1)`, `- (2)` 형식 (대시 필수!)
- Notes 안에 테이블이 있을 수도 있음 (그대로 보존)

### 테이블 컨테이너 스타일

테이블은 회색 박스 안에 표시됨:
```typescript
<div key={`table-${i}`} className="obc-table-container bg-gray-50 dark:bg-gray-800 p-4 rounded-lg my-4 border border-gray-200 dark:border-gray-700">
  {/* 3줄 헤더 */}
  {/* <table> */}
  {/* Notes */}
</div>
```

---

## Quick Reference

새 Part 추가 시 핵심만:
1. **테이블 데이터**: `#### Table X.X.X.X Caption Forming Part...` (한 줄)
2. **테이블 렌더링**: 자동으로 3줄 분리 (절대 1줄로 합치지 말 것!)
3. **테이블 클래스**: `<table class="obc-table">`
4. **Notes 형식**: `<h5 class="table-notes-title">` + `- (1)` 형식

**⚠️ 과거 실수 반복 방지:** CLAUDE.md "실수 기록" 섹션 참고
- 수식 + where 분리
- Clause 줄바꿈
- rowspan/colspan 검증
- 정규식 패턴 주의

---

## 수식 렌더링 규칙 (Global - 모든 Part 적용)

### 수식 + where 블록 통합 렌더링

**데이터 형식 (JSON/Markdown):**
```markdown
$$A = QT/850$$

where,

- A = the area of contact in square metres...
- Q = the total daily design *sanitary sewage* flow in litres, and
- T = the lesser of 50 and the *percolation time*...

(See Note A-8.7.7.1.(5))
```

**웹 렌더링 형태:**
```
┌──────────────────────────────────────────┐
│ ┌────────────────────────────────────┐  │
│ │     A = QT/850                     │  │ ← 수식 (흰 배경)
│ └────────────────────────────────────┘  │
│                                          │
│   where                                  │ ← where 섹션
│     A = the area of contact...          │
│     Q = the total daily design...       │
│     T = the lesser of 50...             │
│   ───────────────────────────────────   │
│   (See Note A-8.7.7.1.(5))              │ ← 이탤릭, 작은 글씨
└──────────────────────────────────────────┘
  ↑ 보라색 왼쪽 테두리, 그라데이션 배경
```

**렌더링 코드 위치:** `SectionView.tsx:750-835`
- LaTeX 수식 (`$$...$$`) 또는 일반 수식 (`A = ...`) 인식
- 다음 줄에 `where` 또는 `where,` 있으면 하나의 박스로 묶음
- `- A = ...` 형태의 변수 정의 인식 (대시로 시작)
- `(See Note A-X.X.X.X.(N))` 패턴 블록 끝에 표시

**CSS 클래스:** `globals.css`
- `.obc-formula-block` - 전체 컨테이너
- `.obc-equation` - 수식 영역
- `.obc-where-section` - where 블록

⚠️ **데이터 변환 시 주의:**
- `where,` (쉼표 포함) 형태도 인식됨
- 변수 정의는 `- A = ...` 또는 `A = ...` 둘 다 OK
- `(See Note...)` 패턴은 where 블록 안에서 인식
