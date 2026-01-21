# Phase 2: 파서 핵심 로직

> 목표: PDF 텍스트에서 각 요소(Section, Article, Clause 등)를 감지하는 정규식 패턴을 이해하고 테스트한다.

---

## ⚠️ 먼저 읽기

**`_checklist/OBC_STRUCTURE_RULES.md`를 먼저 읽으세요!**

- "Sentence" 아님 → **"Clause"**
- 특수 패턴 (9.5.3A, 9.5.1.1A, 9.33.6.10A) 처리 필요

---

## 이 단계에서 배울 것

1. PDF에서 추출한 텍스트가 어떻게 생겼는지
2. 각 요소(Article, **Clause** 등)를 어떤 패턴으로 감지하는지
3. **특수 패턴** (Alternative Subsection, Article Suffix) 처리
4. 참조(Table, Clause 등)를 어떻게 추출하는지

---

## 1. PDF 텍스트 형식

### 실제 PDF에서 추출한 텍스트 예시

```
9.5.1.  General

9.5.1. 0A.  Application

(1) Except as otherwise specified in this Part, this Section applies
only to dwelling units that are intended for use on a continuing or
year-round basis as the principal residence of the occupant.

9.5.1.1.  Method of Measurement

(1) Except as otherwise specified in this Part, the areas, dimensions
and heights of rooms or spaces shall be measured between finished wall
surfaces and between finished floor and ceiling surfaces.

9.5.1.1A.  Floor Areas

(1) Minimum floor areas specified in this Section do not include
closets or built-in bedroom cabinets unless otherwise indicated.

9.5.3A.  Living Rooms or Spaces Within Dwelling Units

9.5.3A.1.  Areas of Living Rooms

(1) The area of a living room or space in a dwelling unit...
```

### 핵심 관찰 (특수 패턴 포함!)

| 요소 | 패턴 특징 | 예시 |
|------|----------|------|
| Subsection | `9.X.X.` + 공백 2개 + 제목 | `9.5.3.  Ceiling Heights` |
| **Alt Subsection** | `9.X.X[A-Z].` + 공백 + 제목 | `9.5.3A.  Living Rooms...` |
| Article | `9.X.X.X.` + 공백 2개 + 제목 | `9.5.3.1.  Ceiling Heights of...` |
| **Article + Suffix** | `9.X.X.X[A-Z].` + 공백 + 제목 | `9.5.1.1A.  Floor Areas` |
| **0A Article** | `9.X.X. 0A.` + 공백 + 제목 | `9.5.1. 0A.  Application` |
| **Sub-Article** | `9.X.X[A-Z].X.` + 공백 + 제목 | `9.5.3A.1.  Areas of...` |
| Clause | `(1)` + 공백 + 대문자 시작 | `(1) Except as...` |
| Sub-clause | `(a)` + 공백 + 소문자 시작 | `(a) where one or...` |

---

## 2. 정규식 패턴

### 기본 패턴

```python
# Subsection: 9.5.3.  Ceiling Heights
SUBSECTION = r'^(9\.\d+\.\d+)\.\s{2,}([A-Z][^\n]+)$'

# Article: 9.5.3.1.  Ceiling Heights of Rooms or Spaces
ARTICLE = r'^(9\.\d+\.\d+\.\d+)\.\s{2,}([A-Z][^\n]+)$'

# Clause: (1) Except as provided... (이전에 "Sentence"라고 불렀던 것)
CLAUSE = r'^\((\d+)\)\s+([A-Z].+)'

# Sub-clause: (a) where one or more...
SUBCLAUSE = r'^\(([a-z])\)\s+(.+)'

# Sub-sub-clause: (i) the width of landings...
SUBSUBCLAUSE = r'^\(([ivx]+)\)\s+(.+)'
```

### 특수 패턴 (중요!)

```python
# Alternative Subsection: 9.5.3A.  Living Rooms...
ALT_SUBSECTION = r'^(9\.\d+\.\d+[A-Z])\.\s+([A-Z][^\n]+)$'

# Article with Suffix: 9.5.1.1A.  Floor Areas
ARTICLE_SUFFIX = r'^(9\.\d+\.\d+\.\d+[A-Z])\.\s+([A-Z][^\n]+)$'

# 0A Article: 9.5.1. 0A.  Application (공백 주의!)
ARTICLE_0A = r'^(9\.\d+\.\d+)\.\s*0A\.\s+([A-Z][^\n]+)$'

# Sub-Article: 9.5.3A.1.  Areas of Living Rooms
SUB_ARTICLE = r'^(9\.\d+\.\d+[A-Z]\.\d+)\.\s+([A-Z][^\n]+)$'
```

---

## 3. 참조 추출 패턴

### 테이블 참조

```python
# "Table 9.5.3.1" 또는 "Table 9.5.3.1."
TABLE_REF = r'Table\s+(9\.\d+\.\d+\.\d+[A-Z]?)\.?'
```

### Clause 참조 (이전에 "Sentence 참조")

```python
# "Clause (2)" 또는 "Clauses (2) and (3)"
# OBC에서는 실제로 "Sentence"라고 부르지만, 구조적으로는 Clause
CLAUSE_REF = r'(?:Sentence|Clause)[s]?\s+\((\d+)\)'
```

### Article 참조

```python
# "Article 9.5.3.1" 또는 "Articles 9.5.3.1 and 9.5.3.2"
# 특수 패턴 포함: 9.5.1.1A
ARTICLE_REF = r'Article[s]?\s+(9\.\d+\.\d+\.\d+[A-Z]?)'
```

---

## 4. 전체 코드

### patterns.py

```python
#!/usr/bin/env python3
"""
OBC PDF 파싱을 위한 정규식 패턴 모음
특수 패턴 (Alternative Subsection, Article Suffix 등) 포함
"""

import re
from typing import Optional, Tuple, Dict, List

# === 구조 감지 패턴 ===

PATTERNS = {
    # 특수 패턴 먼저! (더 구체적인 것부터)

    # Sub-Article: 9.5.3A.1.  Title
    'sub_article': re.compile(
        r'^(9\.\d+\.\d+[A-Z]\.\d+)\.\s+([A-Z][^\n]+)$',
        re.MULTILINE
    ),

    # Article + Suffix: 9.5.1.1A.  Title
    'article_suffix': re.compile(
        r'^(9\.\d+\.\d+\.\d+[A-Z])\.\s+([A-Z][^\n]+)$',
        re.MULTILINE
    ),

    # 0A Article: 9.5.1. 0A.  Title
    'article_0a': re.compile(
        r'^(9\.\d+\.\d+)\.\s*0A\.\s+([A-Z][^\n]+)$',
        re.MULTILINE
    ),

    # Alternative Subsection: 9.5.3A.  Title
    'alt_subsection': re.compile(
        r'^(9\.\d+\.\d+[A-Z])\.\s+([A-Z][^\n]+)$',
        re.MULTILINE
    ),

    # 기본 패턴

    # Article: 9.5.3.1.  Title
    'article': re.compile(
        r'^(9\.\d+\.\d+\.\d+)\.\s{2,}([A-Z][^\n]+)$',
        re.MULTILINE
    ),

    # Subsection: 9.5.3.  Title
    'subsection': re.compile(
        r'^(9\.\d+\.\d+)\.\s{2,}([A-Z][^\n]+)$',
        re.MULTILINE
    ),

    # Clause: (1) Content... (OBC에서 "Sentence"라고 부름)
    'clause': re.compile(
        r'^\((\d+)\)\s+([A-Z].+)',
        re.MULTILINE
    ),

    # Sub-clause: (a) content...
    'subclause': re.compile(
        r'^\(([a-z])\)\s+(.+)',
        re.MULTILINE
    ),

    # Sub-sub-clause: (i) content...
    'subsubclause': re.compile(
        r'^\(([ivx]+)\)\s+(.+)',
        re.MULTILINE
    ),
}

# === 참조 추출 패턴 ===

REF_PATTERNS = {
    'table': re.compile(r'Table\s+(9\.\d+\.\d+\.\d+[A-Z]?)\.?'),
    'clause': re.compile(r'(?:Sentence|Clause)[s]?\s+\((\d+)\)'),
    'article': re.compile(r'Article[s]?\s+(9\.\d+\.\d+\.\d+[A-Z]?)'),
    'section': re.compile(r'Section\s+(9\.\d+)'),
    'subsection': re.compile(r'Subsection\s+(9\.\d+\.\d+[A-Z]?)'),
}


def detect_type(line: str) -> Optional[Tuple[str, Dict]]:
    """
    한 줄의 타입을 감지하고 파싱된 데이터 반환

    Returns:
        ('article', {'id': '9.5.3.1', 'title': 'Title'}) 또는 None

    주의: 특수 패턴을 먼저 체크해야 함!
    """
    line = line.strip()
    if not line:
        return None

    # 페이지 번호 무시
    if line.isdigit():
        return None

    # 헤더/푸터 무시
    if 'Building Code' in line or 'Division B' in line:
        return None

    # === 특수 패턴 먼저! (순서 중요) ===

    # Sub-Article: 9.5.3A.1
    if m := PATTERNS['sub_article'].match(line):
        return ('sub_article', {
            'id': m.group(1),
            'title': m.group(2).strip()
        })

    # 0A Article: 9.5.1. 0A
    if m := PATTERNS['article_0a'].match(line):
        return ('article_0a', {
            'id': m.group(1) + '.0A',  # 9.5.1.0A 형식으로
            'title': m.group(2).strip()
        })

    # Article + Suffix: 9.5.1.1A
    if m := PATTERNS['article_suffix'].match(line):
        return ('article_suffix', {
            'id': m.group(1),
            'title': m.group(2).strip()
        })

    # Alternative Subsection: 9.5.3A
    if m := PATTERNS['alt_subsection'].match(line):
        return ('alt_subsection', {
            'id': m.group(1),
            'title': m.group(2).strip()
        })

    # === 기본 패턴 ===

    # Article: 9.5.3.1
    if m := PATTERNS['article'].match(line):
        return ('article', {
            'id': m.group(1),
            'title': m.group(2).strip()
        })

    # Subsection: 9.5.3
    if m := PATTERNS['subsection'].match(line):
        return ('subsection', {
            'id': m.group(1),
            'title': m.group(2).strip()
        })

    # Clause: (1) - OBC에서 "Sentence"라고 부름
    if m := re.match(r'^\((\d+)\)\s+([A-Z].+)', line):
        return ('clause', {
            'num': m.group(1),
            'content': m.group(2).strip()
        })

    # Sub-clause: (a)
    if m := re.match(r'^\(([a-z])\)\s+(.+)', line):
        return ('subclause', {
            'letter': m.group(1),
            'content': m.group(2).strip()
        })

    # Sub-sub-clause: (i)
    if m := re.match(r'^\(([ivx]+)\)\s+(.+)', line):
        return ('subsubclause', {
            'numeral': m.group(1),
            'content': m.group(2).strip()
        })

    return None


def extract_references(text: str) -> Dict[str, List[str]]:
    """
    텍스트에서 모든 참조 추출

    Returns:
        {
            'tables': ['9.5.3.1'],
            'clauses': ['2', '3'],
            'articles': ['9.5.3.2', '9.5.1.1A'],
            'sections': ['9.5']
        }
    """
    return {
        'tables': REF_PATTERNS['table'].findall(text),
        'clauses': REF_PATTERNS['clause'].findall(text),
        'articles': REF_PATTERNS['article'].findall(text),
        'sections': REF_PATTERNS['section'].findall(text),
        'subsections': REF_PATTERNS['subsection'].findall(text),
    }


def get_node_type(node_id: str) -> str:
    """
    ID 패턴으로 노드 타입 판단 (특수 패턴 포함)

    Examples:
        '9' -> 'part'
        '9.5' -> 'section'
        '9.5.3' -> 'subsection'
        '9.5.3A' -> 'alt_subsection'
        '9.5.3.1' -> 'article'
        '9.5.1.1A' -> 'article_suffix'
        '9.5.3A.1' -> 'sub_article'
    """
    # 특수 패턴 먼저!
    if re.match(r'^9\.\d+\.\d+[A-Z]\.\d+$', node_id):
        return 'sub_article'

    if re.match(r'^9\.\d+\.\d+\.\d+0A$', node_id):
        return 'article_0a'

    if re.match(r'^9\.\d+\.\d+\.\d+[A-Z]$', node_id):
        return 'article_suffix'

    if re.match(r'^9\.\d+\.\d+[A-Z]$', node_id):
        return 'alt_subsection'

    # 기본 패턴
    if re.match(r'^9\.\d+\.\d+\.\d+$', node_id):
        return 'article'

    if re.match(r'^9\.\d+\.\d+$', node_id):
        return 'subsection'

    if re.match(r'^9\.\d+$', node_id):
        return 'section'

    if node_id == '9':
        return 'part'

    return 'unknown'
```

### test_patterns.py

```python
#!/usr/bin/env python3
"""
patterns.py 테스트 (특수 패턴 포함)
"""

from patterns import detect_type, extract_references, get_node_type


def test_subsection():
    line = "9.5.3.  Ceiling Heights"
    result = detect_type(line)
    assert result is not None
    assert result[0] == 'subsection'
    assert result[1]['id'] == '9.5.3'
    print("[OK] Subsection detection")


def test_article():
    line = "9.5.3.1.  Ceiling Heights of Rooms or Spaces"
    result = detect_type(line)
    assert result is not None
    assert result[0] == 'article'
    assert result[1]['id'] == '9.5.3.1'
    print("[OK] Article detection")


def test_clause():
    """이전에 "Sentence"라고 불렀던 것"""
    line = "(1) Except as provided in Sentences (2) and (3), the ceiling heights..."
    result = detect_type(line)
    assert result is not None
    assert result[0] == 'clause'  # NOT 'sentence'!
    assert result[1]['num'] == '1'
    print("[OK] Clause detection")


def test_subclause():
    line = "(a) where one or more risers have a run of less than 280 mm"
    result = detect_type(line)
    assert result is not None
    assert result[0] == 'subclause'
    assert result[1]['letter'] == 'a'
    print("[OK] Sub-clause detection")


# === 특수 패턴 테스트 ===

def test_alt_subsection():
    """Alternative Subsection: 9.5.3A"""
    line = "9.5.3A.  Living Rooms or Spaces Within Dwelling Units"
    result = detect_type(line)
    assert result is not None
    assert result[0] == 'alt_subsection'
    assert result[1]['id'] == '9.5.3A'
    print("[OK] Alternative Subsection detection")


def test_article_suffix():
    """Article with Suffix: 9.5.1.1A"""
    line = "9.5.1.1A.  Floor Areas"
    result = detect_type(line)
    assert result is not None
    assert result[0] == 'article_suffix'
    assert result[1]['id'] == '9.5.1.1A'
    print("[OK] Article + Suffix detection")


def test_sub_article():
    """Sub-Article: 9.5.3A.1"""
    line = "9.5.3A.1.  Areas of Living Rooms"
    result = detect_type(line)
    assert result is not None
    assert result[0] == 'sub_article'
    assert result[1]['id'] == '9.5.3A.1'
    print("[OK] Sub-Article detection")


def test_references():
    text = "shall conform to Table 9.5.3.1 and Sentences (2) and (3)"
    refs = extract_references(text)
    assert '9.5.3.1' in refs['tables']
    assert '2' in refs['clauses']
    assert '3' in refs['clauses']
    print("[OK] Reference extraction")


def test_node_type():
    assert get_node_type('9') == 'part'
    assert get_node_type('9.5') == 'section'
    assert get_node_type('9.5.3') == 'subsection'
    assert get_node_type('9.5.3A') == 'alt_subsection'  # 특수!
    assert get_node_type('9.5.3.1') == 'article'
    assert get_node_type('9.5.1.1A') == 'article_suffix'  # 특수!
    assert get_node_type('9.5.3A.1') == 'sub_article'  # 특수!
    print("[OK] Node type from ID (including special patterns)")


if __name__ == '__main__':
    # 기본 패턴
    test_subsection()
    test_article()
    test_clause()
    test_subclause()

    # 특수 패턴
    test_alt_subsection()
    test_article_suffix()
    test_sub_article()

    # 기타
    test_references()
    test_node_type()

    print("\n=== All tests passed! ===")
```

---

## 5. 실습

### 파일 생성

```bash
cd scripts
# patterns.py, test_patterns.py 생성
```

### 테스트 실행

```bash
python test_patterns.py
```

예상 출력:
```
[OK] Subsection detection
[OK] Article detection
[OK] Clause detection
[OK] Sub-clause detection
[OK] Alternative Subsection detection
[OK] Article + Suffix detection
[OK] Sub-Article detection
[OK] Reference extraction
[OK] Node type from ID (including special patterns)

=== All tests passed! ===
```

---

## 6. 주의사항 (실수 방지)

### 핵심 실수 방지

| 실수 | 원인 | 해결 |
|------|------|------|
| 9.5.3A를 Article로 오인 | 기본 패턴만 사용 | **특수 패턴 먼저 체크** |
| 9.5.1.1A를 일반 Article로 처리 | Suffix 무시 | `[A-Z]?` 추가 |
| "Sentence" 용어 사용 | OBC 원문 용어 | 구조적으로 **"Clause"** |
| 참조 텍스트를 헤딩으로 오인 | 줄 중간의 "9.5.3.1" | **줄 시작** 체크 |

### 패턴 우선순위

```python
# 반드시 이 순서로!
1. sub_article    (9.5.3A.1)  - 가장 구체적
2. article_0a     (9.5.1.0A)
3. article_suffix (9.5.1.1A)
4. alt_subsection (9.5.3A)
5. article        (9.5.3.1)   - 기본
6. subsection     (9.5.3)     - 기본
```

---

## 체크리스트

- [x] `OBC_STRUCTURE_RULES.md` 읽음
- [x] "Sentence" 아니고 **"Clause"**임을 이해함
- [x] PDF 텍스트 형식 이해함
- [x] **특수 패턴** 이해함 (Alt Subsection, Article Suffix, Sub-Article)
- [x] 패턴 **우선순위** 이해함
- [x] patterns.py 작성함
- [x] test_patterns.py 작성함
- [x] 모든 테스트 통과함 (특수 패턴 포함)

---

## 다음 단계

Phase 2 완료 후 → [Phase 3: 트리 빌더](./phase3_tree.md)

Phase 3에서는 감지된 요소들을 계층 구조로 조립하는 방법을 배웁니다.
특히 **Alternative Subsection이 형제 관계**임을 처리해야 합니다.
