# Phase 3: 트리 빌더

> 목표: 감지된 요소들을 계층적 트리로 조립하는 로직을 이해한다.

---

## ⚠️ 먼저 읽기

**`_checklist/OBC_STRUCTURE_RULES.md`를 먼저 읽으세요!**

- **Alternative Subsection (9.5.3A)는 9.5.3의 형제**이지 자식이 아님!
- "Sentence" 아님 → **"Clause"**
- 특수 타입 처리 필요

---

## 이 단계에서 배울 것

1. 순차적으로 감지된 요소들을 트리로 조립하는 방법
2. 스택 기반 파싱의 원리
3. **특수 패턴의 parent 결정** (핵심!)
4. 형제 노드 순서(seq)를 어떻게 관리하는지

---

## 1. 트리 구축 원리

### 핵심 질문

새 요소가 감지되면:
- **"이 요소의 parent는 누구인가?"**
- **"같은 parent 아래에서 몇 번째인가?"**

### 특수 패턴의 parent 결정 (중요!)

```
┌────────────────────────────────────────────────────────────────┐
│ 일반 패턴:                                                      │
│   9.5.3.1 (article) → parent = 9.5.3 (subsection)              │
│                                                                 │
│ 특수 패턴:                                                      │
│   9.5.3A (alt_subsection) → parent = 9.5 (section!)            │
│   9.5.3A.1 (sub_article) → parent = 9.5.3A (alt_subsection)    │
│   9.5.1.1A (article_suffix) → parent = 9.5.1 (subsection)      │
└────────────────────────────────────────────────────────────────┘
```

**핵심:** 9.5.3A는 9.5.3의 **자식이 아니라 형제**!

---

## 2. 입력과 출력 예시

### 일반 패턴

```
입력 (순차적 감지):
  1. Subsection 9.5.3 감지
  2. Article 9.5.3.1 감지
  3. Clause (1) 감지
  4. Clause (2) 감지
  5. Article 9.5.3.2 감지

출력 (트리):
  9.5.3
  ├── 9.5.3.1
  │   ├── 9.5.3.1.(1)
  │   └── 9.5.3.1.(2)
  └── 9.5.3.2
```

### 특수 패턴 (Alternative Subsection)

```
입력 (순차적 감지):
  1. Subsection 9.5.3 감지
  2. Article 9.5.3.1 감지
  3. Alt Subsection 9.5.3A 감지  ← 9.5.3의 형제!
  4. Sub-Article 9.5.3A.1 감지

출력 (트리):
  9.5 (section)
  ├── 9.5.3 (subsection)
  │   └── 9.5.3.1 (article)
  ├── 9.5.3A (alt_subsection)  ← 9.5.3과 같은 레벨!
  │   └── 9.5.3A.1 (sub_article)
  └── 9.5.3B (alt_subsection)
```

---

## 3. 타입 계층 정의 (특수 타입 포함)

```python
# 기본 계층 + 특수 타입
TYPE_LEVELS = {
    'part': 0,
    'section': 1,
    'subsection': 2,
    'alt_subsection': 2,  # subsection과 같은 레벨!
    'article': 3,
    'article_suffix': 3,  # article과 같은 레벨
    'article_0a': 3,
    'sub_article': 3,     # article과 같은 레벨
    'clause': 4,          # OBC에서 "Sentence"라고 부름
    'subclause': 5,
    'subsubclause': 6,
}

def get_level(node_type: str) -> int:
    return TYPE_LEVELS.get(node_type, 99)
```

---

## 4. 스택 기반 파싱

### 컨텍스트 스택 개념

```
스택 = 현재 위치를 나타내는 노드 ID 목록

예시:
- Article 9.5.3.1 처리 중 → 스택: ['9.5', '9.5.3', '9.5.3.1']
- Clause (1) 감지 → parent는 스택 맨 위의 '9.5.3.1'
```

### 특수 패턴 처리 (핵심!)

```
현재 스택: [9, 9.5, 9.5.3, 9.5.3.1]

예시 1: Alt Subsection 9.5.3A 감지
  9.5.3A의 레벨 = 2 (alt_subsection)
  → 레벨 2 이상 pop: 9.5.3.1, 9.5.3 제거
  → 스택: [9, 9.5]
  → parent = 9.5 (section!)  ← 9.5.3이 아님!
  → 결과 스택: [9, 9.5, 9.5.3A]

예시 2: Sub-Article 9.5.3A.1 감지
  9.5.3A.1의 레벨 = 3 (sub_article)
  현재 스택: [9, 9.5, 9.5.3A]
  → parent = 9.5.3A (alt_subsection)
  → 결과 스택: [9, 9.5, 9.5.3A, 9.5.3A.1]
```

---

## 5. 전체 코드

### tree_builder.py

```python
#!/usr/bin/env python3
"""
OBC 파싱 결과를 계층적 트리로 구축
특수 패턴 (Alternative Subsection, Article Suffix 등) 처리 포함
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from patterns import extract_references

# 타입별 레벨 (특수 타입 포함)
TYPE_LEVELS = {
    'part': 0,
    'section': 1,
    'subsection': 2,
    'alt_subsection': 2,  # subsection과 같은 레벨!
    'article': 3,
    'article_suffix': 3,
    'article_0a': 3,
    'sub_article': 3,
    'clause': 4,          # OBC에서 "Sentence"라고 부름
    'subclause': 5,
    'subsubclause': 6,
}


@dataclass
class Node:
    """트리의 노드"""
    id: str
    type: str
    part: int = 9
    parent_id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    page: int = 0
    seq: int = 0
    children: List[str] = field(default_factory=list)
    refs: Dict = field(default_factory=dict)


class TreeBuilder:
    """스택 기반 트리 빌더 (특수 패턴 지원)"""

    def __init__(self, part_num: int = 9):
        self.part_num = part_num
        self.nodes: Dict[str, Node] = {}
        self.context_stack: List[str] = []
        self.seq_counters: Dict[str, int] = {}

    def _get_level(self, node_type: str) -> int:
        """노드 타입의 레벨 반환"""
        return TYPE_LEVELS.get(node_type, 99)

    def _find_parent(self, node_type: str) -> Optional[str]:
        """
        현재 컨텍스트에서 적절한 parent 찾기

        핵심: 자신보다 상위 레벨(낮은 숫자)인 노드 찾기
        """
        target_level = self._get_level(node_type)

        for node_id in reversed(self.context_stack):
            node = self.nodes.get(node_id)
            if node:
                node_level = self._get_level(node.type)
                if node_level < target_level:
                    return node_id

        return None

    def _update_stack(self, node_type: str, node_id: str):
        """
        컨텍스트 스택 업데이트

        원리: 같은 레벨 이상은 제거하고, 새 노드 추가
        """
        new_level = self._get_level(node_type)

        # 현재 레벨 이상인 것들 제거
        while self.context_stack:
            top_id = self.context_stack[-1]
            top_node = self.nodes.get(top_id)
            if top_node:
                top_level = self._get_level(top_node.type)
                if top_level >= new_level:
                    self.context_stack.pop()
                else:
                    break
            else:
                break

        self.context_stack.append(node_id)

    def _get_next_seq(self, parent_id: Optional[str]) -> int:
        """parent 아래에서 다음 순서 번호 반환"""
        key = parent_id or '__root__'
        self.seq_counters[key] = self.seq_counters.get(key, 0) + 1
        return self.seq_counters[key]

    def add_node(
        self,
        node_type: str,
        node_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        page: int = 0
    ) -> Node:
        """
        트리에 노드 추가

        Args:
            node_type: 'part', 'section', 'subsection', 'alt_subsection',
                       'article', 'article_suffix', 'sub_article',
                       'clause', 'subclause', 'subsubclause'
            node_id: 고유 ID (예: '9.5.3.1', '9.5.3A', '9.5.3A.1')
            title: 제목 (Article 이상만)
            content: 내용 (Clause 이하만)
            page: PDF 페이지 번호
        """
        # 1. parent 찾기
        parent_id = self._find_parent(node_type)

        # 2. 순서 번호 할당
        seq = self._get_next_seq(parent_id)

        # 3. 노드 생성
        node = Node(
            id=node_id,
            type=node_type,
            part=self.part_num,
            parent_id=parent_id,
            title=title,
            content=content,
            page=page,
            seq=seq
        )

        # 4. 참조 추출
        if content:
            node.refs = extract_references(content)

        # 5. 노드 저장
        self.nodes[node_id] = node

        # 6. 부모의 children에 추가
        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].children.append(node_id)

        # 7. 스택 업데이트
        self._update_stack(node_type, node_id)

        return node

    def get_node(self, node_id: str) -> Optional[Node]:
        """노드 조회"""
        return self.nodes.get(node_id)

    def get_children(self, node_id: str) -> List[Node]:
        """자식 노드들 조회"""
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.nodes[child_id] for child_id in node.children if child_id in self.nodes]

    def to_dict(self) -> Dict[str, Dict]:
        """SQLite INSERT용 딕셔너리로 변환"""
        result = {}
        for node_id, node in self.nodes.items():
            result[node_id] = {
                'id': node.id,
                'type': node.type,
                'part': node.part,
                'parent_id': node.parent_id,
                'title': node.title,
                'content': node.content,
                'page': node.page,
                'seq': node.seq,
                'refs': node.refs
            }
        return result

    def print_tree(self, node_id: Optional[str] = None, indent: int = 0):
        """트리 구조 출력 (디버깅용)"""
        if node_id is None:
            roots = [n for n in self.nodes.values() if n.parent_id is None]
            for root in roots:
                self.print_tree(root.id, indent)
            return

        node = self.nodes.get(node_id)
        if not node:
            return

        prefix = "  " * indent
        label = node.title or (node.content[:30] + "..." if node.content else "")
        print(f"{prefix}{node.id} [{node.type}] {label}")

        for child_id in node.children:
            self.print_tree(child_id, indent + 1)
```

### test_tree.py

```python
#!/usr/bin/env python3
"""
tree_builder.py 테스트 (특수 패턴 포함)
"""

from tree_builder import TreeBuilder


def test_simple_tree():
    """기본 트리 구축 테스트"""
    builder = TreeBuilder(part_num=9)

    builder.add_node('part', '9', title='Housing and Small Buildings')
    builder.add_node('section', '9.5', title='Design of Areas')
    builder.add_node('subsection', '9.5.3', title='Ceiling Heights')
    builder.add_node('article', '9.5.3.1', title='Ceiling Heights of Rooms')
    builder.add_node('clause', '9.5.3.1.(1)',
                     content='Except as provided in Clauses (2) and (3)...')
    builder.add_node('clause', '9.5.3.1.(2)',
                     content='Ceiling heights shall be not less than 1.95 m.')

    node = builder.get_node('9.5.3.1.(1)')
    assert node is not None
    assert node.parent_id == '9.5.3.1'
    assert node.seq == 1

    print("[OK] Simple tree")


def test_alt_subsection_as_sibling():
    """⚠️ 핵심 테스트: Alternative Subsection은 형제!"""
    builder = TreeBuilder()

    builder.add_node('part', '9', title='Part 9')
    builder.add_node('section', '9.5', title='Section 9.5')
    builder.add_node('subsection', '9.5.3', title='Ceiling Heights')
    builder.add_node('article', '9.5.3.1', title='Article 1')

    # Alternative Subsection - 9.5.3의 형제여야 함!
    builder.add_node('alt_subsection', '9.5.3A', title='Living Rooms')

    # 검증: 9.5.3A의 parent는 9.5 (section)이어야 함
    alt_sub = builder.get_node('9.5.3A')
    assert alt_sub.parent_id == '9.5', f"Expected '9.5', got '{alt_sub.parent_id}'"

    # 9.5의 children에 9.5.3과 9.5.3A 둘 다 있어야 함
    section = builder.get_node('9.5')
    assert '9.5.3' in section.children
    assert '9.5.3A' in section.children

    print("[OK] Alternative Subsection as sibling (CRITICAL)")


def test_sub_article():
    """Sub-Article 테스트: 9.5.3A.1"""
    builder = TreeBuilder()

    builder.add_node('part', '9', title='Part 9')
    builder.add_node('section', '9.5', title='Section 9.5')
    builder.add_node('alt_subsection', '9.5.3A', title='Living Rooms')
    builder.add_node('sub_article', '9.5.3A.1', title='Areas of Living Rooms')

    # 검증: 9.5.3A.1의 parent는 9.5.3A
    sub_art = builder.get_node('9.5.3A.1')
    assert sub_art.parent_id == '9.5.3A'

    print("[OK] Sub-Article")


def test_article_suffix():
    """Article + Suffix 테스트: 9.5.1.1A"""
    builder = TreeBuilder()

    builder.add_node('part', '9', title='Part 9')
    builder.add_node('section', '9.5', title='Section')
    builder.add_node('subsection', '9.5.1', title='General')
    builder.add_node('article', '9.5.1.1', title='Method of Measurement')
    builder.add_node('article_suffix', '9.5.1.1A', title='Floor Areas')

    # 검증: 9.5.1.1A의 parent는 9.5.1 (subsection)
    suffix = builder.get_node('9.5.1.1A')
    assert suffix.parent_id == '9.5.1'

    # 순서 확인
    art = builder.get_node('9.5.1.1')
    assert art.seq == 1
    assert suffix.seq == 2  # 바로 뒤에

    print("[OK] Article with Suffix")


def test_complete_section_95():
    """Section 9.5 전체 구조 테스트"""
    builder = TreeBuilder()

    builder.add_node('part', '9', title='Part 9')
    builder.add_node('section', '9.5', title='Design of Areas')

    # 9.5.1 General
    builder.add_node('subsection', '9.5.1', title='General')
    builder.add_node('article', '9.5.1.1', title='Method of Measurement')
    builder.add_node('article_suffix', '9.5.1.1A', title='Floor Areas')

    # 9.5.3 Ceiling Heights
    builder.add_node('subsection', '9.5.3', title='Ceiling Heights')
    builder.add_node('article', '9.5.3.1', title='Ceiling Heights of Rooms')

    # 9.5.3A Living Rooms (형제!)
    builder.add_node('alt_subsection', '9.5.3A', title='Living Rooms')
    builder.add_node('sub_article', '9.5.3A.1', title='Areas of Living Rooms')

    # 9.5.3B Dining Rooms (형제!)
    builder.add_node('alt_subsection', '9.5.3B', title='Dining Rooms')
    builder.add_node('sub_article', '9.5.3B.1', title='Area of Dining Rooms')

    # 검증
    section = builder.get_node('9.5')
    children_ids = section.children

    assert '9.5.1' in children_ids
    assert '9.5.3' in children_ids
    assert '9.5.3A' in children_ids  # 형제!
    assert '9.5.3B' in children_ids  # 형제!

    print("\n--- Section 9.5 Tree ---")
    builder.print_tree('9.5')
    print("------------------------\n")

    print("[OK] Complete Section 9.5")


def test_reference_extraction():
    """참조 추출 테스트"""
    builder = TreeBuilder()

    builder.add_node('part', '9', title='Part 9')
    builder.add_node('section', '9.5', title='Section')
    builder.add_node('subsection', '9.5.3', title='Subsection')
    builder.add_node('article', '9.5.3.1', title='Article')
    builder.add_node(
        'clause', '9.5.3.1.(1)',
        content='Refer to Table 9.5.3.1 and Sentences (2) and (3).'
    )

    node = builder.get_node('9.5.3.1.(1)')
    assert '9.5.3.1' in node.refs.get('tables', [])
    assert '2' in node.refs.get('clauses', [])
    assert '3' in node.refs.get('clauses', [])

    print("[OK] Reference extraction")


if __name__ == '__main__':
    test_simple_tree()
    test_alt_subsection_as_sibling()  # 핵심!
    test_sub_article()
    test_article_suffix()
    test_complete_section_95()
    test_reference_extraction()
    print("\n=== All tests passed! ===")
```

---

## 6. 핵심 이해 포인트

### Q: Alternative Subsection의 parent는?

```
잘못된 이해:
  9.5.3A의 parent = 9.5.3?  ← 틀림!

올바른 이해:
  9.5.3A의 parent = 9.5 (section)  ← 맞음!

이유: alt_subsection의 레벨(2) < subsection의 레벨(2)이 아니므로
      스택을 거슬러 올라가서 레벨 1인 section을 찾음
```

### Q: 9.5.3.1 다음에 9.5.3A가 오면?

```
처리 전 스택: [9, 9.5, 9.5.3, 9.5.3.1]
                           ↑ 레벨 2   ↑ 레벨 3

새 요소: 9.5.3A (레벨 2)

1. 레벨 2 이상인 것 pop: 9.5.3.1, 9.5.3 제거
2. 스택: [9, 9.5]
3. parent = 9.5 (스택 top, 레벨 1)
4. 결과 스택: [9, 9.5, 9.5.3A]
```

---

## 체크리스트

- [x] `OBC_STRUCTURE_RULES.md` 읽음
- [x] **Alt Subsection이 형제**임을 이해함 (핵심!)
- [x] TYPE_LEVELS에 특수 타입 포함됨
- [x] 스택 기반 파싱 원리 이해함
- [x] tree_builder.py 작성함
- [x] `test_alt_subsection_as_sibling` 테스트 통과함 (핵심!)
- [x] 모든 테스트 통과함 (2026-01-18)

---

## 다음 단계

Phase 3 완료 후 → [Phase 4: Part 9 전체 파싱](./phase4_parsing.md)

Phase 4에서는 실제 PDF에서 Part 9 전체를 파싱합니다.
