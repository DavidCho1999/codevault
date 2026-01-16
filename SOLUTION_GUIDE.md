# PDF 파싱 문제 해결 가이드

> CodeVault 프로젝트 - Part 9 데이터 품질 개선

---

## 목차
1. [문제 요약](#문제-요약)
2. [테이블 파싱 해결책](#1-테이블-파싱-해결책)
3. [수식 렌더링 해결책](#2-수식-렌더링-해결책)
4. [다중 페이지 테이블 처리](#3-다중-페이지-테이블-처리)
5. [구현 로드맵](#구현-로드맵)

---

## 문제 요약

### 현재 문제점 (E2E_ERROR_REPORT.md 참조)
| 문제 | 영향 받는 섹션 | 심각도 |
|------|---------------|--------|
| 테이블 헤더 손상 | 9.6.1, 9.15.3, 9.23.4 | Critical |
| 테이블 중복 | 9.6.1, 9.15.4, 9.23.3 | Critical |
| 다른 섹션 내용 혼입 | 9.4.3, 9.15.3 | Critical |
| 수식이 텍스트로 표시 | 전체 | Medium |
| 문장 파편화 | 9.1.1, 9.3.1, 9.25.2 | High |

---

## 1. 테이블 파싱 해결책

### 라이브러리 비교

| 라이브러리 | 장점 | 단점 | 추천 용도 |
|-----------|------|------|----------|
| **pdfplumber** | 복잡한 테이블 지원, 셀 병합 처리 | 느림 (0.1-0.2s/페이지) | **Building Code (추천)** |
| **camelot** | 격자 감지 우수 | 5년간 미유지보수 | 단순 테이블 |
| **tabula-py** | 사용 쉬움 | Java 필요, 병합 셀 취약 | 간단한 테이블 |
| **pymupdf4llm** | 매우 빠름 (0.12s) | 새로움, 예제 적음 | 속도 중시 |

### 추천: pdfplumber로 교체

**설치:**
```bash
pip install pdfplumber>=0.10.3
```

**새 추출 스크립트 (extract_tables_pdfplumber.py):**

```python
"""
pdfplumber 기반 테이블 추출
- 복잡한 Building Code 테이블 지원
- 병합 셀 처리
- 다중 페이지 테이블 감지
"""

import pdfplumber
import json
import re
from pathlib import Path

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'
OUTPUT_DIR = './output'

# 테이블별 설정 (bbox, 전략 등)
TABLE_CONFIG = {
    'Table 9.3.2.1': {
        'page': 719,
        'bbox': (50, 150, 750, 700),  # (x0, y0, x1, y1)
        'strategy': 'lines',
        'header_rows': 2
    },
    'Table 9.6.1.3-A': {
        'page': 731,
        'bbox': (40, 100, 760, 750),
        'strategy': 'lines',
        'header_rows': 3
    },
    'Table 9.15.3.4': {
        'page': 820,  # 확인 필요
        'bbox': (50, 200, 750, 600),
        'strategy': 'lines',
        'header_rows': 2
    },
    # ... 다른 테이블 추가
}

def extract_table_with_pdfplumber(pdf_path, table_id, config):
    """pdfplumber로 테이블 추출"""

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[config['page'] - 1]  # 0-indexed

        # bbox로 영역 크롭
        if 'bbox' in config:
            cropped = page.crop(config['bbox'])
        else:
            cropped = page

        # 테이블 설정
        table_settings = {
            "vertical_strategy": config.get('strategy', 'lines'),
            "horizontal_strategy": config.get('strategy', 'lines'),
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 3
        }

        # 추출
        table = cropped.extract_table(table_settings)

        if table:
            # 헤더 분리
            header_rows = config.get('header_rows', 1)
            headers = table[:header_rows]
            data = table[header_rows:]

            return {
                'id': table_id,
                'headers': headers,
                'data': data,
                'page': config['page']
            }

        return None

def clean_table_data(table_data):
    """테이블 데이터 정리"""
    if not table_data:
        return table_data

    cleaned = []
    seen_rows = set()

    for row in table_data:
        # 빈 행 제거
        if all(cell is None or str(cell).strip() == '' for cell in row):
            continue

        # 중복 행 제거
        row_key = tuple(str(cell).strip() if cell else '' for cell in row)
        if row_key in seen_rows:
            continue
        seen_rows.add(row_key)

        # 셀 정리
        cleaned_row = []
        for cell in row:
            if cell is None:
                cleaned_row.append('')
            else:
                # 여러 줄 바꿈 정리
                cleaned_cell = re.sub(r'\n+', ' ', str(cell))
                cleaned_cell = re.sub(r'\s+', ' ', cleaned_cell).strip()
                cleaned_row.append(cleaned_cell)

        cleaned.append(cleaned_row)

    return cleaned

def validate_table(table_data, table_id):
    """테이블 검증"""
    issues = []

    if not table_data:
        issues.append('empty_table')
        return issues

    # 컬럼 수 일관성 확인
    col_counts = [len(row) for row in table_data]
    if len(set(col_counts)) > 1:
        issues.append(f'inconsistent_columns: {set(col_counts)}')

    # 너무 긴 셀 감지 (병합 셀 의심)
    for i, row in enumerate(table_data):
        for j, cell in enumerate(row):
            if cell and len(str(cell)) > 500:
                issues.append(f'long_cell_row{i}_col{j}: {len(str(cell))} chars')

    return issues

def extract_all_tables():
    """모든 테이블 추출"""
    results = {}

    for table_id, config in TABLE_CONFIG.items():
        print(f"Extracting {table_id}...")

        table = extract_table_with_pdfplumber(PDF_PATH, table_id, config)

        if table:
            # 데이터 정리
            table['data'] = clean_table_data(table['data'])

            # 검증
            issues = validate_table(table['data'], table_id)
            table['issues'] = issues

            if issues:
                print(f"  ⚠️ Issues: {issues}")
            else:
                print(f"  ✅ OK")

            results[table_id] = table
        else:
            print(f"  ❌ Failed to extract")

    return results

if __name__ == '__main__':
    results = extract_all_tables()

    # JSON 저장
    output_path = Path(OUTPUT_DIR) / 'tables_pdfplumber.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {output_path}")
```

---

## 2. 수식 렌더링 해결책

### 현재 문제
```
W = w × [ ∑ sjs / (storeys × 4.9)]
```
이런 수식이 그냥 텍스트로 보임

### 해결책: KaTeX 사용 (가장 빠름)

**설치:**
```bash
cd codevault
npm install katex react-katex
```

### Step 1: Python에서 수식 감지 및 변환

**parse_obc_v5.py에 추가:**

```python
import re

def detect_equations(text):
    """수식 패턴 감지"""
    patterns = [
        # 변수 = 계산식 패턴
        r'([A-Z])\s*=\s*([^.\n]{10,})',
        # 수학 기호 포함
        r'.*[∑∏×÷±√∞≤≥≠].*',
        # 분수 패턴
        r'\w+\s*/\s*\w+',
    ]

    equations = []
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            equations.append({
                'original': match.group(),
                'start': match.start(),
                'end': match.end()
            })

    return equations

def convert_to_latex(equation_text):
    """일반 텍스트를 LaTeX로 변환"""

    replacements = {
        '×': r'\\times',
        '÷': r'\\div',
        '√': r'\\sqrt',
        '±': r'\\pm',
        '∑': r'\\sum',
        '∏': r'\\prod',
        '≤': r'\\leq',
        '≥': r'\\geq',
        '≠': r'\\neq',
        '∞': r'\\infty',
    }

    latex = equation_text
    for char, latex_char in replacements.items():
        latex = latex.replace(char, latex_char)

    # 분수 변환: a / b -> \frac{a}{b}
    latex = re.sub(r'(\w+)\s*/\s*\(([^)]+)\)', r'\\frac{\1}{(\2)}', latex)
    latex = re.sub(r'(\w+)\s*/\s*(\w+)', r'\\frac{\1}{\2}', latex)

    # 아래첨자: x_1 -> x_{1}
    latex = re.sub(r'_(\w)', r'_{\1}', latex)

    # 위첨자: x^2 -> x^{2}
    latex = re.sub(r'\^(\w)', r'^{\1}', latex)

    return latex

def process_content_with_equations(content):
    """콘텐츠에서 수식을 찾아 LaTeX 마커로 변환"""

    equations = detect_equations(content)

    # 역순으로 처리 (인덱스 유지를 위해)
    for eq in sorted(equations, key=lambda x: x['start'], reverse=True):
        original = eq['original']
        latex = convert_to_latex(original)

        # 마커로 감싸기
        marked = f'$$LATEX:{latex}$$'
        content = content[:eq['start']] + marked + content[eq['end']:]

    return content
```

### Step 2: React 컴포넌트 생성

**src/components/code/EquationRenderer.tsx:**

```tsx
'use client';

import React, { useMemo } from 'react';
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';

interface EquationRendererProps {
  latex: string;
  block?: boolean;
}

export function EquationRenderer({ latex, block = true }: EquationRendererProps) {
  // 에러 처리
  const renderEquation = useMemo(() => {
    try {
      if (block) {
        return <BlockMath math={latex} />;
      }
      return <InlineMath math={latex} />;
    } catch (error) {
      console.error('LaTeX rendering error:', error);
      return <code className="text-red-500 bg-red-50 px-2 py-1 rounded">{latex}</code>;
    }
  }, [latex, block]);

  return (
    <div className="my-4 overflow-x-auto">
      {renderEquation}
    </div>
  );
}
```

### Step 3: ContentRenderer 수정

**src/components/code/ContentRenderer.tsx:**

```tsx
'use client';

import React from 'react';
import { EquationRenderer } from './EquationRenderer';

interface ContentRendererProps {
  content: string;
}

export function ContentRenderer({ content }: ContentRendererProps) {
  // $$LATEX:...$$  패턴 찾기
  const parts = useMemo(() => {
    const regex = /\$\$LATEX:([^$]*)\$\$/g;
    const result: (string | { type: 'latex'; content: string })[] = [];
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(content)) !== null) {
      // 수식 앞 텍스트
      if (match.index > lastIndex) {
        result.push(content.slice(lastIndex, match.index));
      }

      // 수식
      result.push({
        type: 'latex',
        content: match[1]
      });

      lastIndex = regex.lastIndex;
    }

    // 나머지 텍스트
    if (lastIndex < content.length) {
      result.push(content.slice(lastIndex));
    }

    return result;
  }, [content]);

  return (
    <div className="prose prose-sm max-w-none">
      {parts.map((part, index) => {
        if (typeof part === 'string') {
          return <span key={index}>{part}</span>;
        }
        return <EquationRenderer key={index} latex={part.content} />;
      })}
    </div>
  );
}
```

### 예시: 변환 결과

**Before (텍스트):**
```
W = w × [ ∑ sjs / (storeys × 4.9)]
```

**After (LaTeX 렌더링):**
$$W = w \times \left[ \sum \frac{sjs}{(storeys \times 4.9)} \right]$$

---

## 3. 다중 페이지 테이블 처리

### 감지 로직

```python
def detect_table_continuation(pdf, page_num):
    """다음 페이지로 테이블이 이어지는지 감지"""

    if page_num >= len(pdf.pages) - 1:
        return False

    current_page = pdf.pages[page_num]
    next_page = pdf.pages[page_num + 1]

    # 현재 페이지 마지막 테이블
    current_tables = current_page.find_tables()
    if not current_tables:
        return False

    # 다음 페이지 첫 테이블
    next_tables = next_page.find_tables()
    if not next_tables:
        return False

    # 컬럼 수 비교
    current_cols = len(current_tables[-1].cells[0]) if current_tables[-1].cells else 0
    next_cols = len(next_tables[0].cells[0]) if next_tables[0].cells else 0

    # 같은 컬럼 수면 연속 테이블로 판단
    return current_cols == next_cols

def extract_multipage_table(pdf, start_page, table_id):
    """다중 페이지 테이블 추출 및 병합"""

    all_rows = []
    current_page = start_page
    header = None

    while current_page < len(pdf.pages):
        page = pdf.pages[current_page]
        tables = page.find_tables()

        if not tables:
            break

        table = tables[0].extract()

        if current_page == start_page:
            # 첫 페이지: 헤더 저장
            header = table[0]
            all_rows.extend(table)
        else:
            # 이후 페이지: 헤더 중복 제거
            if table[0] == header:
                all_rows.extend(table[1:])
            else:
                all_rows.extend(table)

        # 다음 페이지 확인
        if not detect_table_continuation(pdf, current_page):
            break

        current_page += 1

    return all_rows
```

---

## 구현 로드맵

### Phase 1: 테이블 파싱 개선 (1주차)

1. **pdfplumber 설치 및 테스트**
   ```bash
   pip install pdfplumber>=0.10.3
   ```

2. **가장 문제 많은 테이블 3개 테스트**
   - Table 9.15.3.4 (완전 손상)
   - Table 9.6.1.3-A (중복)
   - Table 9.23.4.2 (단어 분리)

3. **PyMuPDF vs pdfplumber 비교**
   - 정확도
   - 속도
   - 결과 품질

4. **성공 시 전체 마이그레이션**

### Phase 2: 수식 렌더링 (2주차)

1. **KaTeX 설치**
   ```bash
   npm install katex react-katex
   ```

2. **수식 감지 로직 추가**
   - parse_obc_v5.py 생성

3. **React 컴포넌트 생성**
   - EquationRenderer.tsx
   - ContentRenderer.tsx 수정

4. **테스트**
   - 9.15.3의 W = w × ... 수식
   - 다른 수식 포함 섹션

### Phase 3: 다중 페이지 테이블 (3주차)

1. **연속 테이블 감지 로직 구현**
2. **테스트 케이스 작성**
3. **병합 로직 검증**

---

## 빠른 테스트

### pdfplumber 테스트 (5분)

```python
# test_pdfplumber.py
import pdfplumber

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'

with pdfplumber.open(PDF_PATH) as pdf:
    # Table 9.15.3.4 테스트 (가장 손상 심한 테이블)
    page = pdf.pages[819]  # 820페이지 (0-indexed)

    tables = page.find_tables()
    print(f"Found {len(tables)} tables")

    for i, table in enumerate(tables):
        data = table.extract()
        print(f"\nTable {i+1}:")
        for row in data[:5]:  # 첫 5행만
            print(row)
```

실행:
```bash
cd scripts_temp
python test_pdfplumber.py
```

---

## 참고 자료

- [pdfplumber 공식 문서](https://github.com/jsvine/pdfplumber)
- [KaTeX 공식 문서](https://katex.org/docs/api.html)
- [react-katex](https://www.npmjs.com/package/react-katex)
- [Building Code PDF 파싱 Best Practices](https://unstract.com/blog/extract-tables-from-pdf-python/)
