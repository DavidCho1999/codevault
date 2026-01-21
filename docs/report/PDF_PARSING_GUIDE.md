# PDF 파싱 종합 가이드 (OBC Part 9 프로젝트 경험 기반)

> 이 문서는 Ontario Building Code Part 9 PDF 파싱 프로젝트에서 겪은 실수, 배운 교훈, 그리고 해결방안을 종합 정리한 것입니다.
>
> 작성일: 2026-01-17

---

## 1. PDF 텍스트 추출 기본

### 사용 도구
```python
import fitz  # PyMuPDF
doc = fitz.open('document.pdf')
page = doc[page_num]
```

### 추출 방법 비교

| 방법 | 용도 | 장점 | 단점 |
|------|------|------|------|
| `page.get_text()` | 단순 텍스트 | 빠름 | 순서 뒤섞임 가능 |
| `page.get_text("blocks")` | 블록 단위 | 위치 정보 포함 | 추가 정렬 필요 |
| `page.get_text("dict")` | 상세 구조 | 폰트, 이미지 정보 | 복잡함 |
| `page.get_text("html")` | HTML 변환 | 서식 유지 | 파싱 추가 필요 |

---

## 2. 실수 기록 및 해결방안

### 실수 #1: 텍스트 순서 뒤섞임

**문제**
```python
# 잘못된 방법
text = page.get_text()  # 순서 보장 안됨
```

**증상**: 9.1.1.7이 9.1.1.1보다 위에 표시됨

**원인**: PDF 내부 텍스트 블록 순서 ≠ 시각적 순서

**해결**
```python
# 올바른 방법: 좌표로 정렬
blocks = page.get_text("blocks")
# blocks: (x0, y0, x1, y1, text, block_no, block_type)
sorted_blocks = sorted(blocks, key=lambda b: (b[1], b[0]))  # y좌표 → x좌표
text = "\n".join([b[4] for b in sorted_blocks if b[6] == 0])
```

---

### 실수 #2: 섹션 경계 분리 실패

**문제**
```python
# 잘못된 방법: 단순 페이지 연결
for p in range(start_page, end_page):
    content += doc[p].get_text()
```

**증상**: 9.2 Definitions 내용이 9.3에 섞임

**원인**: 페이지 경계 ≠ 섹션 경계

**해결**
```python
# 올바른 방법: 섹션 ID 패턴으로 경계 분리
import re

def extract_section(text, section_id, next_section_id):
    # 시작점 찾기
    start_pattern = rf'^{re.escape(section_id)}\.\s'
    start_match = re.search(start_pattern, text, re.MULTILINE)

    # 종료점 찾기 (다음 섹션 시작)
    end_pattern = rf'^{re.escape(next_section_id)}\.\s'
    end_match = re.search(end_pattern, text[start_match.end():], re.MULTILINE)

    return text[start_match.start():start_match.end() + end_match.start()]
```

---

### 실수 #3: Article 내용 누락

**문제**
```python
# 잘못된 방법: Subsection 레벨만 인식
if next_subsection_id in text:
    return text[:text.find(next_subsection_id)]
```

**증상**: 9.4.2 섹션에서 9.4.2.2, 9.4.2.3 Article 전체 누락

**원인**:
- Subsection (9.4.2) 내부에 여러 Article (9.4.2.1, 9.4.2.2, ...) 존재
- 다음 Subsection (9.4.3) 발견 시 조기 종료

**해결**
```python
# 올바른 방법: Article 레벨까지 파싱
def extract_subsection_with_articles(text, subsection_id):
    # 9.4.2 → 9.4.3까지 전체 추출
    # 내부 Article (9.4.2.1, 9.4.2.2, ...) 모두 포함

    current_major = subsection_id  # "9.4.2"
    parts = current_major.split('.')
    next_major = f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"  # "9.4.3"

    start = text.find(f"{current_major}.")
    end = text.find(f"{next_major}.")

    return text[start:end] if end > 0 else text[start:]
```

---

### 실수 #4: 수식이 이미지로 저장됨 (Critical)

**문제**
```python
text = page.get_text()  # 이미지 내 텍스트 추출 불가
```

**증상**: `xd = 5(h - 0.55Ss/γ)` 수식 완전 누락

**원인**: PDF 생성 시 수식을 **이미지로 삽입** (MathType, Symbol 폰트)

**진단 방법**
```python
# 이미지 블록 확인
blocks = page.get_text("dict")["blocks"]
for block in blocks:
    if block["type"] == 1:  # 이미지
        print(f"Image at: {block['bbox']}")
    elif block["type"] == 0:  # 텍스트
        for line in block.get("lines", []):
            y = line["bbox"][1]
            text = "".join([span["text"] for span in line["spans"]])
            print(f"Text at y={y}: {text[:50]}")

# 결과 예시:
# Text at y=371: "(5)...shall be calculated as follows:"
# Image at: (276.95, 382.5, 371.05, 422.35)  ← 수식!
# Text at y=423: "where"
```

**해결방안**

| 방법 | 난이도 | 정확도 | 설명 |
|------|--------|--------|------|
| 수동 입력 | 낮음 | 100% | 주요 수식 직접 JSON에 추가 |
| Tesseract OCR | 중간 | 70-80% | 일반 텍스트 OK, 수식은 부정확 |
| MathPix API | 중간 | 95%+ | LaTeX 변환, 유료 |
| pdf.js + 수동 | 높음 | 90%+ | 이미지 추출 후 변환 |

**당장의 해결책 (수동 입력)**
```python
# JSON에 직접 수식 추가
equations = {
    "9.4.2.2.(5)": "xd = 5(h - 0.55Ss/γ)",
    "9.4.2.1.(1)(f)": "Do = 10(Ho - 0.8Ss/γ)",
    "9.4.2.2.(1)": "S = CbSs + Sr"
}

# content에 삽입
old = "calculated as follows:\n\nwhere"
new = f"calculated as follows:\n\n{equations['9.4.2.2.(5)']}\n\nwhere"
content = content.replace(old, new)
```

---

### 실수 #5: 조항 번호 분리됨

**문제**
```
(e)
the maximum total roof area...
```

**원인**: PDF 텍스트 블록이 조항 번호와 내용을 분리

**해결**
```python
import re

def fix_clause_formatting(text):
    # (a)\n내용 → (a) 내용
    text = re.sub(r'\(([a-z])\)\s*\n+([A-Za-z])', r'(\1) \2', text)

    # (i)\n내용 → (i) 내용 (로마 숫자)
    text = re.sub(r'\(([ivx]+)\)\s*\n+([A-Za-z])', r'(\1) \2', text)

    # 9.4.2.1.\nApplication → 9.4.2.1. Application
    text = re.sub(r'(9\.\d+\.\d+\.\d+\.)\s*\n+([A-Z])', r'\1 \2', text)

    return text
```

---

## 3. 테이블 파싱 라이브러리 (향후 참고)

현재는 PyMuPDF로 테이블을 추출하고 있지만, 복잡한 테이블의 경우 다른 라이브러리가 더 나을 수 있음.

| 라이브러리 | 장점 | 단점 | 추천 용도 |
|-----------|------|------|----------|
| **pdfplumber** | 복잡한 테이블 지원, 셀 병합 처리 | 느림 (0.1-0.2s/페이지) | **Building Code (추천)** |
| **camelot** | 격자 감지 우수 | 5년간 미유지보수 | 단순 테이블 |
| **tabula-py** | 사용 쉬움 | Java 필요, 병합 셀 취약 | 간단한 테이블 |
| **pymupdf4llm** | 매우 빠름 (0.12s) | 새로움, 예제 적음 | 속도 중시 |

```bash
# pdfplumber 설치
pip install pdfplumber>=0.10.3
```

---

## 4. 검증 자동화

### Content 길이 검증
```python
def validate_sections(data):
    warnings = []
    criticals = []

    for section in data['sections']:
        content_len = len(section.get('content', ''))

        if content_len < 200:
            criticals.append({
                'id': section['id'],
                'title': section['title'],
                'length': content_len
            })
        elif content_len < 500:
            warnings.append({
                'id': section['id'],
                'title': section['title'],
                'length': content_len
            })

    return criticals, warnings

# 실행
criticals, warnings = validate_sections(data)
print(f"Critical (<200자): {len(criticals)}개")
print(f"Warning (<500자): {len(warnings)}개")
```

### 수식 이미지 감지
```python
def find_equation_images(doc, page_range):
    """이미지로 된 수식 찾기"""
    results = []

    for page_num in page_range:
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]

        text_lines = [(line["bbox"][1], "".join([s["text"] for s in line["spans"]]))
                      for block in blocks if block["type"] == 0
                      for line in block.get("lines", [])]

        for block in blocks:
            if block["type"] == 1:  # image
                bbox = block["bbox"]
                y = bbox[1]

                # 헤더 제외, 수식 크기 범위
                if y > 50 and 30 < (bbox[2]-bbox[0]) < 400:
                    # 앞뒤 텍스트로 수식 여부 판단
                    before = next((t for ty, t in sorted(text_lines) if ty < y-5), "")

                    if any(kw in before.lower() for kw in ['follows', 'formula', 'equation']):
                        results.append({
                            'page': page_num + 1,
                            'context': before[:70]
                        })

    return results
```

---

## 5. 권장 워크플로우

```
┌─────────────────────────────────────────────────────────────┐
│  1. PDF 구조 분석                                            │
│     - 페이지 범위 확인                                       │
│     - 섹션 ID 패턴 파악                                      │
│     - 이미지/수식 위치 확인                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. 텍스트 추출                                              │
│     - get_text("blocks") 사용                               │
│     - y좌표 → x좌표 정렬                                     │
│     - 섹션 ID 패턴으로 경계 분리                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. 후처리                                                   │
│     - 조항 번호 병합 (a)\n → (a)                             │
│     - Article ID 정리                                        │
│     - 불필요한 공백/줄바꿈 제거                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. 검증                                                     │
│     - Content 길이 체크 (<200자 Critical)                    │
│     - 이미지 수식 감지                                       │
│     - 원본 PDF와 비교 (샘플링)                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  5. 수동 보완                                                │
│     - 누락된 수식 직접 입력                                   │
│     - 짧은 섹션 원본 확인                                    │
│     - 특수 문자 처리                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. 핵심 교훈 요약

| 교훈 | 설명 |
|------|------|
| **텍스트 순서 믿지 말 것** | 항상 좌표로 정렬 |
| **페이지 경계 ≠ 섹션 경계** | ID 패턴으로 분리 |
| **Article 레벨까지 파싱** | Subsection만 보면 내용 누락 |
| **수식은 이미지일 수 있음** | `get_text("dict")`로 확인 |
| **검증 자동화 필수** | Content 길이, 이미지 감지 |
| **수동 검토 병행** | 수식 많은 섹션은 꼭 확인 |

---

## 7. 체크리스트

### PDF 파싱 전 확인
- [ ] 페이지 범위 확인
- [ ] 섹션 ID 패턴 파악 (예: 9.X.X.X.)
- [ ] 테이블/수식 위치 확인

### 파싱 후 검증
- [ ] 모든 섹션 content 길이 > 200자
- [ ] 이미지 수식 누락 확인
- [ ] 조항 번호 포맷팅 확인
- [ ] 샘플 섹션 원본과 비교

---

## 8. 관련 파일

- `CLAUDE.md` - 실수 기록 원본
- `CONTENT_ANALYSIS_REPORT.md` - 섹션 길이 분석 결과
- `CONTENT_FIX_REPORT.md` - 수정된 섹션 목록
- `scripts_temp/parse_obc_v4.py` - 파싱 스크립트
