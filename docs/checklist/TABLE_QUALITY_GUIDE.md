# 테이블 품질 가이드 (Table Quality Guide)

> Golden Standard: Table 9.3.1.7 기준
>
> "렌더링됨" ≠ "완료" - 7개 항목 모두 충족 필수

---

## 필수 품질 체크리스트

| # | 항목 | 설명 |
|---|------|------|
| 1 | **caption** | ⚠️ 제목만 ("Forming Part of..."는 **제외**) |
| 2 | **Notes 분리** | `<div class="table-notes">` 사용 |
| 3 | **유니코드 위첨자** | `⁽¹⁾ ⁽²⁾` (`<sup>` 금지) |
| 4 | **inline style** | `style="text-align: center;"` (Tailwind 금지) |
| 5 | **source 필드** | `"source": "manual_override"` |
| 6 | **MERGE 구조** | PDF와 동일한 rowspan/colspan |
| 7 | **데이터 정확성** | PDF 원본과 값 일치 |

---

## MERGE 구조 검증 (가장 중요!)

### 왜 중요한가?

Camelot 자동 변환은 복잡한 병합 인식 못함 → **항상 PDF 비교 필수**

### 검증 방법

```bash
# 1. PDF 이미지 추출
python scripts_temp/extract_table_image.py <page_num>

# 2. HTML 병합 개수 확인
python -c "
import json
with open('codevault/public/data/part9_tables.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
html = data['Table <table_id>']['html']
print(f'rowspan: {html.count(\"rowspan\")}')
print(f'colspan: {html.count(\"colspan\")}')
"
```

### 확인 항목

```
[ ] PDF 이미지 추출
[ ] rowspan 필요한 셀 확인 (세로 병합)
[ ] colspan 필요한 셀 확인 (가로 병합)
[ ] HTML 개수 = PDF 개수
[ ] 빈 <th></th> 없음 (병합 누락 징후!)
```

### 흔한 실수

```
PDF: "Roof rafters..." 3행 차지 (rowspan=3)
HTML: <th>Roof rafters...</th> + <th></th> + <th></th>
→ 빈 셀 = rowspan 누락!
```

---

## 형식 규격

### caption

```html
<caption class="text-center mb-2">
  <strong>테이블 제목</strong>
</caption>
```

- ⚠️ **"Table X.X.X."** 제외 (팝업 헤더와 중복 방지)
- ⚠️ **"Forming Part of..."** 제외 (별도 표시됨 - 중복 방지)

### Notes

```html
<div class="table-notes mt-2 text-sm text-gray-600">
  <p class="font-semibold">Notes to Table X.X.X.X.:</p>
  <p>(1) 주석 내용...</p>
</div>
```

### 유니코드 참조

| 용도 | 문자 |
|------|------|
| 위첨자 | ⁽¹⁾ ⁽²⁾ ⁽³⁾ ⁽⁴⁾ ⁽⁵⁾ |
| 아래첨자 | ₁ ₂ ₃ ₄ ₅ |
| 부등호 | ≥ ≤ |

---

## 예시 비교

### ✅ Golden Standard (9.3.1.7)

```json
{
  "title": "Table 9.3.1.7",
  "page": 718,
  "html": "<table>...<caption><strong>Site-Batched...</strong></caption>...<th>Parts⁽¹⁾</th>...</table><div class=\"table-notes\">...</div>",
  "source": "manual_override"
}
```

**주의**: caption에 "Forming Part of..."는 포함하지 않음 (중복 방지)

### ❌ 미완료 (자동 변환)

```json
{
  "title": "Table 9.3.2.1",
  "html": "<table>...<th>Boards<sup>(1)</sup></th>...</table>"
  // caption 없음, Notes 없음, <sup> 사용, source 없음
}
```

---

## 수동 오버라이드 JSON 형식

```json
{
  "<table_id>": {
    "title": "테이블 제목",
    "page": 123,
    "cols": 5,
    "rows": 10,
    "header_rows": 2,
    "data": [
      ["Col0", "Col1", null, "Col3", "Col4"],
      [null, "Row1", "Val", "Val", "Val"]
    ],
    "spans": {
      "rowspans": [{"row": 0, "col": 0, "span": 2}],
      "colspans": [{"row": 0, "col": 1, "span": 2}]
    },
    "notes": "수정 이유"
  }
}
```

**규칙**:
- colspan 병합된 오른쪽 셀 → `null`
- rowspan 병합된 아래 셀 → `null`
- spans는 시작 위치만 기록

---

## 작업 절차

1. **PDF 확인** → `extract_table_image.py <page>`
2. **MERGE 파악** → rowspan/colspan 위치 확인
3. **caption 파악** → ⚠️ 제목만 ("Forming Part"는 **제외**)
4. **Notes 확인** → PDF 하단 (1), (2) 등
5. **오버라이드 등록** → `manual_table_overrides.json`
6. **변환** → `table_override_convert.py update <id>`
7. **HTML 확인** → 병합 개수 일치 확인
8. **웹 검증** → Playwright 스크린샷

---

## 관련 파일

| 파일 | 용도 |
|------|------|
| `codevault/public/data/part9_tables.json` | 현재 HTML |
| `codevault/public/data/manual_table_overrides.json` | 수동 오버라이드 |
| `scripts_temp/extract_table_image.py` | PDF 이미지 추출 |
| `scripts_temp/table_override_convert.py` | 오버라이드 변환 |
