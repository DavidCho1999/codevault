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
    """핵심 테스트: Alternative Subsection은 형제!"""
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
        content='Refer to Table 9.5.3.1 and Sentence (2) and Clause (3).'
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
