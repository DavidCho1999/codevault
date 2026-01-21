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

    # Article: 9.5.3.1.  Title (공백 1개 이상)
    'article': re.compile(
        r'^(9\.\d+\.\d+\.\d+)\.\s+([A-Z][^\n]+)$',
        re.MULTILINE
    ),

    # Subsection: 9.5.3.  Title (공백 1개 이상)
    'subsection': re.compile(
        r'^(9\.\d+\.\d+)\.\s+([A-Z][^\n]+)$',
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
