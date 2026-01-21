---
description: PDF 테이블 추출 및 수정 (상태 확인, 추가, 검증, 수동 오버라이드)
argument-hint: [status | add <table_id> | check <table_id> | fix <table_id> | extract <page_num>]
model: haiku
---

# PDF 테이블 관리

명령어: **$ARGUMENTS**

---

## CRITICAL WARNINGS

> **"렌더링됨" ≠ "완료"!**
> - 테이블이 보인다고 끝 아님
> - 7개 품질 체크리스트 모두 충족 필수
> - PDF 이미지 비교 없이 PASS 금지

**반복 실수 체크 (작업 전 확인!):**
- [ ] PDF 이미지 먼저 추출했나? (`extract_table_image.py`)
- [ ] MERGE 구조 (rowspan/colspan) PDF와 비교했나?
- [ ] caption에서 "Table X.X.X." 제거했나? (헤더와 중복)
- [ ] caption에 "Forming Part of..." 넣지 않았나? (subtitle 중복)
- [ ] `<sup>` 대신 유니코드 `⁽¹⁾` 사용했나?
- [ ] inline style 사용했나? (Tailwind 금지)

---

## 필수 규칙

1. **table_id → section_id**: `9.8.7.1` → `9.8.7`
2. **품질 가이드**: `_checklist/TABLE_QUALITY_GUIDE.md`
3. **실수 패턴**: `_checklist/MISTAKES_LOG.md` (#9-#13 테이블 관련)

---

## 품질 체크리스트 (7개 필수)

| # | 항목 |
|---|------|
| 1 | caption (제목만 - ⚠️ "Forming Part of"는 **제외**) |
| 2 | Notes 분리 (`table-notes` div) |
| 3 | 유니코드 위첨자 `⁽¹⁾` (`<sup>` 금지) |
| 4 | inline style (Tailwind 금지) |
| 5 | source: "manual_override" |
| 6 | **MERGE 구조** (PDF 이미지 비교!) |
| 7 | 데이터 정확성 |

> 모두 충족해야 PASS

---

## 명령어

| 명령 | 설명 |
|------|------|
| `status` | 전체 테이블 상태 |
| `add <id>` | v9_fixed에서 추가 |
| `check <id>` | 웹 렌더링 검증 |
| `fix <id>` | 수동 오버라이드 |
| `extract <page>` | PDF 이미지 추출 |

---

## status

```bash
python scripts_temp/table_gap_analysis.py
```

- `[OK]` → 정상
- `[MISSING - auto]` → `/table add`
- `[MISSING - manual]` → `/table fix`

---

## add <table_id>

```bash
# 1. 확인
grep '"table_id": "<id>"' codevault/public/data/part9_tables_v9_fixed.json

# 2. 변환
python scripts_temp/table_smart_convert.py update <id>

# 3. 웹 확인
http://localhost:3001/code/<section_id>
```

---

## check <table_id>

### 1. 자동 검증 (토큰 0)

```bash
# section_id = table_id에서 마지막 숫자 제거 (9.8.7.1 → 9.8.7)
python scripts_temp/auto_verify.py --web <section_id>
```

**결과:**
- `[OK] PASS` + `Table` 포함 → 기본 렌더링 OK
- `[WARN] 테이블 버튼 없음` → JSON 확인 필요

### 2. JSON 확인

```bash
# 테이블 존재 + MERGE 개수
python -c "
import json
with open('codevault/public/data/part9_tables.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
html = data.get('Table <id>', {}).get('html', '')
print(f'exists: {bool(html)}')
print(f'rowspan: {html.count(\"rowspan\")}')
print(f'colspan: {html.count(\"colspan\")}')
"
```

### 3. Playwright (MERGE 확인 필요시만)

> **자동 검증 PASS + MERGE 개수 정상이면 생략!**

```
browser_navigate → http://localhost:3001/code/<section_id>
browser_snapshot → 팝업 열어서 구조 확인
```

---

## fix <table_id>

### Phase 1: 분석

```bash
# 페이지 확인
grep -A 5 '"table_id": "<id>"' codevault/public/data/part9_tables_v9_fixed.json | grep '"page"'

# PDF 이미지
python scripts_temp/extract_table_image.py <page>

# 이미지 분석
Read tool → scripts_temp/table_p<page>_t0.png
```

### Phase 2: 오버라이드

`manual_table_overrides.json`:
```json
{
  "<id>": {
    "title": "제목",
    "page": 123,
    "cols": 5, "rows": 10, "header_rows": 2,
    "data": [["Col0", "Col1", null, "Col3"]],
    "spans": {
      "rowspans": [{"row": 0, "col": 0, "span": 2}],
      "colspans": [{"row": 0, "col": 1, "span": 2}]
    }
  }
}
```

### Phase 3: 적용

```bash
python scripts_temp/table_override_convert.py update <id>
```

---

## extract <page>

```bash
python scripts_temp/extract_table_image.py <page>
# → scripts_temp/table_p<page>_t0.png
```

---

## 주요 파일

| 파일 | 용도 |
|------|------|
| `part9_tables.json` | 현재 HTML |
| `part9_tables_v9_fixed.json` | 원본 데이터 |
| `manual_table_overrides.json` | 수동 오버라이드 |

| 스크립트 | 용도 |
|----------|------|
| `table_gap_analysis.py` | 누락 분석 |
| `table_smart_convert.py` | 스마트 변환 |
| `table_override_convert.py` | 오버라이드 적용 |
| `extract_table_image.py` | PDF 이미지 |

---

## 상세 참조

- 품질 기준: `_checklist/TABLE_QUALITY_GUIDE.md`
- 실수 패턴: `_checklist/MISTAKES_LOG.md`
- 체크리스트: `_checklist/PART9_VERIFICATION_CHECKLIST.md`
