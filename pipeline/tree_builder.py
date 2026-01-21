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

    def _find_parent_from_id(self, node_type: str, node_id: str) -> Optional[str]:
        """
        ID에서 parent 추출

        9.1.1 → 9.1 (Section)
        9.1.1.1 → 9.1.1 (Subsection)
        9.5.3A → 9.5 (Section)
        9.5.3A.1 → 9.5.3A (Alt Subsection)
        9.5.1.1A → 9.5.1 (Subsection)
        """
        import re

        # 일반 Subsection: 9.1.1 → 9.1
        if node_type == 'subsection':
            m = re.match(r'^(\d+\.\d+)\.\d+$', node_id)
            if m:
                return m.group(1)

        # 일반 Article: 9.1.1.1 → 9.1.1
        elif node_type == 'article':
            m = re.match(r'^(\d+\.\d+\.\d+)\.\d+$', node_id)
            if m:
                return m.group(1)

        # Alt Subsection: 9.5.3A → 9.5
        elif node_type == 'alt_subsection':
            m = re.match(r'^(\d+\.\d+)\.\d+[A-Z]$', node_id)
            if m:
                return m.group(1)

        # Sub-Article: 9.5.3A.1 → 9.5.3A
        elif node_type == 'sub_article':
            m = re.match(r'^(\d+\.\d+\.\d+[A-Z])\.\d+$', node_id)
            if m:
                return m.group(1)

        # Article Suffix: 9.5.1.1A → 9.5.1
        elif node_type == 'article_suffix':
            m = re.match(r'^(\d+\.\d+\.\d+)\.\d+[A-Z]$', node_id)
            if m:
                return m.group(1)

        # 0A Article: 9.33.6.10A → 9.33.6
        elif node_type == 'article_0a':
            m = re.match(r'^(\d+\.\d+\.\d+)\.\d+[A-Z]$', node_id)
            if m:
                return m.group(1)

        return None

    def _find_parent(self, node_type: str, node_id: str = '') -> Optional[str]:
        """
        적절한 parent 찾기

        모든 타입: ID에서 직접 추출 (더 안정적)
        """
        # ID에서 parent 추출 (모든 타입)
        parent_from_id = self._find_parent_from_id(node_type, node_id)
        if parent_from_id and parent_from_id in self.nodes:
            return parent_from_id

        # fallback: 스택에서 찾기 (clause 등)
        target_level = self._get_level(node_type)

        for stack_id in reversed(self.context_stack):
            node = self.nodes.get(stack_id)
            if node:
                node_level = self._get_level(node.type)
                if node_level < target_level:
                    return stack_id

        return None

    def _update_stack(self, node_type: str, node_id: str):
        """
        컨텍스트 스택 업데이트

        원리: 같은 레벨 이상은 제거하고, 새 노드 추가
        주의: clause, subclause, subsubclause는 스택에 추가 X
        """
        # clause 레벨은 스택에 추가하지 않음 (Article이 parent로 유지되어야 함)
        if node_type in ('clause', 'subclause', 'subsubclause'):
            return

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
        # 1. parent 찾기 (특수 타입은 ID 기반)
        parent_id = self._find_parent(node_type, node_id)

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
