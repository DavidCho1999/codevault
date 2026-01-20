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
    # 기본 참조 테스트
    text = "shall conform to Table 9.5.3.1 and Sentence (2)"
    refs = extract_references(text)
    assert '9.5.3.1' in refs['tables']
    assert '2' in refs['clauses']

    # 복수 참조 테스트 (각각 키워드 필요)
    text2 = "see Sentence (2) and Sentence (3)"
    refs2 = extract_references(text2)
    assert '2' in refs2['clauses']
    assert '3' in refs2['clauses']

    # Article 참조 테스트 (특수 패턴 포함)
    text3 = "refer to Article 9.5.1.1A"
    refs3 = extract_references(text3)
    assert '9.5.1.1A' in refs3['articles']

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
